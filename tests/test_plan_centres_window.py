"""The stiffness centre and the mass centre in the position plan's tab (calc/tools/plan_canvas_outline.py, plan_centres_card.py, plan_tab*.py, plan_properties.py; issue #54, spec docs/requirements/completed/2026-10-13-plan-positions-centre-rigidite-centre-masse.md, REQ-009, REQ-011, UI-001 to UI-004, ARCH-007, ARCH-009, ARCH-011).

The engineer, 12.10.2026: «Ajouter un outil pour dessiner le contour du bâtiment (un polygone) sur le plan» · «Dessiner S, M et le contour dans la fenêtre ; une case à cocher sur le plan, enregistrée avec lui, décide s'ils apparaissent aussi sur le plan imprimé» · «Donner à chaque mur dessiné son mode de construction».

What is held, off-screen: the tool draws an outline as an area is drawn, and a second one takes the place of the first in one step; the outline is taken by its edge and never by its inside, reshaped by a corner, moved, deleted, and not copied; the window draws S and M whatever the plan prints, and they follow a wall moved; the card says what each centre stands on or why it is not there, in the three languages and by the very sentence the warnings say; a bracing wall and its tool have their construction mode, with no default; a section has none of it, and neither has the fire-protection plan.

⚠️ Skipped where PySide6 is not installed; the calculation and the contract are tests/test_plan_centres.py's.
"""

TIER = "fast"  # tests/run_tests.py --fast

import contextlib
import copy
import sys
import tempfile
from pathlib import Path

import conftest
from conftest import ROOT, Skip

import project
from domains import plan as model
from domains import plan_centres
from domains import plan_svg

_STATE = {}
OUTLINE = [[100, 100], [700, 100], [700, 500], [100, 500]]


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


def _source(mode="timber_frame"):
    """A floor plan of four bracing walls on a 600 by 400 building: S at (550, 300) in timber frame, the walls' lengths being 50 and 150 across and 100 each along."""
    source = model.new_source("P90", floor="1")
    source["sheet"] = {"width": 800, "height": 600}
    walls = [("W101", (100, 275), (100, 325)), ("W102", (700, 225), (700, 375)), ("H101", (350, 100), (450, 100)), ("H102", (350, 500), (450, 500))]
    for label, a, b in walls:
        element = {"type": label[0], "label": label, "points": [list(a), list(b)]}
        if mode:
            element["construction"] = mode
        source["elements"].append(element)
    return source


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


def _click(canvas, point):
    """A left click exactly at `point`, past the snapping: the tests say where, not what is near."""
    canvas._forced = tuple(point)
    try:
        canvas._left_click(tuple(point), False)
    finally:
        canvas._forced = None


def _draw_outline(canvas, points):
    import plan_canvas_outline
    canvas.set_tool(plan_canvas_outline.TOOL)
    for p in points:
        _click(canvas, p)
    _click(canvas, points[0])   # a click on the first corner closes it


# --- the canvas: the tool, and the outline taken, reshaped, moved, deleted --------------------------------------

def test_the_tool_draws_one_outline_as_an_area_is_drawn_and_a_second_takes_its_place():
    import plan_canvas_outline
    canvas, history = _canvas(_source())
    done = []
    canvas.tool_done.connect(lambda: done.append(True))
    canvas.set_tool(plan_canvas_outline.TOOL)
    assert canvas.tool_kind() == "poly", "drawn as every area: the same clicks, the same snapping, the same Shift"
    for p in OUTLINE[:2]:
        _click(canvas, p)
    assert canvas.drawing == [tuple(p) for p in OUTLINE[:2]] and "outlines" not in canvas.source, "nothing is written while it is drawn"
    for p in OUTLINE[2:]:
        _click(canvas, p)
    _click(canvas, OUTLINE[0])
    assert canvas.source["outlines"] == [{"points": OUTLINE}] and canvas.selection == ("outline", 0) and len(history) == 1
    assert done == [True] and canvas.drawing == [], "the tool is given back: a plan has one outline"
    assert canvas.source["elements"] == _source()["elements"], "the outline is no element"
    # Enter closes it as well, Backspace takes the last corner back, and a second outline takes the place of the first -- one step
    canvas.set_tool(plan_canvas_outline.TOOL)
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest
    for p in ([200, 200], [600, 200], [600, 400], [300, 450]):
        _click(canvas, p)
    QTest.keyClick(canvas, Qt.Key.Key_Backspace)
    _click(canvas, [200, 400])
    QTest.keyClick(canvas, Qt.Key.Key_Return)
    assert canvas.source["outlines"] == [{"points": [[200, 200], [600, 200], [600, 400], [200, 400]]}] and len(history) == 2
    assert history[-1]["outlines"] == [{"points": OUTLINE}], "«Annuler» brings the first one back"
    # two corners are no area: nothing is made
    canvas.set_tool(plan_canvas_outline.TOOL)
    _click(canvas, [10, 10])
    _click(canvas, [50, 10])
    QTest.keyClick(canvas, Qt.Key.Key_Return)
    assert len(history) == 2 and len(canvas.source["outlines"][0]["points"]) == 4
    model.check_source({**canvas.source, "schema_version": model.version_of(canvas.source)}, "P90.json")


def test_the_outline_is_taken_by_its_edge_and_never_by_its_inside():
    canvas, history = _canvas(dict(_source(), outlines=[{"points": copy.deepcopy(OUTLINE)}]))
    canvas.set_tool("select")
    canvas.press_select((400, 300))   # the middle of the building: nothing stands there
    assert canvas.selection is None, "a click inside the outline takes nothing"
    canvas.drag = None
    canvas.press_select((250, 500))   # on its lower edge, clear of the wall H102
    assert canvas.selection == ("outline", 0) and canvas.drag["kind"] == "outline"
    canvas.drag = None
    canvas.press_select((400, 500))   # on that edge where the wall H102 runs along it: the wall
    assert canvas.selection == ("element", 3), "an element drawn along the outline is taken before it"
    canvas.drag = None
    assert plan_centres.hit_outline(canvas.source, (400, 300), 5) is None and plan_centres.hit_outline(canvas.source, (100, 300), 5) == 0
    assert plan_centres.hit_outline(canvas.source, (400, 99), 5) == 0 and plan_centres.hit_outline({}, (0, 0), 5) is None
    # selected, its corners are joined and each carries a handle
    canvas.select(("outline", 0))
    assert len(canvas.handles) == 4 and not canvas.select_item.path().isEmpty()


def test_a_corner_is_dragged_the_whole_is_moved_and_it_is_deleted_but_not_copied():
    import plan_canvas_edit
    import plan_canvas_outline
    canvas, history = _canvas(dict(_source(), outlines=[{"points": copy.deepcopy(OUTLINE)}]))
    canvas.snap_axes = canvas.snap_elements = False
    canvas.select(("outline", 0))
    before = plan_centres.state(canvas.source)["mass"]["point"]
    assert plan_canvas_outline.press_vertex(canvas, (700, 500), canvas.tolerance()) and canvas.drag["vertex"] == 2
    drag = canvas.drag
    drag["moved"] = True
    canvas.begin_change()
    assert plan_canvas_outline.follow(canvas, drag, (780.004, 560.0), False)
    canvas.end_change()
    assert canvas.source["outlines"][0]["points"][2] == [780, 560], "to a hundredth of a sheet unit, as every point of the plan"
    assert plan_centres.state(canvas.source)["mass"]["point"] != before, "M follows the outline"
    assert history[-1]["outlines"][0]["points"] == OUTLINE, "one step of «Annuler»"
    # moved whole by its edge, Shift keeping the move straight
    canvas.drag = None
    assert plan_canvas_outline.press_edge(canvas, (100, 300), canvas.tolerance())
    assert plan_canvas_outline.follow(canvas, canvas.drag, (150, 304), True)
    assert canvas.source["outlines"][0]["points"][0] == [150, 100], "Shift: horizontal"
    canvas.drag = None
    # «Déplacer» moves it; «Copier» and «Dupliquer» make no second one, and say so
    canvas.set_tool("move")
    for p in ((150, 100), (100, 100)):
        canvas._forced = p
        plan_canvas_edit.click(canvas, p, False)
    canvas._forced = None
    assert canvas.source["outlines"][0]["points"][0] == [100, 100]
    said = []
    canvas.edit_refused.connect(said.append)
    canvas.select(("outline", 0))
    steps = len(history)
    assert canvas.single_selected() == "outline" and canvas.duplicate_selection() is False
    canvas.set_tool("copy")
    for p in ((100, 100), (300, 300)):
        canvas._forced = p
        plan_canvas_edit.click(canvas, p, False)
    canvas._forced = None
    assert said and set(said) == {"outline"} and len(canvas.source["outlines"]) == 1
    assert len(history) == steps and canvas.drawing == [], "refused at the first click: no base point taken, no step of «Annuler» opened for nothing"
    canvas.select(("element", 0))
    assert canvas.single_selected() is None
    # its corners are snap points behind «Accrocher aux éléments», and none of its own while one is dragged
    canvas.set_tool("select")
    canvas.snap_elements = True
    assert (100.0, 100.0) in plan_canvas_outline.snap_points(canvas) and plan_canvas_outline.snap_points(canvas, ("outline", 0)) == []
    p, kind = canvas.snapped((101, 101))
    assert tuple(p) == (100.0, 100.0) and kind == "vertex"
    # Delete takes it away, and the plan is the file it was before one was drawn: no empty list left behind, no 1.8 for nothing
    canvas.select(("outline", 0))
    canvas.delete_selection()
    assert "outlines" not in canvas.source and canvas.selection is None
    for element in canvas.source["elements"]:
        element.pop("construction", None)
    assert model.version_of(canvas.source) == "1.6"


def test_the_window_draws_s_and_m_whatever_the_plan_prints_and_they_follow_the_drawing():
    source = dict(_source(), outlines=[{"points": copy.deepcopy(OUTLINE)}])
    assert "print_centres" not in source
    canvas, _history = _canvas(source)
    drawn = plan_svg.render(canvas.drawn_source(), centres=True)
    assert ">S</text>" in drawn and ">M</text>" in drawn and canvas.overlay_renderer.isValid()
    seen = []
    original = plan_svg.render

    def spy(*args, **kwargs):
        seen.append(kwargs.get("centres"))
        return original(*args, **kwargs)
    plan_svg.render = spy
    try:
        canvas.redraw()
        # a wall moved: S has moved, nothing saved
        before = plan_centres.state(canvas.source)["stiffness"]["point"]
        canvas.select(("element", 1))
        canvas.begin_change()
        canvas.translate_selection(-200, 0)
        canvas.end_change()
        after = plan_centres.state(canvas.source)["stiffness"]["point"]
        # another plan shown over this one is drawn without its own centres
        over = canvas.superposition_svg(source, source)
    finally:
        plan_svg.render = original
    assert seen[0] is True and after[0] < before[0] - 100
    assert seen[-1] in (None, False) and plan_svg.CENTRES_OPEN not in over


# --- the tab: the tool's button, the card, the construction mode ---------------------------------------------------

@contextlib.contextmanager
def _dialogs():
    """Nothing modal can block the run: a question says yes."""
    from PySide6.QtWidgets import QFileDialog, QMessageBox
    stubs = {
        (QMessageBox, "warning"): staticmethod(lambda *a, **k: QMessageBox.StandardButton.Ok),
        (QMessageBox, "critical"): staticmethod(lambda *a, **k: QMessageBox.StandardButton.Ok),
        (QMessageBox, "information"): staticmethod(lambda *a, **k: QMessageBox.StandardButton.Ok),
        (QMessageBox, "question"): staticmethod(lambda *a, **k: QMessageBox.StandardButton.Yes if len(a) < 4 else QMessageBox.StandardButton.Discard),
        (QFileDialog, "getOpenFileName"): staticmethod(lambda *a, **k: ("", "")),
    }
    originals = {key: key[0].__dict__[key[1]] for key in stubs}
    for (owner, attr), stub in stubs.items():
        setattr(owner, attr, stub)
    try:
        yield
    finally:
        for (owner, attr), original in originals.items():
            setattr(owner, attr, original)


def _window():
    if "window" not in _STATE:
        app = _qt()
        here = conftest.project_copy("plan_centres_window")
        with project.using(here), _dialogs():
            import woodcore_gui
            window = woodcore_gui.MainWindow()
        _STATE.update(app=app, window=window, here=here)
    return _STATE["window"], _STATE["here"]


def _tab(kind="PlanTab"):
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


def _settle():
    from PySide6.QtCore import QCoreApplication, QEvent
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete.value)   # the card of the previous selection really gone


def _combo_with(parent, data):
    from PySide6.QtWidgets import QComboBox
    return next((c for c in parent.findChildren(QComboBox) if c.findData(data) >= 0), None)


def test_the_tool_has_its_button_and_its_hint_on_a_floor_plan_and_not_on_a_section():
    import plan_canvas_outline
    tab, here = _tab()
    with project.using(here), _dialogs():
        _open(tab, _source())
        button = tab.tool_buttons[plan_canvas_outline.TOOL]
        assert not button.isHidden() and button.toolTip() == tab.t("plan_tip_outline") and not button.icon().isNull()
        tab.choose_tool(plan_canvas_outline.TOOL)
        assert tab.canvas.tool == plan_canvas_outline.TOOL and tab.hint.text() == tab.t("plan_hint_outline")
        assert not tab.drawing_tool(), "the outline is no element: the pane does not turn into an element's options"
        # every language has the tool's words, and they are not one another's
        import plan_tab_words
        for key in ("plan_tool_outline", "plan_tip_outline", "plan_hint_outline", "plan_outline_selected", "plan_outline_single",
                    "plan_group_centres", "plan_print_centres", "plan_clt_power", "plan_construction", "plan_construction_none", "plan_centres_stiffness", "plan_centres_mass"):
            words = [plan_tab_words.STRINGS[lang][key] for lang in ("fr", "de", "en")]
            assert all(words) and len(set(words)) == 3, key
        # drawn through the tab: one step of «Annuler», which takes it back
        tab.choose_tool("select")
        tab.canvas.set_tool(plan_canvas_outline.TOOL)
        for p in OUTLINE + [OUTLINE[0]]:
            _click(tab.canvas, p)
        assert tab.source["outlines"] == [{"points": OUTLINE}] and tab.canvas.tool == "select", "the tab goes back to «Sélection»"
        _settle()
        assert tab.has_selection() and tab.t("plan_outline_selected") in [label.text() for label in tab.selection_group.findChildren(type(tab.hint))]
        tab.undo()
        assert not tab.source.get("outlines")
        tab.redo()
        assert tab.source["outlines"] == [{"points": OUTLINE}]
        # «Copier» on it is refused, and said where the hint is
        tab.canvas.select(("outline", 0))
        tab.canvas.duplicate_selection()
        assert tab.hint.text() == tab.t("plan_outline_single")
        # a section has neither the tool nor the outline: switching takes it out in the step that switches, and brings it back with «Annuler»
        tab.canvas.select(None)
        tab.plan_type_combo.setCurrentIndex(tab.plan_type_combo.findData("section"))
        assert not tab.source.get("outlines") and button.isHidden() and not tab.tool_shown(plan_canvas_outline.TOOL)
        tab.choose_tool(plan_canvas_outline.TOOL)
        assert tab.canvas.tool == "select", "refused on a section"
        assert tab.centres_group.isHidden(), "no stiffness centre on an elevation: no card"
        tab.undo()
        assert tab.source["outlines"] == [{"points": OUTLINE}] and model.plan_type(tab.source) == "floor"
        tab.fill()
        tab.on_changed()
        assert not button.isHidden() and not tab.centres_group.isHidden()
        tab.dirty = False


def test_the_card_says_what_each_centre_stands_on_or_why_it_is_not_there():
    tab, here = _tab()
    window = tab.app
    language = window.lang
    card = None
    try:
        with project.using(here), _dialogs():
            _open(tab, _source())
            card = tab.centres_card
            assert tab.t("plan_group_centres") in [c.title() for c in tab.visible_modules()], "a module of the plan, with nothing selected"
            tab.canvas.select(("element", 0))
            assert tab.centres_group.isHidden(), "the pane is the selection's then"
            tab.canvas.select(None)
            # S on four timber frame walls, to the power 1; no outline, no M -- by the sentence the warnings say
            note = plan_centres.state(tab.source)["mass_note"]
            for lang in ("fr", "de", "en"):
                window.lang = lang
                card.refresh()
                assert card.stiffness.text() == tab.t("plan_centres_stiffness", walls=4, mode=tab.t("warn_plan_construction_timber_frame"), power="1"), lang
                assert card.mass.text() == window.note_text(note), lang
                assert card.mass.text() != str(note), (lang, "the window's own sentence, not the export's English")
                assert card.mass.text() == tab.t("warn_plan_centres_no_outline", plan="P90"), lang
            window.lang = language
            assert not card.form.isRowVisible(card.power), "no CLT wall: no power to choose"
            # mixed modes: no S, and the reason names the modes found
            tab.canvas.select(("element", 3))
            tab.set_construction("concrete")
            tab.canvas.select(None)
            mixed = plan_centres.state(tab.source)["stiffness_note"]
            assert mixed.code == "plan_centres_mixed" and card.stiffness.text() == window.note_text(mixed)
            assert "3" in card.stiffness.text() and "1" in card.stiffness.text()
            tab.undo()
            assert tab.source["elements"][3]["construction"] == "timber_frame", "one step of «Annuler»"
            # CLT: the power is asked for, S waits for it, and it is the plan's
            for element in tab.source["elements"]:
                element["construction"] = "clt"
            tab.canvas.invalidate()
            tab.on_changed()
            assert card.form.isRowVisible(card.power) and card.power.currentData() is None
            assert card.stiffness.text() == window.note_text(plan_centres.state(tab.source)["stiffness_note"]) and plan_centres.state(tab.source)["stiffness_note"].code == "plan_centres_no_power"
            card.power.setCurrentIndex(card.power.findData(2.0))
            card.on_power(0)
            assert tab.source["clt_power"] == 2.0 and plan_centres.state(tab.source)["stiffness"]["power"] == 2.0
            assert card.stiffness.text() == tab.t("plan_centres_stiffness", walls=4, mode=tab.t("warn_plan_construction_clt"), power="2")
            # the switch: written where it is on, taken out where it is off, one step each
            assert not card.print_box.isChecked()
            card.print_box.setChecked(True)
            assert tab.source["print_centres"] is True
            # asked for and no outline: the warning under the plan is the card's own sentence
            assert window.note_text(plan_centres.state(tab.source)["mass_note"]) in tab.message.toPlainText()
            card.print_box.setChecked(False)
            assert "print_centres" not in tab.source
            assert window.note_text(plan_centres.state(tab.source)["mass_note"]) not in tab.message.toPlainText(), "not printed: said in the card, not among the warnings"
            # an outline: M, and the draft checks at the version it will be written at -- no message for a plan read as 1.6
            tab.edit(lambda: tab.source.__setitem__("outlines", [{"points": copy.deepcopy(OUTLINE)}]))
            assert card.mass.text() == tab.t("plan_centres_mass") and tab.source["schema_version"] == "1.6"
            assert "schema_version" not in tab.message.toPlainText(), tab.message.toPlainText()
    finally:
        window.lang = language
        if card is not None:
            card.refresh()
        tab.dirty = False


def test_a_bracing_wall_and_its_tool_have_their_construction_mode_and_no_default():
    tab, here = _tab()
    with project.using(here), _dialogs():
        _open(tab, _source(mode=None))
        # a wall already drawn has no mode: «non défini», and S waits for it -- the card names the walls
        tab.canvas.select(("element", 0))
        _settle()
        combo = _combo_with(tab.selection_group, "timber_frame")
        assert combo is not None and combo.currentData() is None and combo.itemText(0) == tab.t("plan_construction_none")
        assert [combo.itemData(i) for i in range(combo.count())] == [None, *plan_centres.MODES]
        assert combo.itemText(combo.findData("clt")) == tab.t("warn_plan_construction_clt"), "the mode's word is the one the warnings name it by"
        tab.canvas.select(None)
        note = plan_centres.state(tab.source)["stiffness_note"]
        assert note.code == "plan_centres_no_mode" and "W101" in tab.centres_card.stiffness.text() and "H102" in tab.centres_card.stiffness.text()
        # chosen for the selected wall: one step; a beam and a bearing wall have no such row
        tab.canvas.select(("element", 0))
        tab.set_construction("clt")
        assert tab.source["elements"][0]["construction"] == "clt"
        tab.set_construction(None)
        assert "construction" not in tab.source["elements"][0]
        tab.undo()
        assert tab.source["elements"][0]["construction"] == "clt"
        tab.edit(lambda: tab.source["elements"].append({"type": "V", "label": "V101", "points": [[10, 10], [60, 10]]}))
        tab.canvas.select(("element", 4))
        _settle()
        assert _combo_with(tab.selection_group, "timber_frame") is None, "a bearing wall braces nothing: a field with no effect is no field"
        # the tool: its pane shows the mode the next wall takes, «non défini» first, kept for the walls after it
        tab.canvas.select(None)
        tab.canvas.tool_defaults.pop("W", None)
        tab.choose_tool("W")
        _settle()
        combo = _combo_with(tab.selection_group, "concrete")
        assert combo is not None and combo.currentData() is None
        combo.setCurrentIndex(combo.findData("concrete"))
        combo.activated.emit(combo.currentIndex())
        assert tab.canvas.tool_defaults["W"]["construction"] == "concrete"
        for a, b in (((200, 200), (300, 200)), ((200, 300), (300, 300))):
            tab.canvas.add_element("W", [a, b])
        assert [element.get("construction") for element in tab.source["elements"][-2:]] == ["concrete", "concrete"]
        assert tab.source["elements"][0]["construction"] == "clt", "changing the tool's mode touches no wall drawn"
        # ... and choosing «non défini» again takes the default back
        combo = _combo_with(tab.selection_group, "concrete")
        combo.setCurrentIndex(0)
        combo.activated.emit(0)
        assert "construction" not in tab.canvas.tool_defaults["W"]
        tab.choose_tool("T")
        _settle()
        assert _combo_with(tab.selection_group, "concrete") is None
        tab.choose_tool("select")
        tab.dirty = False


def test_a_mode_against_its_positions_section_is_a_warning_under_the_plan():
    """ARCH-009, the window's path: the tab hands the positions' section types to the plan's warnings -- the project's, and those chosen in the pane and not saved yet."""
    import positions_store
    tab, here = _tab()
    with project.using(here), _dialogs():
        _open(tab, _source())
        positions, by_id = tab.positions, tab.position_by_id
        try:
            tab.positions = list(positions) + [{"position": "W101", "type": "Wand", "section_type": "clt", "dimension": "20/30/20", "units": "mm"}]
            tab.position_ids = [row["position"] for row in tab.positions]
            assert tab.section_types()["W101"] == "clt"
            tab.on_changed()
            note = next(n for n in model.warnings(tab.source, tab.position_ids, sections=tab.section_types()) if getattr(n, "code", "") == "plan_centres_section")
            assert tab.app.note_text(note) in tab.message.toPlainText() and "W101" in tab.app.note_text(note)
            assert tab.t("warn_plan_construction_timber_frame") in tab.app.note_text(note), "the mode named in the window's language"
            tab.canvas.select(("element", 0))
            tab.set_construction("clt")
            assert "W101" not in "".join(line for line in tab.message.toPlainText().splitlines() if "CLT" in line and "section" in line.lower())
            # a section chosen in the pane and not saved yet counts as the position's
            tab.source.setdefault(tab.PENDING_KEY, {})["H101"] = {"type": "Wand", "section_type": "clt", "dimension": "20/20/20", "units": "mm"}
            assert tab.section_types()["H101"] == "clt"
            assert positions_store.section_types(tab.pending_rows()) == {"H101": "clt"}
        finally:
            tab.source.pop(tab.PENDING_KEY, None)
            tab.positions, tab.position_by_id = positions, by_id
            tab.position_ids = [row["position"] for row in positions]
            tab.canvas.select(None)
            tab.dirty = False


def test_every_reason_has_its_one_sentence_in_the_three_languages():
    """ARCH-011: each reason the calculation gives is an `engine.Note` of a code, and the window has its sentence in French, German and English -- the holes of each filled by the note's own arguments, so a sentence and its note cannot drift apart."""
    _qt()
    import woodcore_gui
    import woodcore_gui_words
    mixed = _source()
    mixed["elements"][3]["construction"] = "concrete"
    parallel = _source()
    parallel["elements"] = parallel["elements"][:2]
    cross = _source()
    cross["elements"] = [{"type": "W", "label": "W101", "construction": "timber_frame", "points": [[100, 300], [700, 300]]},
                         {"type": "W", "label": "W102", "construction": "timber_frame", "points": [[400, 100], [400, 500]]}]
    states = [plan_centres.state(source) for source in (
        dict(_source(), elements=[]), _source(mode=None), mixed, _source(mode="clt"), parallel, cross,
        dict(_source(), outlines=[{"points": [[0, 0], [50, 50], [100, 100]]}]))]
    notes = [note for found in states for note in (found["stiffness_note"], found["mass_note"], *found["remarks"]) if note is not None]
    notes += plan_centres.warnings(_source(), {"W101": "clt"})
    notes += [plan_centres.mode_note(mode) for mode in plan_centres.MODES]
    codes = {note.code for note in notes}
    assert codes == {"plan_centres_no_walls", "plan_centres_no_mode", "plan_centres_mixed", "plan_centres_no_power", "plan_centres_one_direction", "plan_centres_no_torsion",
                     "plan_centres_no_outline", "plan_centres_flat_outline", "plan_centres_section",
                     "plan_construction_timber_frame", "plan_construction_clt", "plan_construction_concrete"}, codes
    for note in notes:
        said = [woodcore_gui.note_text(note, lang) for lang in ("fr", "de", "en")]
        assert all(said) and len(set(said)) >= (1 if note.code == "plan_construction_clt" else 2), (note.code, said)   # «CLT» is CLT in French and in English
        assert not any("{" in text for text in said), (note.code, said)
        for lang in ("fr", "de", "en"):
            assert "warn_" + note.code in woodcore_gui_words.STRINGS[lang], (note.code, lang)
    # a wall's number and the mode found are named, the mode in the window's language
    section = next(note for note in notes if note.code == "plan_centres_section")
    assert "W101" in woodcore_gui.note_text(section, "fr") and "ossature bois" in woodcore_gui.note_text(section, "fr") and "Holzrahmenbau" in woodcore_gui.note_text(section, "de")


def test_a_call_may_leave_them_out_from_the_command_builder_and_the_switch_is_worded_once():
    """UI-007, ARCH-011: the «Affichage» view's builder writes `centres: false` and nothing at the default; the switch reads alike in the builder and on an export sheet's plan view -- two tables, held to one wording here (a document's plan had a third until the spec 2026-10-21-commandes-typst-refonte)."""
    _qt()
    import plan_command_builder
    import sheet_editor_words
    assert "centres" not in plan_command_builder.command_text({"plan": "P01"})
    # a native figure since the spec 2026-10-21-commandes-typst-refonte (REQ-013): the centres a word of `detail-figure` left out
    assert plan_command_builder.command_text({"plan": "P01", "centres": False}) == '#figure(image-positions-plan("P01", detail-figure: ("length", "axes", "dimensions")), kind: image, caption: [P01]) <fig-p01>'
    for lang in ("fr", "de", "en"):
        words = {plan_command_builder.STRINGS[lang]["pcb_centres"], sheet_editor_words.STRINGS[lang]["se_centres"]}
        assert len(words) == 1 and all(words), (lang, words)
    tab, here = _tab()
    with project.using(here), _dialogs():
        options = tab.builder.options if hasattr(tab.builder, "options") else tab.builder
        box = options.centres
        assert box.isChecked() and box.text() == plan_command_builder.STRINGS[tab.app.lang]["pcb_centres"]
        assert options.values()["centres"] is True
        box.setChecked(False)
        assert options.values()["centres"] is False
        box.setChecked(True)


def test_the_fire_protection_plan_has_none_of_it():
    import plan_canvas_outline
    tab, here = _tab("FireTab")
    with project.using(here), _dialogs():
        assert plan_canvas_outline.TOOL not in tab.tool_buttons, "bracing walls are the position plan's: no outline tool (rule 16, docs/domain/fire-plans.md)"
        assert not hasattr(tab, "centres_card")
        titles = [card.title() for card, _when in tab.modules]
        plan_tab, _here = _tab("PlanTab")
        assert plan_tab.t("plan_group_centres") not in titles
        # its «Affichage» builder offers no such switch either, and writes no such argument
        options = tab.builder.options if hasattr(tab.builder, "options") else tab.builder
        assert options.centres.isHidden() and "centres" not in options.values()
