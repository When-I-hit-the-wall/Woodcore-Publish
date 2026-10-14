"""Woodcore's «Plan de protection incendie» tab and its canvas (docs/domain/position-plans.md §3.3sexies, docs/ui/window.md §10quater; calc/tools/fire_tab.py, fire_canvas.py), built off-screen -- origin/Gian's tests of v0.112, ported with the tab onto the position plan's base (drawing_tab.DrawingTab) in v0.115, and the tests of what the port made of it: the documents shared with the position plans, a page ticked into a fire plan that follows its one position plan or has a frame of its own, the crop shown alone, a calibration refused where the plan follows, a page turned in either tab turning both kinds, a position plan archived detaching the fire plans that follow it, Gian's 1.0 sources opened without being written, and the tab shown in the base de projet and the report and not in the convention.

What is held, and against what:

* **The tab is registered where the engineer looks for it**: in the «Projet» group right under «Plan de positions» (v0.115, the engineer's order), with an icon and its words in the three languages -- the same keys in each, no ß in the Swiss German, and a sentence for every warning calc/domains/fire.py makes.
* **A plan that follows a position plan shows that plan's frame** -- its sheet, its crop, its scale -- and cannot change its background or its scale from here: those and the calibration are greyed, and say why. Its crop it may state for itself (drawn here, taken back with «Reprendre»). The frame it follows is read afresh, so a position plan changed in its own tab is followed.
* **Everything is drawn by hand, and nothing is delimited**: the tools the program had for rooms -- the wand, the barrier, the cut, «Proposer les zones», «Fusionner», the walls on the contour -- and their words are gone.
* **The tools draw what the plan holds**: a surface of the kind the bar's combo says, a wall of its fire resistance, a door in three clicks (the hinge, the other jamb, the side it opens to) that is previewed as the pointer moves and states no `class` when it has no fire resistance, an escape route's length, an emergency exit and an escape route's width; the sources they make are all ones fire.check_source accepts.
* **The selection's card changes an entry already drawn** -- the kind of the surfaces, the fire resistance of the walls, the kind and the fire resistance of the doors, the two flips of a door, the text of a width -- for every entry selected at once and in ONE step of the history; the four lists are the plan's and follow the canvas's selection both ways.
* **The legend is a check box and a box on the plan**: switched on it is put where fire.legend_default says, a press inside it with the selection tool drags it -- before anything under it is hit --, one step of the history for the whole drag, and it is no entry: it is not selected and Delete does not remove it.
* **The right pane is the position plan's**, card by card: «Taille des symboles» holds the plan's two factors; the selection's «Taille et opacité propres» offers the factors every entry selected may state -- orange with «Reprendre» where one is stated -- and the opacity they are drawn at, and where the one text selected stands; the legend has a size of its own; «Cadrage» says whose crop is in force for a plan that follows a position plan; the last card holds the calls that print the plan. Each change of them is one step of the history, a drag included, and none widens the pane.
* **A drag does not stutter**: while a point or the legend is dragged the handles follow the pointer at once and the overlay -- every length and area measured again -- is rendered at most every DRAG_REDRAW_MS (the engineer asked for half a second), and once more when the button is let go.
* **Saving is writing the source and exporting it**: fire/<id>.json, readable again by calc/domains/fire.py, and data/fire.json beside it; a duplicate under another id and «Supprimer» that archives and exports again.

⚠️ Every message box and dialog is stubbed -- a modal off-screen never comes back -- and the project the tab works on is a copy made for the run (conftest.project_copy).
"""

import contextlib
import json
import os
import sys

import conftest
from conftest import ROOT, Skip

import project
from domains import figure_style, fire

TOOLS = str(ROOT / "calc" / "tools")


def _qt():
    if TOOLS not in sys.path:
        sys.path.insert(0, TOOLS)
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:
        raise Skip(f"PySide6 is not installed ({exc})")
    return QApplication.instance() or QApplication([])


@contextlib.contextmanager
def _dialogs():
    """Nothing modal can block the run: a yes/no question says yes, a save/discard/cancel one discards, a choice picks «Fond propre…», the file dialog chooses nothing."""
    from PySide6.QtWidgets import QFileDialog, QInputDialog, QMessageBox
    stubs = {
        (QMessageBox, "warning"): staticmethod(lambda *a, **k: QMessageBox.StandardButton.Ok),
        (QMessageBox, "critical"): staticmethod(lambda *a, **k: QMessageBox.StandardButton.Ok),
        (QMessageBox, "information"): staticmethod(lambda *a, **k: QMessageBox.StandardButton.Ok),
        (QMessageBox, "question"): staticmethod(lambda *a, **k: QMessageBox.StandardButton.Yes if len(a) < 4 else QMessageBox.StandardButton.Discard),
        (QFileDialog, "getOpenFileName"): staticmethod(lambda *a, **k: ("", "")),
        (QInputDialog, "getItem"): staticmethod(lambda parent, title, label, items, *a, **k: (items[0], True)),
        (QInputDialog, "getText"): staticmethod(lambda *a, **k: ("Dossier_77", True)),
    }
    originals = {key: key[0].__dict__[key[1]] for key in stubs}
    for (owner, attr), stub in stubs.items():
        setattr(owner, attr, stub)
    try:
        yield
    finally:
        for (owner, attr), original in originals.items():
            setattr(owner, attr, original)


def _without_fire_plans(copied):
    """The copy of the example project with no fire-protection plan in it: neither a source nor anything of one in its export. The example project carries two of its own -- `Pavillon-EG` and `Treppenhaus`, which the worked examples of `show-fire-plan` name -- and every test here but one draws its own plans and counts them, so it starts from none."""
    for source in fire.source_paths(copied.fire_dir):
        source.unlink()
    (copied.data_dir / fire.EXPORT_FILE).unlink(missing_ok=True)
    figures = copied.data_dir / "fire"
    if figures.is_dir():
        for figure in figures.iterdir():
            figure.unlink()


@contextlib.contextmanager
def _tab(name, own_plans=False):
    """(window, tab, the project copy) with every dialog stubbed; the window is closed once the draft is let go. The copy holds no fire-protection plan unless `own_plans` keeps the example project's own two (_without_fire_plans)."""
    app = _qt()
    copied = conftest.project_copy(name)
    if not own_plans:
        _without_fire_plans(copied)
    with project.using(copied), _dialogs():
        import woodcore_gui
        window = woodcore_gui.MainWindow()
        tab = next(t for t in window.tabs if type(t).__name__ == "FireTab")
        try:
            yield window, tab, copied
        finally:
            tab.dirty = False
            conftest.dispose(window)
            app.processEvents()


def _draw(tab, ring):
    """An outline drawn through the canvas's own tool, point by point, then finished."""
    canvas = tab.canvas
    tab.choose_tool("polygon")
    for point in ring:
        canvas.add_point(point)
    canvas.finish_drawing()


def _square(x, y, size=200):
    return [(x, y), (x + size, y), (x + size, y + size), (x, y + size)]


def _fresh(tab, plan=None):
    """An unsaved draft of a floor, at one pixel to the sheet unit -- the pick tolerance is a few units, not the hundreds the fitted view of an unshown window would make it."""
    tab.open_source(fire.new_source("T1", plan), None, False)
    tab.canvas.resetTransform()
    return tab.source


def _scaled(tab):
    """A draft with a frame of its own and a scale of 30 sheet units to the metre."""
    source = fire.new_source("T1")
    source["scale"] = {"mode": "calibration", "points": [[0, 0], [300, 0]], "length_m": 10}
    tab.open_source(source, None, False)
    tab.canvas.resetTransform()
    return tab.source


def _line(tab, tool, points):
    """A wall or an escape route's length drawn through the canvas's own tool, point by point, then finished."""
    tab.choose_tool(tool)
    for point in points:
        tab.canvas.add_point(point)
    tab.canvas.finish_drawing()


def _door(tab, hinge, jamb, side):
    """A door drawn through the canvas's own tool: three clicks."""
    tab.choose_tool("door")
    for point in (hinge, jamb, side):
        tab.canvas.add_point(point)


def _events(canvas):
    """A maker of the mouse events a drag is made of, at scene coordinates."""
    from PySide6.QtCore import QEvent, QPointF, Qt
    from PySide6.QtGui import QMouseEvent

    def event(kind, scene, buttons, button=Qt.MouseButton.LeftButton, modifiers=Qt.KeyboardModifier.NoModifier):
        pos = QPointF(canvas.mapFromScene(QPointF(*scene)))
        return QMouseEvent(kind, pos, canvas.viewport().mapToGlobal(pos), button, buttons, modifiers)

    return event, QEvent


def _drag(canvas, start, stops):
    """A press at `start`, a move to each of `stops`, and the release at the last: what a drag of the selection tool is."""
    from PySide6.QtCore import Qt
    event, QEvent = _events(canvas)
    canvas.mousePressEvent(event(QEvent.Type.MouseButtonPress, start, Qt.MouseButton.LeftButton))
    for scene in stops:
        canvas.mouseMoveEvent(event(QEvent.Type.MouseMove, scene, Qt.MouseButton.LeftButton, Qt.MouseButton.NoButton))
    canvas.mouseReleaseEvent(event(QEvent.Type.MouseButtonRelease, stops[-1], Qt.MouseButton.NoButton))


# --- registered ---------------------------------------------------------------------------------

def test_every_warning_of_the_fire_module_has_a_sentence_in_each_language():
    _qt()
    import woodcore_gui
    frame_less = {"id": "B1", "label": "", "plan": "Gone", "zones": []}
    gone = fire.warnings(frame_less, {})
    own = {"id": "B2", "label": "", "sheet": {"width": 100, "height": 100}, "zones": [{"id": "Z1", "points": [[500, 500], [600, 500], [600, 600]]}]}
    scaleless = fire.warnings(own, {})
    codes = {note.code for note in gone + scaleless}
    assert codes == {"fire_plan_gone", "fire_no_scale", "fire_zone_outside"}, codes
    for note in gone + scaleless:
        for lang in ("fr", "de", "en"):
            text = woodcore_gui.note_text(note, lang)
            assert text != str(note) and "{" not in text and note.args["fire"] in text, (lang, note.code, text)
    # without a scale nothing is measured, whatever it is: no area, no length, no width -- and nothing is said of delimiting any more
    import fire_tab
    for lang in ("fr", "de", "en"):
        assert "{fire}" in fire_tab.STRINGS[lang]["warn_fire_no_scale"]


def test_what_the_delimiting_had_is_gone_from_the_tab_the_canvas_and_the_words():
    _qt()
    import fire_canvas
    import fire_tab
    for lang, words in fire_tab.STRINGS.items():
        dead = [key for key in words if any(part in key for part in ("wand", "barrier", "_cut", "propose", "merge", "detection", "contour", "refused", "_gap", "_thin", "min_area"))]
        assert not dead, (lang, dead)
        assert not [key for key, text in words.items() if "Baguette" in text or "Barrière" in text or "Fusionner" in text], lang
    assert not hasattr(fire_tab, "fire_render") and not hasattr(fire_tab, "QDoubleSpinBox")
    for tool in ("wand", "barrier", "cut"):
        assert tool not in fire_tab.TOOLS and tool not in fire_tab.NAMES and tool not in fire_tab.HINTS, tool
        assert tool not in fire_canvas.DRAWING_TOOLS, tool
    for name in ("wand_clicked", "cut_drawn", "add_barrier", "click_line"):
        assert not hasattr(fire_canvas.FireCanvas, name), name
    with _tab("fire_tab_gone") as (window, tab, copied):
        assert [t for t in tab.tool_buttons] == list(fire_tab.TOOLS)
        for name in ("propose_button", "merge_button", "contour_button", "merge_selection_button", "detection_spins", "detect_result", "walls_cache",
                     "prepare_walls", "propose", "on_wand", "merge", "on_cut", "contour", "on_detection", "refused"):
            assert not hasattr(tab, name), name
        assert not hasattr(tab.canvas, "wand_clicked") and not hasattr(tab.canvas, "cut_drawn")
        # the bar, in the order the engineer asked for
        assert list(fire_tab.TOOLS) == ["select", "pan", "ruler", "move", "copy", "polygon", "wall", "door", "route", "exit", "width", "text"]   # the ruler since issue #9, «Déplacer» and «Copier» since issue #18 (D-015: no construction aid on the fire plan), «Texte» since issue #43
        # the crop and the calibration left the bar for the right pane (v0.116)
        assert list(fire_tab.PANE_TOOLS) == ["crop", "calibrate"] and "crop" not in tab.tool_buttons and "calibrate" not in tab.tool_buttons
        assert tab.tool_buttons["polygon"].text() == tab.t("fp_tool_polygon") and tab.tool_buttons["route"].text() == tab.t("fp_tool_route")


# --- following a position plan --------------------------------------------------------------------

def test_a_draft_following_a_position_plan_shows_its_frame_and_cannot_change_it_from_here():
    with _tab("fire_tab_follow") as (window, tab, copied):
        frames = fire.plan_frames(copied.plans_dir)
        assert "Pavillon" in frames
        source = tab_source = fire.new_source("T1", "Pavillon")
        tab.open_source(source, None, False)
        pav = frames["Pavillon"]
        assert tab.frame()["crop"] == pav["crop"] and tab.frame()["sheet"] == pav["sheet"]
        assert not tab.own_frame() and tab.canvas.frame_source()["crop"] == pav["crop"] and tab.canvas.frame_source()["sheet"] == pav["sheet"]
        assert tab.canvas.sheet_rect().width() == pav["sheet"]["width"]
        assert tab.follow_combo.currentData() == "Pavillon"
        # the scale is the position plan's; the crop is drawn here, over the position plan's (the plan may state one for itself)
        assert tab.crop_draw_button.isEnabled() and not tab.calibrate_button.isEnabled()
        assert tab.calibrate_button.toolTip() == tab.t("fp_follow_tip")
        assert not tab.scale_mode.isEnabled() and not tab.opacity.isEnabled()
        assert not tab.reset_crop_button.isVisibleTo(tab.crop_group), "«Feuille entière» has no meaning for a crop that is the position plan's"
        assert "Pavillon" not in tab_source and not [key for key in fire.FRAME_KEYS if key in tab_source]
        # a tool that needs a frame of its own is not chosen
        tab.choose_tool("calibrate")
        assert tab.canvas.tool == "select"
        tab.choose_tool("crop")
        assert tab.canvas.tool == "crop"
        tab.choose_tool("select")
        # its own frame, chosen: the frame it followed is copied in, nothing jumps, and the tools come back -- in one step of «Annuler»
        steps = len(tab.undo_stack)
        index = tab.follow_combo.findData("")
        tab.follow_combo.setCurrentIndex(index)
        assert tab.own_frame() and "plan" not in tab.source
        assert tab.source["crop"] == pav["crop"] and tab.source["sheet"] == pav["sheet"]
        assert len(tab.undo_stack) == steps + 1
        assert tab.crop_draw_button.isEnabled() and tab.calibrate_button.isEnabled() and tab.scale_mode.isEnabled()
        assert tab.reset_crop_button.isVisibleTo(tab.crop_group), "a plan with a frame of its own takes the whole sheet back"
        fire.check_source(tab.source, "t")
        tab.undo()
        assert not tab.own_frame() and tab.source["plan"] == "Pavillon" and tab.follow_combo.currentData() == "Pavillon"
        # and the other way round
        tab.follow_combo.setCurrentIndex(tab.follow_combo.findData("Fluchttreppe"))
        assert tab.source["plan"] == "Fluchttreppe" and not [key for key in fire.FRAME_KEYS if key in tab.source]


def test_a_position_plan_changed_in_its_own_tab_is_followed_when_the_tab_is_shown_again():
    with _tab("fire_tab_shown") as (window, tab, copied):
        tab.open_source(fire.new_source("T1", "Pavillon"), None, False)
        path = copied.plans_dir / "Pavillon.json"
        plan = json.loads(path.read_text(encoding="utf-8"))
        plan["crop"] = {"x": 10, "y": 20, "w": 300, "h": 200}
        path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
        assert tab.frame()["crop"] != plan["crop"], "read before the tab is shown again"
        tab.on_shown()
        assert tab.frame()["crop"] == plan["crop"]
        rect = tab.canvas.crop_item.rect()
        assert (rect.x(), rect.y(), rect.width(), rect.height()) == (10, 20, 300, 200)
        # a position plan that is gone is kept in the combo, marked, and warned about
        path.unlink()
        tab.on_shown()
        assert tab.follow_combo.currentData() == "Pavillon" and "Pavillon" in tab.follow_combo.currentText()
        assert "Pavillon" in tab.message.toPlainText()


# --- surfaces ----------------------------------------------------------------------------------------

def test_an_outline_drawn_by_clicks_becomes_the_next_surface_of_the_kind_in_the_bar_and_one_undo_removes_it():
    from domains import fire_svg
    with _tab("fire_tab_polygon") as (window, tab, copied):
        _fresh(tab)
        assert tab.surface_combo.currentData() == "horizontal" and tab.canvas.zone_kind == "horizontal"
        _draw(tab, _square(100, 100))
        assert [zone["id"] for zone in tab.source["zones"]] == ["Z1"]
        assert tab.source["zones"][0]["kind"] == "horizontal", "a surface states its kind: the bar's"
        assert tab.canvas.selected == ["Z1"], "the new surface is the selection"
        assert tab.dirty and tab.zone_tree.topLevelItemCount() == 1
        assert [tab.zone_tree.topLevelItem(0).text(0)] == ["Z1"] and tab.zone_tree.topLevelItem(0).isSelected()
        fire.check_source(tab.source, "t")
        _draw(tab, _square(400, 100))
        assert [zone["id"] for zone in tab.source["zones"]] == ["Z1", "Z2"]
        tab.undo()
        assert [zone["id"] for zone in tab.source["zones"]] == ["Z1"]
        tab.undo()
        assert tab.source["zones"] == [] and tab.canvas.selected == [], "an undo took the selected surface away, and the selection with it"
        tab.redo()
        assert [zone["id"] for zone in tab.source["zones"]] == ["Z1"]
        # fewer than three points make nothing, and Escape gives an outline up
        steps = len(tab.undo_stack)
        _draw(tab, [(600, 600), (700, 600)])
        assert len(tab.undo_stack) == steps and len(tab.source["zones"]) == 1
        tab.choose_tool("polygon")
        tab.canvas.add_point((600, 600))
        from PySide6.QtCore import Qt
        from PySide6.QtTest import QTest
        QTest.keyClick(tab.canvas, Qt.Key.Key_Escape)
        assert tab.canvas.drawing == []
        # Backspace takes the last point off the outline being drawn, Return ends it
        tab.canvas.add_point((10, 10))
        tab.canvas.add_point((200, 10))
        QTest.keyClick(tab.canvas, Qt.Key.Key_Backspace)
        assert tab.canvas.drawing == [(10, 10)]
        # the preview follows the bar's tool and is drawn in the colour of what it will be
        assert fire_svg.ZONE_COLOUR.lower() == tab.canvas.preview.pen().color().name().lower()


def test_a_surface_takes_the_kind_the_bar_says_and_the_card_changes_it_for_all_selected_in_one_step():
    from i18n import strings
    from norms import vkf
    with _tab("fire_tab_kind") as (window, tab, copied):
        _fresh(tab)
        canvas = tab.canvas
        # the bar's combo holds the three kinds of the sheet, named in the window's language and drawn in their colour
        assert [tab.surface_combo.itemData(i) for i in range(tab.surface_combo.count())] == list(fire.SURFACES)
        for i, kind in enumerate(fire.SURFACES):
            assert tab.surface_combo.itemText(i) == strings.term(vkf.escape(kind)["label"], tab.app.lang) and not tab.surface_combo.itemIcon(i).isNull()
        _draw(tab, _square(100, 100))
        tab.surface_combo.setCurrentIndex(tab.surface_combo.findData("clear"))
        assert canvas.zone_kind == "clear"
        steps = len(tab.undo_stack)
        assert [zone["kind"] for zone in tab.source["zones"]] == ["horizontal"] and len(tab.undo_stack) == steps, "the bar's combo is the next surface's and never one already drawn"
        _draw(tab, _square(400, 100))
        assert [zone["kind"] for zone in tab.source["zones"]] == ["horizontal", "clear"]
        # one surface: its kind, its name, its area; two of two kinds: the kind shows none
        canvas.select_ids(["Z1"])
        assert tab.zone_box.isVisibleTo(tab) and tab.single_box.isVisibleTo(tab) and tab.zone_kind_combo.currentData() == "horizontal"
        canvas.select_ids(["Z1", "Z2"])
        assert tab.zone_box.isVisibleTo(tab) and not tab.single_box.isVisibleTo(tab) and tab.zone_kind_combo.currentIndex() == -1
        steps = len(tab.undo_stack)
        tab.zone_kind_combo.setCurrentIndex(tab.zone_kind_combo.findData("vertical"))
        assert [zone["kind"] for zone in tab.source["zones"]] == ["vertical", "vertical"] and len(tab.undo_stack) == steps + 1
        assert tab.zone_tree.topLevelItem(1).text(1) == strings.term(vkf.escape("vertical")["label"], tab.app.lang)
        assert tab.zone_kind_combo.currentData() == "vertical", "both share a kind now: the combo shows it"
        fire.check_source(tab.source, "t")
        tab.undo()
        assert [zone["kind"] for zone in tab.source["zones"]] == ["horizontal", "clear"]
        # a draft that states no kind -- one drawn before the kinds existed -- shows none, and is given one by choosing
        draft = tab.source["zones"][0]
        del draft["kind"]
        tab.canvas.invalidate()
        tab.on_changed()
        canvas.select_ids(["Z1"])
        tab.refresh_selection()
        assert tab.zone_kind_combo.currentIndex() == -1 and tab.zone_tree.topLevelItem(0).text(1) == "—"
        tab.zone_kind_combo.setCurrentIndex(tab.zone_kind_combo.findData("clear"))
        assert draft["kind"] == "clear"
        fire.check_source(tab.source, "t")


def test_a_click_selects_the_surface_under_it_ctrl_adds_one_and_delete_removes_them_in_one_step():
    from PySide6.QtCore import QPointF, Qt
    from PySide6.QtTest import QTest
    with _tab("fire_tab_delete") as (window, tab, copied):
        _fresh(tab)
        _draw(tab, _square(100, 100))
        _draw(tab, _square(400, 100))
        canvas = tab.canvas
        canvas.centerOn(350, 200)
        tab.choose_tool("select")

        def click(x, y, modifier=Qt.KeyboardModifier.NoModifier):
            QTest.mouseClick(canvas.viewport(), Qt.MouseButton.LeftButton, modifier, canvas.mapFromScene(QPointF(x, y)))

        click(150, 150)
        assert canvas.selected == ["Z1"] and tab.zone_tree.topLevelItem(0).isSelected() and not tab.zone_tree.topLevelItem(1).isSelected()
        click(450, 150, Qt.KeyboardModifier.ControlModifier)
        assert canvas.selected == ["Z1", "Z2"], "Ctrl adds the surface, the last one in focus"
        assert tab.zone_tree.topLevelItem(0).isSelected() and tab.zone_tree.topLevelItem(1).isSelected()
        click(450, 150, Qt.KeyboardModifier.ControlModifier)
        assert canvas.selected == ["Z1"], "Ctrl on a surface already selected takes it out"
        click(700, 500)
        assert canvas.selected == [], "a click on nothing clears the selection"
        # the list is a way to select too
        tab.zone_tree.topLevelItem(1).setSelected(True)
        assert canvas.selected == ["Z2"]
        canvas.select_ids(["Z1", "Z2"])
        steps = len(tab.undo_stack)
        QTest.keyClick(canvas, Qt.Key.Key_Delete)
        assert tab.source["zones"] == [] and canvas.selected == [] and tab.zone_tree.topLevelItemCount() == 0
        assert len(tab.undo_stack) == steps + 1, "both surfaces went in one step of «Annuler»"
        tab.undo()
        assert [zone["id"] for zone in tab.source["zones"]] == ["Z1", "Z2"]


def test_the_corners_of_the_surface_in_focus_are_dragged_and_a_drag_is_one_step():
    from PySide6.QtCore import QEvent, QPointF, Qt
    from PySide6.QtGui import QMouseEvent
    with _tab("fire_tab_drag") as (window, tab, copied):
        _fresh(tab)
        _draw(tab, _square(100, 100))
        canvas = tab.canvas
        canvas.centerOn(200, 200)
        tab.choose_tool("select")
        zone = tab.source["zones"][0]
        steps = len(tab.undo_stack)

        def event(kind, scene, buttons, button=Qt.MouseButton.LeftButton):
            pos = QPointF(canvas.mapFromScene(QPointF(*scene)))
            return QMouseEvent(kind, pos, canvas.viewport().mapToGlobal(pos), button, buttons, Qt.KeyboardModifier.NoModifier)

        down = event(QEvent.Type.MouseButtonPress, (100, 100), Qt.MouseButton.LeftButton)
        canvas.mousePressEvent(down)
        assert canvas.drag and canvas.drag["kind"] == "vertex" and canvas.drag["vertex"] == 0, "a corner of the surface in focus is what the press takes"
        for scene in ((90, 90), (80, 70), (60, 50)):
            canvas.mouseMoveEvent(event(QEvent.Type.MouseMove, scene, Qt.MouseButton.LeftButton, Qt.MouseButton.NoButton))
        canvas.mouseReleaseEvent(event(QEvent.Type.MouseButtonRelease, (60, 50), Qt.MouseButton.NoButton))
        assert zone["points"][0] == [60, 50] and zone["points"][1] == [300, 100]
        assert len(tab.undo_stack) == steps + 1, "a drag is one step, not one a pixel"
        assert tab.dirty
        tab.undo()
        assert tab.source["zones"][0]["points"][0] == [100, 100]


def test_a_surfaces_name_is_typed_and_is_one_step_of_the_history():
    with _tab("fire_tab_label") as (window, tab, copied):
        _fresh(tab)
        _draw(tab, _square(100, 100))
        steps = len(tab.undo_stack)
        assert tab.single_box.isVisibleTo(tab) and not tab.nothing_label.isVisibleTo(tab)
        tab.zone_label.setText("Bü")
        tab.on_zone_label()
        tab.zone_label.setText("Büro 1")
        tab.on_zone_label()
        assert tab.source["zones"][0]["label"] == "Büro 1"
        assert len(tab.undo_stack) == steps + 1, "a name typed is one step, not one a letter"
        assert tab.zone_tree.topLevelItem(0).text(2) == "Büro 1"
        tab.on_zone_label_done()
        tab.zone_label.setText("")
        tab.on_zone_label()
        assert "label" not in tab.source["zones"][0], "a name emptied is taken off"


# --- walls with a fire resistance and escape routes ----------------------------------------------------

def test_the_wall_tool_draws_a_wall_of_the_class_chosen_in_the_combo_and_one_undo_removes_it():
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest
    from domains import fire_svg
    from i18n import strings
    from norms import vkf
    with _tab("fire_tab_wall") as (window, tab, copied):
        _fresh(tab)
        canvas = tab.canvas
        # the bar's combo holds the ten resistances of the sheet, in its order, named in the window's language and drawn in their colour
        assert [tab.wall_combo.itemData(i) for i in range(tab.wall_combo.count())] == vkf.resistance_keys()
        for i, row in enumerate(vkf.resistances()):
            assert tab.wall_combo.itemText(i) == strings.translate(row["label"], tab.app.lang) and not tab.wall_combo.itemIcon(i).isNull()
        assert tab.wall_combo.currentData() == "EI 30" and canvas.wall_class == "EI 30"
        tab.wall_combo.setCurrentIndex(tab.wall_combo.findData("EI 60"))
        assert canvas.wall_class == "EI 60"
        assert tab.tool_buttons["wall"].toolTip() == tab.t("fp_hint_wall") and tab.tool_buttons["route"].toolTip() == tab.t("fp_hint_route")
        steps = len(tab.undo_stack)
        tab.choose_tool("wall")
        assert tab.hint.text() == tab.t("fp_hint_wall")
        canvas.add_point((100, 100))
        canvas.add_point((300, 100))
        assert canvas.drawing == [(100, 100), (300, 100)] and "walls" not in tab.source
        assert canvas.preview.pen().color().name() == fire_svg.wall_colour("EI 60"), "the line is previewed in the colour of its resistance"
        canvas.add_point((300, 300))
        canvas.finish_drawing()
        assert tab.source["walls"] == [{"id": "W1", "class": "EI 60", "points": [[100, 100], [300, 100], [300, 300]]}]
        assert canvas.selected == ["W1"] and len(tab.undo_stack) == steps + 1 and tab.dirty
        assert tab.wall_tree.topLevelItemCount() == 1 and tab.wall_tree.topLevelItem(0).text(1) == "EI 60" and tab.wall_tree.topLevelItem(0).isSelected()
        assert tab.entry_tabs.currentWidget() is tab.wall_tree, "the list of the entry in focus comes to the front"
        fire.check_source(tab.source, "t")
        # Enter ends a line, a click on its last point does too, Escape gives one up -- and the resistance chosen after is the next wall's
        tab.wall_combo.setCurrentIndex(tab.wall_combo.findData("EI 90"))
        canvas.add_point((400, 400))
        canvas.add_point((500, 400))
        QTest.keyClick(canvas, Qt.Key.Key_Return)
        assert [w["id"] for w in tab.source["walls"]] == ["W1", "W2"] and tab.source["walls"][1]["class"] == "EI 90"
        canvas.add_point((400, 500))
        canvas.add_point((500, 500))
        canvas.add_point((502, 501))
        assert canvas.drawing == [] and tab.source["walls"][2]["points"] == [[400, 500], [500, 500]], "a click on the last point ends the line"
        canvas.add_point((700, 700))
        canvas.add_point((701, 700))
        assert canvas.drawing == [(700, 700)], "with one point down the line waits for its next"
        QTest.keyClick(canvas, Qt.Key.Key_Escape)
        assert canvas.drawing == [] and len(tab.source["walls"]) == 3
        # a click lands on a corner of a surface exactly, and on the end of a wall
        _draw(tab, _square(600, 100))
        tab.choose_tool("wall")
        canvas.add_point((603, 98))
        canvas.add_point((498, 399))
        assert canvas.drawing == [(600, 100), (500, 400)]
        canvas.finish_drawing()
        assert tab.source["walls"][3]["points"] == [[600, 100], [500, 400]]
        # Shift keeps a direction
        canvas.add_point((900, 800))
        canvas.add_point((1000, 803), shift=True)
        assert canvas.drawing[1] == (1000, 800)
        canvas.finish_drawing()
        assert [w["id"] for w in tab.source["walls"]] == ["W1", "W2", "W3", "W4", "W5"]
        steps = len(tab.undo_stack)
        tab.undo()
        assert [w["id"] for w in tab.source["walls"]] == ["W1", "W2", "W3", "W4"] and len(tab.undo_stack) == steps - 1
        tab.undo()
        tab.undo()
        tab.undo()
        assert [w["id"] for w in tab.source["walls"]] == ["W1", "W2"]


def test_the_route_tool_draws_an_escape_routes_length_and_it_shows_in_its_list_when_the_plan_has_a_scale():
    with _tab("fire_tab_route") as (window, tab, copied):
        _scaled(tab)
        steps = len(tab.undo_stack)
        _line(tab, "route", [(30, 30), (330, 30), (330, 330)])
        route = tab.source["routes"][0]
        assert route == {"id": "F1", "points": [[30, 30], [330, 30], [330, 330]]} and tab.canvas.selected == ["F1"]
        assert len(tab.undo_stack) == steps + 1
        # 600 sheet units at 30 to the metre
        assert fire.route_text(route, 30) == "20 m"
        row = tab.escape_tree.topLevelItem(0)
        assert [row.text(i) for i in range(4)] == ["F1", tab.t("fp_symbol_length"), "20", ""] and row.isSelected()
        assert tab.entry_tabs.currentWidget() is tab.escape_tree
        assert tab.route_box.isVisibleTo(tab) and not tab.single_box.isVisibleTo(tab) and not tab.wall_box.isVisibleTo(tab) and not tab.width_box.isVisibleTo(tab)
        assert tab.route_length_label.text() == tab.t("fp_length_value", length="20")
        assert tab.route_text_edit.text() == "" and tab.route_text_edit.placeholderText() == "20 m"
        # a text typed replaces the length written along the route: the whole of it is one step, and emptied the key goes
        steps = len(tab.undo_stack)
        tab.route_text_edit.setText("Treppe")
        tab.on_route_text()
        tab.route_text_edit.setText("Treppe 2")
        tab.on_route_text()
        assert route["text"] == "Treppe 2" and len(tab.undo_stack) == steps + 1
        assert tab.escape_tree.topLevelItem(0).text(3) == "Treppe 2"
        tab.on_zone_label_done()
        tab.route_text_edit.setText("")
        tab.on_route_text()
        assert "text" not in route
        fire.check_source(tab.source, "t")
        # a plan without a scale measures nothing: «—», and the empty placeholder
        _fresh(tab)
        _line(tab, "route", [(30, 30), (330, 30)])
        assert tab.escape_tree.topLevelItem(0).text(2) == "—"
        assert tab.route_length_label.text() == f"— ({tab.t('fp_no_scale_short')})" and tab.route_text_edit.placeholderText() == ""
        # a route of one point is no route
        steps = len(tab.undo_stack)
        _line(tab, "route", [(100, 100)])
        assert len(tab.source["routes"]) == 1 and len(tab.undo_stack) == steps


def test_changing_the_class_in_the_selection_card_changes_the_selected_walls_in_one_step():
    with _tab("fire_tab_class") as (window, tab, copied):
        _scaled(tab)
        canvas = tab.canvas
        tab.wall_combo.setCurrentIndex(tab.wall_combo.findData("EI 30"))
        _line(tab, "wall", [(100, 100), (300, 100)])
        tab.wall_combo.setCurrentIndex(tab.wall_combo.findData("EI 60"))
        _line(tab, "wall", [(100, 300), (300, 300)])
        canvas.select_ids(["W2"])
        assert tab.wall_box.isVisibleTo(tab) and not tab.several_label.isVisibleTo(tab) and not tab.single_box.isVisibleTo(tab)
        assert tab.class_combo.currentData() == "EI 60"
        assert tab.wall_length_label.text() == tab.t("fp_length_value", length="6.7"), "200 units at 30 to the metre"
        # the bar's combo is the next wall's resistance and never a wall already drawn
        steps = len(tab.undo_stack)
        tab.wall_combo.setCurrentIndex(tab.wall_combo.findData("EI 60-RF1"))
        assert [w["class"] for w in tab.source["walls"]] == ["EI 30", "EI 60"] and len(tab.undo_stack) == steps
        # one wall: its class is changed in one step
        tab.class_combo.setCurrentIndex(tab.class_combo.findData("EI 90"))
        assert [w["class"] for w in tab.source["walls"]] == ["EI 30", "EI 90"] and len(tab.undo_stack) == steps + 1
        assert tab.wall_tree.topLevelItem(1).text(1) == "EI 90"
        # two walls of two resistances show none; the one chosen is given to both, in one step
        canvas.select_ids(["W1", "W2"])
        assert tab.class_combo.currentData() is None
        assert tab.wall_length_label.text() == tab.t("fp_several_walls", count=2, length="13.3")
        steps = len(tab.undo_stack)
        tab.class_combo.setCurrentIndex(tab.class_combo.findData("EI 60-RF1"))
        assert [w["class"] for w in tab.source["walls"]] == ["EI 60-RF1", "EI 60-RF1"] and len(tab.undo_stack) == steps + 1
        assert [tab.wall_tree.topLevelItem(i).text(1) for i in range(2)] == ["EI 60-RF1", "EI 60-RF1"]
        fire.check_source(tab.source, "t")
        tab.undo()
        assert [w["class"] for w in tab.source["walls"]] == ["EI 30", "EI 90"]
        # without a scale a length is not told
        _fresh(tab)
        _line(tab, "wall", [(100, 100), (300, 100)])
        assert tab.wall_length_label.text() == f"— ({tab.t('fp_no_scale_short')})"


def test_a_click_on_a_wall_selects_the_wall_and_not_the_surface_under_it_and_a_route_comes_first():
    from PySide6.QtCore import QEvent, QPointF, Qt
    from PySide6.QtGui import QMouseEvent
    from PySide6.QtTest import QTest
    with _tab("fire_tab_hit") as (window, tab, copied):
        _fresh(tab)
        _draw(tab, _square(100, 100, 400))
        _line(tab, "wall", [(150, 300), (450, 300)])
        _line(tab, "route", [(150, 400), (450, 400)])
        canvas = tab.canvas
        canvas.centerOn(300, 300)
        tab.choose_tool("select")

        def click(x, y, modifier=Qt.KeyboardModifier.NoModifier):
            QTest.mouseClick(canvas.viewport(), Qt.MouseButton.LeftButton, modifier, canvas.mapFromScene(QPointF(x, y)))

        click(300, 304)
        assert canvas.selected == ["W1"], "the wall lies over the surface, and is what a click on it means"
        assert tab.wall_tree.topLevelItem(0).isSelected() and not tab.zone_tree.topLevelItem(0).isSelected() and tab.entry_tabs.currentWidget() is tab.wall_tree
        click(300, 250)
        assert canvas.selected == ["Z1"] and tab.entry_tabs.currentWidget() is tab.zone_tree
        click(300, 402)
        assert canvas.selected == ["F1"], "a route first"
        click(300, 250, Qt.KeyboardModifier.ControlModifier)
        assert canvas.selected == ["F1", "Z1"]
        click(300, 304, Qt.KeyboardModifier.ControlModifier)
        assert canvas.selected == ["F1", "Z1", "W1"]
        click(300, 304, Qt.KeyboardModifier.ControlModifier)
        assert canvas.selected == ["F1", "Z1"]
        # a list is a way to select too, and what it selects replaces what the others showed
        tab.wall_tree.topLevelItem(0).setSelected(True)
        assert canvas.selected == ["W1"] and not tab.zone_tree.topLevelItem(0).isSelected() and not tab.escape_tree.topLevelItem(0).isSelected()

        # the points of the focused wall are dragged, one step for a drag
        def event(kind, scene, buttons, button=Qt.MouseButton.LeftButton):
            pos = QPointF(canvas.mapFromScene(QPointF(*scene)))
            return QMouseEvent(kind, pos, canvas.viewport().mapToGlobal(pos), button, buttons, Qt.KeyboardModifier.NoModifier)

        steps = len(tab.undo_stack)
        canvas.mousePressEvent(event(QEvent.Type.MouseButtonPress, (450, 300), Qt.MouseButton.LeftButton))
        assert canvas.drag and canvas.drag["kind"] == "vertex" and canvas.drag["id"] == "W1" and canvas.drag["vertex"] == 1
        for scene in ((460, 300), (480, 300), (510, 300)):
            canvas.mouseMoveEvent(event(QEvent.Type.MouseMove, scene, Qt.MouseButton.LeftButton, Qt.MouseButton.NoButton))
        canvas.mouseReleaseEvent(event(QEvent.Type.MouseButtonRelease, (510, 300), Qt.MouseButton.NoButton))
        assert tab.source["walls"][0]["points"] == [[150, 300], [510, 300]] and len(tab.undo_stack) == steps + 1
        tab.undo()
        assert tab.source["walls"][0]["points"] == [[150, 300], [450, 300]]


# --- doors ---------------------------------------------------------------------------------------------

def test_the_door_tool_takes_three_clicks_previews_the_door_and_saves_its_kind_its_points_and_the_side_it_opens_to():
    from norms import vkf
    with _tab("fire_tab_door") as (window, tab, copied):
        _fresh(tab)
        canvas = tab.canvas
        # the bar's choices: how it opens, and its fire resistance -- none being «sans résistance»
        assert [tab.door_kind_combo.itemData(i) for i in range(tab.door_kind_combo.count())] == list(fire.DOOR_KINDS)
        assert [tab.door_class_combo.itemData(i) for i in range(tab.door_class_combo.count())] == vkf.door_classes() + [""]
        assert tab.door_class_combo.itemText(tab.door_class_combo.count() - 1) == tab.t("fp_door_plain")
        assert canvas.door_kind == "swing" and canvas.door_class == "EI 30"
        assert tab.tool_buttons["door"].toolTip() == tab.t("fp_hint_door")
        steps = len(tab.undo_stack)
        tab.choose_tool("door")
        assert tab.hint.text() == tab.t("fp_hint_door")
        canvas.add_point((100, 100))
        canvas.add_point((190, 100))
        assert canvas.drawing == [(100, 100), (190, 100)] and "doors" not in tab.source and len(tab.undo_stack) == steps, "two clicks are not a door yet"
        # between the second click and the third the door follows the pointer: the side the pointer is on is the side it opens to
        canvas.cursor = (150, 160)
        canvas.update_helpers()
        assert canvas.preview_shape() == fire.door_shape({"kind": "swing", "points": [[100, 100], [190, 100]], "side": 1})
        below = canvas.preview.path().boundingRect()
        assert below.bottom() > 100 + 80 and below.top() <= 100 + 1, "a quarter disc under the line"
        canvas.cursor = (150, 40)
        canvas.update_helpers()
        assert canvas.preview_shape() == fire.door_shape({"kind": "swing", "points": [[100, 100], [190, 100]], "side": -1})
        above = canvas.preview.path().boundingRect()
        assert above.top() < 100 - 80 and above.bottom() >= 100 - 1, "and above it when the pointer is"
        canvas.add_point((150, 160))
        assert tab.source["doors"] == [{"id": "T1", "kind": "swing", "class": "EI 30", "points": [[100, 100], [190, 100]], "side": 1}]
        assert canvas.selected == ["T1"] and canvas.drawing == [] and len(tab.undo_stack) == steps + 1 and tab.dirty
        assert len(canvas.handles) == 2, "a door has its two points to drag"
        fire.check_source(tab.source, "t")
        # a sliding door without a fire resistance, opening upwards: no `class` at all
        tab.door_kind_combo.setCurrentIndex(tab.door_kind_combo.findData("slide"))
        tab.door_class_combo.setCurrentIndex(tab.door_class_combo.findData(""))
        assert canvas.door_kind == "slide" and canvas.door_class is None
        assert tab.source["doors"][0]["kind"] == "swing" and tab.source["doors"][0]["class"] == "EI 30", "the bar's combos are the next door's and never one already drawn"
        _door(tab, (300, 300), (390, 300), (350, 250))
        plain = tab.source["doors"][1]
        assert plain == {"id": "T2", "kind": "slide", "points": [[300, 300], [390, 300]], "side": -1} and "class" not in plain
        # a swinging door of the other class
        tab.door_kind_combo.setCurrentIndex(tab.door_kind_combo.findData("swing"))
        tab.door_class_combo.setCurrentIndex(tab.door_class_combo.findData("E 30"))
        _door(tab, (500, 500), (500, 590), (550, 540))
        e30 = tab.source["doors"][2]
        assert e30["kind"] == "swing" and e30["class"] == "E 30" and e30["side"] in (1, -1)
        assert e30["side"] == fire.side_of(e30["points"][0], e30["points"][1], (550, 540)), "the side is the third click's"
        fire.check_source(tab.source, "t")
        # one step each, and an undo takes the door and the selection away
        steps = len(tab.undo_stack)
        tab.undo()
        assert [d["id"] for d in tab.source["doors"]] == ["T1", "T2"] and len(tab.undo_stack) == steps - 1 and canvas.selected == []


def test_a_door_waits_for_its_clicks_is_given_up_with_escape_and_keeps_to_a_direction_with_shift_and_snaps_to_a_wall():
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest
    with _tab("fire_tab_door_clicks") as (window, tab, copied):
        _fresh(tab)
        canvas = tab.canvas
        _line(tab, "wall", [(100, 100), (300, 100)])
        tab.choose_tool("door")
        steps = len(tab.undo_stack)
        # the same point twice is no second point
        canvas.add_point((500, 500))
        canvas.add_point((501, 501))
        assert canvas.drawing == [(500, 500)]
        # Shift keeps the jamb on one of the eight directions from the hinge
        canvas.add_point((590, 504), shift=True)
        assert canvas.drawing[1] == (590, 500)
        # Backspace takes the last click off, Escape gives the door up
        QTest.keyClick(canvas, Qt.Key.Key_Backspace)
        assert canvas.drawing == [(500, 500)]
        QTest.keyClick(canvas, Qt.Key.Key_Escape)
        assert canvas.drawing == [] and "doors" not in tab.source and len(tab.undo_stack) == steps
        # Enter before the door is whole gives it up, too
        canvas.add_point((500, 500))
        canvas.add_point((590, 500))
        QTest.keyClick(canvas, Qt.Key.Key_Return)
        assert canvas.drawing == [] and "doors" not in tab.source
        # a hinge and a jamb land on the end of a wall exactly; the third click is where it is
        canvas.add_point((98, 102))
        canvas.add_point((299, 99))
        assert canvas.drawing == [(100, 100), (300, 100)]
        canvas.add_point((201, 101))
        door = tab.source["doors"][0]
        assert door["points"] == [[100, 100], [300, 100]] and door["side"] in (1, -1)
        # a click on the line itself is no side to choose: the first
        canvas.add_point((400, 400))
        canvas.add_point((480, 400))
        canvas.add_point((440, 400))
        assert tab.source["doors"][1]["side"] == 1


def test_a_door_is_drawn_with_the_mouse_in_three_clicks_and_the_preview_follows_the_pointer():
    from PySide6.QtCore import Qt
    with _tab("fire_tab_door_mouse") as (window, tab, copied):
        _fresh(tab)
        canvas = tab.canvas
        canvas.centerOn(150, 120)
        tab.choose_tool("door")
        event, QEvent = _events(canvas)

        def click(x, y):
            canvas.mousePressEvent(event(QEvent.Type.MouseButtonPress, (x, y), Qt.MouseButton.LeftButton))
            canvas.mouseReleaseEvent(event(QEvent.Type.MouseButtonRelease, (x, y), Qt.MouseButton.NoButton))

        click(100, 100)
        click(190, 100)
        assert len(canvas.drawing) == 2 and "doors" not in tab.source
        canvas.mouseMoveEvent(event(QEvent.Type.MouseMove, (150, 170), Qt.MouseButton.NoButton, Qt.MouseButton.NoButton))
        assert abs(canvas.cursor[0] - 150) < 1.5 and abs(canvas.cursor[1] - 170) < 1.5, "the third click is not snapped: the pointer is where the side is chosen"
        assert canvas.preview_shape() is not None and not canvas.preview.path().isEmpty()
        click(150, 170)
        door = tab.source["doors"][0]
        assert door["side"] == 1 and abs(door["points"][0][0] - 100) < 1.5 and abs(door["points"][1][0] - 190) < 1.5
        assert canvas.drawing == [] and canvas.preview_shape() is None and canvas.selected == ["T1"]
        # a quick second click arrives as a double-click and is not lost
        for x, y in ((300, 300), (390, 300)):
            canvas.mousePressEvent(event(QEvent.Type.MouseButtonPress, (x, y), Qt.MouseButton.LeftButton))
        canvas.mouseDoubleClickEvent(event(QEvent.Type.MouseButtonDblClick, (350, 360), Qt.MouseButton.LeftButton))
        assert len(tab.source["doors"]) == 2 and tab.source["doors"][1]["side"] == 1


def test_the_card_of_a_door_changes_its_kind_and_its_fire_resistance_for_all_selected_in_one_step():
    with _tab("fire_tab_door_card") as (window, tab, copied):
        _scaled(tab)
        canvas = tab.canvas
        _door(tab, (100, 100), (127, 100), (110, 150))   # 27 units: 0.9 m
        _door(tab, (300, 100), (330, 100), (310, 50))    # 30 units: 1 m
        tab.choose_tool("select")
        first, second = tab.source["doors"]
        canvas.select_ids(["T1"])
        assert tab.door_box.isVisibleTo(tab) and not tab.zone_box.isVisibleTo(tab) and not tab.wall_box.isVisibleTo(tab) and not tab.several_label.isVisibleTo(tab)
        assert tab.door_kind_card_combo.currentData() == "swing" and tab.door_class_card_combo.currentData() == "EI 30"
        assert tab.door_width_label.text() == tab.t("fp_width_value", width="0.9")
        # the fire resistance: another, then none -- the key goes --, then the kind: each one step
        steps = len(tab.undo_stack)
        tab.door_class_card_combo.setCurrentIndex(tab.door_class_card_combo.findData("E 30"))
        assert first["class"] == "E 30" and len(tab.undo_stack) == steps + 1
        tab.door_class_card_combo.setCurrentIndex(tab.door_class_card_combo.findData(""))
        assert "class" not in first and len(tab.undo_stack) == steps + 2
        assert tab.door_tree.topLevelItem(0).text(2) == tab.t("fp_door_plain")
        tab.door_kind_card_combo.setCurrentIndex(tab.door_kind_card_combo.findData("slide"))
        assert first["kind"] == "slide" and len(tab.undo_stack) == steps + 3 and tab.door_tree.topLevelItem(0).text(1) == tab.t("fp_door_slide")
        fire.check_source(tab.source, "t")
        # two doors that differ show none, and the width is not one number; the choice made is given to both, in one step
        canvas.select_ids(["T1", "T2"])
        assert tab.door_kind_card_combo.currentIndex() == -1 and tab.door_class_card_combo.currentIndex() == -1
        assert tab.door_width_label.text() == "—"
        steps = len(tab.undo_stack)
        tab.door_kind_card_combo.setCurrentIndex(tab.door_kind_card_combo.findData("swing"))
        assert [d["kind"] for d in tab.source["doors"]] == ["swing", "swing"] and len(tab.undo_stack) == steps + 1
        tab.door_class_card_combo.setCurrentIndex(tab.door_class_card_combo.findData("E 30"))
        assert [d.get("class") for d in tab.source["doors"]] == ["E 30", "E 30"] and len(tab.undo_stack) == steps + 2
        assert tab.door_kind_card_combo.currentData() == "swing", "they share a kind now: the combo shows it"
        tab.undo()
        assert [d.get("class") for d in tab.source["doors"]] == [None, "EI 30"]
        # without a scale a width is not told
        _fresh(tab)
        _door(tab, (100, 100), (127, 100), (110, 150))
        assert tab.door_width_label.text() == f"— ({tab.t('fp_no_scale_short')})" and tab.door_tree.topLevelItem(0).text(3) == "—"


def test_the_two_flips_turn_the_hinge_and_the_side_of_every_door_selected_in_one_step_and_keep_the_selection():
    import copy
    with _tab("fire_tab_flip") as (window, tab, copied):
        _fresh(tab)
        canvas = tab.canvas
        _door(tab, (100, 100), (190, 100), (150, 160))          # opens down
        tab.door_kind_combo.setCurrentIndex(tab.door_kind_combo.findData("slide"))
        _door(tab, (300, 300), (390, 300), (350, 250))          # slides, opens up
        tab.choose_tool("select")
        before = copy.deepcopy(tab.source["doors"])
        canvas.select_ids(["T1", "T2"])
        assert tab.flip_hinge_button.isVisibleTo(tab) and tab.flip_side_button.isVisibleTo(tab)
        assert tab.flip_hinge_button.toolTip() == tab.t("fp_flip_hinge_tip") and tab.flip_side_button.toolTip() == tab.t("fp_flip_side_tip")
        first, second = tab.source["doors"]
        steps = len(tab.undo_stack)
        tab.flip_hinge_button.click()
        for door, was in zip(tab.source["doors"], before):
            assert door["points"] == [was["points"][1], was["points"][0]], "the hinge is on the other jamb"
            assert door["side"] == -was["side"], "the count of the side turns with the line: the same side of the wall"
            assert door["id"] == was["id"] and door["kind"] == was["kind"] and door.get("class") == was.get("class")
        assert tab.source["doors"][0] is first and tab.source["doors"][1] is second, "the entries are changed in place"
        assert canvas.selected == ["T1", "T2"] and len(tab.undo_stack) == steps + 1, "both doors in one step, and the selection is kept"
        # the shape really is the other way: the quarter disc of the flipped door starts from the other jamb and stays on the same side of the wall
        shape = fire.door_shape(first)
        assert list(shape[0]) == before[0]["points"][1], "the hinge is where the jamb was"
        assert shape[-1][1] > 100, "and the leaf still opens down, to the side of the wall it opened to"
        fire.check_source(tab.source, "t")
        # flipping twice is giving it back
        tab.flip_hinge_button.click()
        assert tab.source["doors"] == before and len(tab.undo_stack) == steps + 2
        # the side alone: the hinge stays where it is
        tab.flip_side_button.click()
        for door, was in zip(tab.source["doors"], before):
            assert door["points"] == was["points"] and door["side"] == -was["side"]
        assert len(tab.undo_stack) == steps + 3 and canvas.selected == ["T1", "T2"]
        tab.undo()
        assert tab.source["doors"] == before
        # one door of the two
        canvas.select_ids(["T2"])
        tab.flip_side_button.click()
        assert tab.source["doors"][0] == before[0] and tab.source["doors"][1]["side"] == -before[1]["side"]
        # nothing selected, nothing flipped
        canvas.select_ids([])
        steps = len(tab.undo_stack)
        tab.flip_doors("hinge")
        assert len(tab.undo_stack) == steps


# --- emergency exits and widths -----------------------------------------------------------------------

def test_the_exit_tool_takes_two_clicks_previews_the_arrow_and_its_points_are_dragged():
    with _tab("fire_tab_exit") as (window, tab, copied):
        _fresh(tab)
        canvas = tab.canvas
        steps = len(tab.undo_stack)
        tab.choose_tool("exit")
        assert tab.hint.text() == tab.t("fp_hint_exit")
        canvas.add_point((100, 100))
        assert canvas.drawing == [(100, 100)] and canvas.preview_shape() is None, "the pointer has not moved yet: nothing to preview"
        canvas.cursor = (220, 100)
        canvas.update_helpers()
        assert canvas.preview_shape() == fire.exit_shape([[100, 100], [220, 100]]) and canvas.preview.path().elementCount() >= 7
        canvas.add_point((100.5, 100.5))
        assert canvas.drawing == [(100, 100)], "the tail's own point is no tip"
        canvas.add_point((220, 100))
        assert tab.source["exits"] == [{"id": "N1", "points": [[100, 100], [220, 100]]}]
        assert canvas.selected == ["N1"] and canvas.drawing == [] and len(tab.undo_stack) == steps + 1
        assert len(canvas.handles) == 2
        fire.check_source(tab.source, "t")
        row = tab.escape_tree.topLevelItem(0)
        assert [row.text(i) for i in range(4)] == ["N1", tab.t("fp_symbol_exit"), "", ""] and row.isSelected() and tab.entry_tabs.currentWidget() is tab.escape_tree
        # it has no card of its own: the count is told
        assert tab.several_label.isVisibleTo(tab) and tab.several_label.text() == tab.t("fp_mixed", count=1, detail=tab.t("fp_kind_exits", n=1))
        # the outline round it is the arrow's shape
        shape = fire.exit_shape([[100, 100], [220, 100]])
        rect = canvas.select_item.path().boundingRect()
        assert abs(rect.left() - min(x for x, _y in shape)) < 1e-6 and abs(rect.right() - max(x for x, _y in shape)) < 1e-6
        # its tip is dragged: one step
        tab.choose_tool("select")
        steps = len(tab.undo_stack)
        _drag(canvas, (220, 100), ((230, 100), (260, 100)))
        tip = tab.source["exits"][0]["points"][1]
        assert abs(tip[0] - 260) < 1.5 and abs(tip[1] - 100) < 1.5 and len(tab.undo_stack) == steps + 1
        tab.undo()
        assert tab.source["exits"][0]["points"] == [[100, 100], [220, 100]]


def test_the_width_tool_takes_two_clicks_and_its_text_replaces_the_measured_width_when_typed():
    with _tab("fire_tab_width") as (window, tab, copied):
        _scaled(tab)
        canvas = tab.canvas
        steps = len(tab.undo_stack)
        tab.choose_tool("width")
        assert tab.hint.text() == tab.t("fp_hint_width")
        canvas.add_point((100, 100))
        assert canvas.drawing == [(100, 100)]
        canvas.add_point((136, 100))
        width = tab.source["widths"][0]
        assert width == {"id": "B1", "points": [[100, 100], [136, 100]]} and canvas.selected == ["B1"] and len(tab.undo_stack) == steps + 1
        fire.check_source(tab.source, "t")
        # 36 sheet units at 30 to the metre
        assert fire.width_text(width, 30) == "1.20 m"
        row = tab.escape_tree.topLevelItem(0)
        assert [row.text(i) for i in range(4)] == ["B1", tab.t("fp_symbol_width"), "1.2", ""] and row.isSelected()
        assert tab.width_box.isVisibleTo(tab) and not tab.route_box.isVisibleTo(tab) and not tab.several_label.isVisibleTo(tab)
        assert tab.width_label.text() == tab.t("fp_width_value", width="1.2")
        assert tab.width_text_edit.text() == "" and tab.width_text_edit.placeholderText() == "1.20 m"
        # a text typed replaces the width written on the line: the whole of it is one step, and emptied the key goes
        steps = len(tab.undo_stack)
        tab.width_text_edit.setText("Min")
        tab.on_width_text()
        tab.width_text_edit.setText("Min. 1.20 m")
        tab.on_width_text()
        assert width["text"] == "Min. 1.20 m" and len(tab.undo_stack) == steps + 1
        assert tab.escape_tree.topLevelItem(0).text(3) == "Min. 1.20 m"
        tab.on_zone_label_done()
        tab.width_text_edit.setText("")
        tab.on_width_text()
        assert "text" not in width
        fire.check_source(tab.source, "t")
        # a plan without a scale measures nothing: «—», and an empty placeholder
        _fresh(tab)
        tab.choose_tool("width")
        canvas.add_point((100, 100))
        canvas.add_point((136, 100))
        assert tab.escape_tree.topLevelItem(0).text(2) == "—"
        assert tab.width_label.text() == f"— ({tab.t('fp_no_scale_short')})" and tab.width_text_edit.placeholderText() == ""


def test_a_mixed_selection_is_told_by_its_count_and_delete_removes_all_six_kinds_in_one_step():
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest
    with _tab("fire_tab_mixed") as (window, tab, copied):
        _fresh(tab)
        canvas = tab.canvas
        _draw(tab, _square(100, 100))
        _line(tab, "wall", [(400, 100), (600, 100)])
        _door(tab, (400, 200), (490, 200), (440, 240))
        _line(tab, "route", [(400, 300), (600, 300)])
        tab.choose_tool("exit")
        canvas.add_point((400, 400))
        canvas.add_point((480, 400))
        tab.choose_tool("width")
        canvas.add_point((400, 500))
        canvas.add_point((436, 500))
        ids = ["Z1", "W1", "T1", "F1", "N1", "B1"]
        assert [entry["id"] for collection in fire.COLLECTIONS for entry in tab.source[collection]].count("Z1") == 1
        canvas.select_ids(ids)
        detail = ", ".join(tab.t(f"fp_kind_{c}", n=1) for c in ("zones", "walls", "doors", "routes", "exits", "widths"))
        assert tab.several_label.isVisibleTo(tab) and tab.several_label.text() == tab.t("fp_mixed", count=6, detail=detail)
        assert not tab.door_box.isVisibleTo(tab) and not tab.wall_box.isVisibleTo(tab) and not tab.zone_box.isVisibleTo(tab)
        assert tab.delete_selection_button.isEnabled()
        assert all(tree.selectedItems() for tree in tab.tree_list), "every list marks its own share"
        steps = len(tab.undo_stack)
        QTest.keyClick(canvas, Qt.Key.Key_Delete)
        assert all(tab.source[collection] == [] for collection in fire.COLLECTIONS) and canvas.selected == []
        assert len(tab.undo_stack) == steps + 1, "six entries of six kinds went in one step of «Annuler»"
        assert all(tree.topLevelItemCount() == 0 for tree in tab.tree_list)
        assert not tab.delete_selection_button.isEnabled() and tab.delete_selection_button.toolTip() == tab.t("fp_nothing_selected")
        assert not tab.delete_button.isEnabled() and tab.delete_button.toolTip() == tab.t("fp_nothing_selected")
        tab.undo()
        assert [len(tab.source[collection]) for collection in ("zones", "walls", "doors", "routes", "exits", "widths")] == [1] * 6


# --- the legend ---------------------------------------------------------------------------------------

def test_the_legend_is_a_check_box_that_puts_a_box_on_the_plan_and_undo_follows_it():
    from domains import fire_svg
    with _tab("fire_tab_legend") as (window, tab, copied):
        _fresh(tab)
        assert not tab.legend_check.isChecked() and "legend" not in tab.source
        assert fire_svg.legend_box(tab.source, tab.frame(), tab.app.lang) is None, "a plan without a legend has no box"
        steps = len(tab.undo_stack)
        tab.legend_check.setChecked(True)
        assert tab.source["legend"] == fire.legend_default(tab.frame()) and len(tab.undo_stack) == steps + 1 and tab.dirty
        assert fire_svg.legend_box(tab.source, tab.frame(), tab.app.lang) is not None
        fire.check_source(tab.source, "t")
        tab.undo()
        assert "legend" not in tab.source and not tab.legend_check.isChecked(), "the box follows the source when a step is undone"
        tab.redo()
        assert "legend" in tab.source and tab.legend_check.isChecked()
        steps = len(tab.undo_stack)
        tab.legend_check.setChecked(False)
        assert "legend" not in tab.source and len(tab.undo_stack) == steps + 1
        tab.undo()
        assert tab.source["legend"] == fire.legend_default(tab.frame()) and tab.legend_check.isChecked()
        # it follows the source when a plan is loaded, too
        tab.open_source(fire.new_source("Other"), None, False)
        assert not tab.legend_check.isChecked()
        source = fire.new_source("With")
        source["legend"] = {"x": 20.0, "y": 30.0}
        tab.open_source(source, None, False)
        assert tab.legend_check.isChecked()


def test_a_press_in_the_legend_drags_it_before_anything_under_it_is_hit_in_one_step_and_it_is_no_entry():
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest
    from domains import fire_svg
    with _tab("fire_tab_legend_drag") as (window, tab, copied):
        _fresh(tab)
        canvas = tab.canvas
        tab.legend_check.setChecked(True)
        x, y, w, h = fire_svg.legend_box(tab.source, tab.frame(), tab.app.lang)
        # a surface lying under the legend, and a wall: a press in the box is the legend's
        _draw(tab, [(x + 5, y + 5), (x + w, y + 5), (x + w, y + h)])
        spot = (x + w - 10, y + 15)
        assert canvas.legend_under(spot), "the box has only grown, with the row the surface gave it"
        assert fire.hit(tab.source, spot, canvas.tolerance()) == "Z1", "the surface is what lies under the spot, and the legend is drawn over it"
        canvas.select_ids([])
        tab.choose_tool("select")
        steps = len(tab.undo_stack)
        # a press that does not move leaves no step and selects nothing
        _drag(canvas, spot, (spot,))
        assert canvas.selected == [] and len(tab.undo_stack) == steps and tab.source["legend"] == fire.legend_default(tab.frame())
        start = tab.source["legend"]["x"], tab.source["legend"]["y"]
        event, QEvent = _events(canvas)
        canvas.mousePressEvent(event(QEvent.Type.MouseButtonPress, spot, Qt.MouseButton.LeftButton))
        assert canvas.drag and canvas.drag["kind"] == "legend" and canvas.selected == [], "the legend is taken, the surface under it is not"
        for i in range(1, 6):
            canvas.mouseMoveEvent(event(QEvent.Type.MouseMove, (spot[0] + 10 * i, spot[1] + 6 * i), Qt.MouseButton.LeftButton, Qt.MouseButton.NoButton))
        canvas.mouseReleaseEvent(event(QEvent.Type.MouseButtonRelease, (spot[0] + 50, spot[1] + 30), Qt.MouseButton.NoButton))
        legend = tab.source["legend"]
        assert abs(legend["x"] - (start[0] + 50)) < 1.5 and abs(legend["y"] - (start[1] + 30)) < 1.5, (start, legend)
        assert legend["x"] == round(legend["x"], 2) and legend["y"] == round(legend["y"], 2), "to a hundredth of a sheet unit"
        assert len(tab.undo_stack) == steps + 1, "the whole drag is one step"
        assert tab.dirty and canvas.selected == [] and canvas.drag is None
        fire.check_source(tab.source, "t")
        # the box is where it was dropped
        box = fire_svg.legend_box(tab.source, tab.frame(), tab.app.lang)
        assert abs(box[0] - (x + 50)) < 1.5
        tab.undo()
        assert (tab.source["legend"]["x"], tab.source["legend"]["y"]) == start
        # it is no entry: not selectable, and Delete takes nothing of it
        QTest.keyClick(canvas, Qt.Key.Key_Delete)
        assert "legend" in tab.source
        canvas.select_ids(["Z1"])
        QTest.keyClick(canvas, Qt.Key.Key_Delete)
        assert tab.source["zones"] == [] and "legend" in tab.source
        # once moved away, what it covered can be selected again
        tab.undo()
        _drag(canvas, spot, ((spot[0] + 200, spot[1] + 200),))
        canvas.select_ids([])
        new = fire_svg.legend_box(tab.source, tab.frame(), tab.app.lang)
        assert not (new[0] <= spot[0] <= new[0] + new[2] and new[1] <= spot[1] <= new[1] + new[3])
        event, QEvent = _events(canvas)
        canvas.mousePressEvent(event(QEvent.Type.MouseButtonPress, spot, Qt.MouseButton.LeftButton))
        canvas.mouseReleaseEvent(event(QEvent.Type.MouseButtonRelease, spot, Qt.MouseButton.NoButton))
        assert canvas.selected == ["Z1"]


def test_the_legend_is_written_in_the_windows_language_and_the_canvas_hands_it_to_the_drawing():
    from domains import fire_svg
    with _tab("fire_tab_lang") as (window, tab, copied):
        assert tab.canvas.lang == tab.app.lang
        seen = []
        real = fire_svg.render
        fire_svg.render = lambda *a, **k: (seen.append(k.get("lang")), real(*a, **k))[1]
        try:
            tab.canvas.lang = "en"
            tab.canvas.redraw()
            assert seen[-1] == "en"
            tab.canvas.lang = "fr"
            tab.canvas.redraw()
            assert seen[-1] == "fr"
        finally:
            fire_svg.render = real
        # and the box is sized for the words it is written in
        _fresh(tab)
        tab.legend_check.setChecked(True)
        _line(tab, "route", [(30, 30), (330, 30)])
        widths = {}
        for lang in ("de", "fr", "en"):
            widths[lang] = fire_svg.legend_box(tab.source, tab.frame(), lang)[2]
        assert len(set(widths.values())) > 1, widths


# --- a drag does not stutter --------------------------------------------------------------------------

def test_a_drag_renders_the_overlay_at_most_every_half_second_while_the_outline_and_the_handles_follow_at_once():
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest
    _qt()   # calc/tools on the path before its import, whatever part of the file this test runs in (issue #24)
    import fire_canvas
    from domains import fire_svg
    with _tab("fire_tab_throttle") as (window, tab, copied):
        _fresh(tab)
        canvas = tab.canvas
        _draw(tab, _square(100, 100))
        tab.choose_tool("select")
        assert fire_canvas.DRAG_REDRAW_MS == 500 and canvas.drag_timer.interval() == 500 and canvas.drag_timer.isSingleShot()
        counts = {"redraw": 0, "helpers": 0}
        real_redraw, real_helpers = canvas.redraw, canvas.update_helpers

        def redraw():
            counts["redraw"] += 1
            real_redraw()

        def helpers():
            counts["helpers"] += 1
            real_helpers()

        canvas.redraw, canvas.update_helpers = redraw, helpers
        try:
            event, QEvent = _events(canvas)
            steps = len(tab.undo_stack)
            canvas.mousePressEvent(event(QEvent.Type.MouseButtonPress, (100, 100), Qt.MouseButton.LeftButton))
            assert canvas.drag and canvas.drag["kind"] == "vertex"
            before = counts["helpers"]
            for i in range(1, 11):
                canvas.mouseMoveEvent(event(QEvent.Type.MouseMove, (100 - 4 * i, 100 - 3 * i), Qt.MouseButton.LeftButton, Qt.MouseButton.NoButton))
                point = tab.source["zones"][0]["points"][0]
                assert (canvas.handles[0].pos().x(), canvas.handles[0].pos().y()) == (point[0], point[1]), "the handle is on the point at every movement"
            assert counts["helpers"] - before >= 10, "the outline and the handles are drawn at every movement"
            assert counts["redraw"] == 0, "the overlay -- every length and area measured again -- is not rendered at every movement"
            assert canvas.drag_timer.isActive()
            # half a second later it is rendered once, as the source then is
            QTest.qWait(fire_canvas.DRAG_REDRAW_MS + 150)
            assert counts["redraw"] == 1 and not canvas.drag_timer.isActive()
            for i in range(11, 16):
                canvas.mouseMoveEvent(event(QEvent.Type.MouseMove, (100 - 4 * i, 100 - 3 * i), Qt.MouseButton.LeftButton, Qt.MouseButton.NoButton))
            assert counts["redraw"] == 1 and canvas.drag_timer.isActive(), "the next render waits for its half second, too"
            # the button let go: the final state is drawn at once, and no render is left waiting
            canvas.mouseReleaseEvent(event(QEvent.Type.MouseButtonRelease, (40, 55), Qt.MouseButton.NoButton))
            assert counts["redraw"] == 2 and not canvas.drag_timer.isActive()
            moved = tab.source["zones"][0]["points"][0]
            assert len(tab.undo_stack) == steps + 1 and abs(moved[0] - 40) < 1.5 and abs(moved[1] - 55) < 1.5
            QTest.qWait(fire_canvas.DRAG_REDRAW_MS + 150)
            assert counts["redraw"] == 2, "nothing is rendered a third time"
            # the legend, dragged, is rendered the same way
            tab.legend_check.setChecked(True)
            x, y, w, h = fire_svg.legend_box(tab.source, tab.frame(), tab.app.lang)
            canvas.select_ids([])
            counts["redraw"] = 0
            spot = (x + w / 2, y + h / 2)
            canvas.mousePressEvent(event(QEvent.Type.MouseButtonPress, spot, Qt.MouseButton.LeftButton))
            assert canvas.drag["kind"] == "legend"
            for i in range(1, 9):
                canvas.mouseMoveEvent(event(QEvent.Type.MouseMove, (spot[0] + 5 * i, spot[1] + 5 * i), Qt.MouseButton.LeftButton, Qt.MouseButton.NoButton))
            assert counts["redraw"] == 0 and canvas.drag_timer.isActive()
            assert not canvas.preview.path().isEmpty(), "the legend's outline follows the pointer while the overlay waits"
            canvas.mouseReleaseEvent(event(QEvent.Type.MouseButtonRelease, (spot[0] + 40, spot[1] + 40), Qt.MouseButton.NoButton))
            assert counts["redraw"] == 1 and not canvas.drag_timer.isActive()
        finally:
            del canvas.redraw
            del canvas.update_helpers


# --- the lists ----------------------------------------------------------------------------------------

def test_the_four_lists_show_what_the_source_holds_and_follow_the_selection_both_ways():
    from i18n import strings
    from norms import vkf
    with _tab("fire_tab_lists") as (window, tab, copied):
        _scaled(tab)
        canvas = tab.canvas
        tab.surface_combo.setCurrentIndex(tab.surface_combo.findData("vertical"))
        _draw(tab, _square(100, 100, 150))                 # 5 m by 5 m
        tab.wall_combo.setCurrentIndex(tab.wall_combo.findData("EI 90"))
        _line(tab, "wall", [(400, 100), (700, 100)])       # 10 m
        _line(tab, "wall", [(400, 200), (700, 200)])
        _door(tab, (400, 300), (427, 300), (410, 350))     # 0.9 m, swing, EI 30
        tab.door_kind_combo.setCurrentIndex(tab.door_kind_combo.findData("slide"))
        tab.door_class_combo.setCurrentIndex(tab.door_class_combo.findData(""))
        _door(tab, (500, 300), (530, 300), (510, 250))     # 1 m, sliding, none
        _line(tab, "route", [(30, 500), (330, 500), (330, 800)])   # 20 m
        tab.choose_tool("exit")
        canvas.add_point((400, 500))
        canvas.add_point((480, 500))
        tab.choose_tool("width")
        canvas.add_point((400, 600))
        canvas.add_point((436, 600))
        tab.width_text_edit.setText("Min. 1.20 m")
        tab.on_width_text()
        assert [tab.entry_tabs.tabText(i) for i in range(tab.entry_tabs.count())] == [tab.t(key) for key in ("fp_zones", "fp_walls", "fp_doors", "fp_escape")]
        assert [tree.topLevelItemCount() for tree in tab.tree_list] == [1, 2, 2, 3]
        assert [tab.zone_tree.headerItem().text(i) for i in range(4)] == [tab.t(k) for k in ("fp_col_id", "fp_col_kind", "fp_col_name", "fp_col_area")]
        assert [tab.door_tree.headerItem().text(i) for i in range(4)] == [tab.t(k) for k in ("fp_col_id", "fp_col_kind", "fp_col_class", "fp_col_width")]
        assert [tab.escape_tree.headerItem().text(i) for i in range(4)] == [tab.t(k) for k in ("fp_col_id", "fp_col_symbol", "fp_col_value", "fp_col_text")]

        def rows(tree):
            return [[tree.topLevelItem(r).text(c) for c in range(tree.columnCount())] for r in range(tree.topLevelItemCount())]

        assert rows(tab.zone_tree) == [["Z1", strings.term(vkf.escape("vertical")["label"], tab.app.lang), "", "25"]]
        assert rows(tab.wall_tree) == [["W1", "EI 90", "10"], ["W2", "EI 90", "10"]]
        assert rows(tab.door_tree) == [["T1", tab.t("fp_door_swing"), "EI 30", "0.9"], ["T2", tab.t("fp_door_slide"), tab.t("fp_door_plain"), "1"]]
        assert rows(tab.escape_tree) == [["F1", tab.t("fp_symbol_length"), "20", ""], ["N1", tab.t("fp_symbol_exit"), "", ""],
                                         ["B1", tab.t("fp_symbol_width"), "1.2", "Min. 1.20 m"]]
        # a selection on the plan marks the rows and brings the list of the entry in focus to the front
        canvas.select_ids(["T2"])
        assert tab.door_tree.topLevelItem(1).isSelected() and not tab.door_tree.topLevelItem(0).isSelected() and tab.entry_tabs.currentWidget() is tab.door_tree
        canvas.select_ids(["N1", "Z1"])
        assert tab.escape_tree.topLevelItem(1).isSelected() and tab.zone_tree.topLevelItem(0).isSelected() and not tab.wall_tree.selectedItems()
        assert tab.entry_tabs.currentWidget() is tab.zone_tree
        canvas.select_ids(["Z1", "B1"])
        assert tab.entry_tabs.currentWidget() is tab.escape_tree
        # and a row selects on the plan, replacing what the other lists showed
        tab.door_tree.topLevelItem(0).setSelected(True)
        assert canvas.selected == ["T1"] and not tab.zone_tree.selectedItems() and not tab.escape_tree.selectedItems()
        tab.escape_tree.topLevelItem(2).setSelected(True)
        assert canvas.selected == ["B1"] and not tab.door_tree.selectedItems()
        # without a scale every measure is «—»
        _fresh(tab)
        _draw(tab, _square(100, 100))
        _door(tab, (400, 300), (427, 300), (410, 350))
        _line(tab, "route", [(30, 500), (330, 500)])
        tab.choose_tool("width")
        canvas.add_point((400, 600))
        canvas.add_point((436, 600))
        assert tab.zone_tree.topLevelItem(0).text(3) == "—" and tab.door_tree.topLevelItem(0).text(3) == "—"
        assert [tab.escape_tree.topLevelItem(i).text(2) for i in range(2)] == ["—", "—"]


# --- saving -------------------------------------------------------------------------------------------

def test_a_plan_is_saved_as_its_source_duplicated_and_archived_and_exported_each_time():
    if TOOLS not in sys.path:   # first of its part when the runner splits this file (run_tests.py): calc/tools/ is not on the path yet
        sys.path.insert(0, TOOLS)
    import source_archive
    with _tab("fire_tab_save") as (window, tab, copied):
        folder = copied.fire_dir
        tab.open_source(fire.new_source("B07", "Pavillon"), None, True)
        tab.reload_list(select=None)
        assert tab.save()
        assert fire.read_source(folder / "B07.json")["plan"] == "Pavillon"
        assert tab.current_id == "B07" and not tab.dirty
        exported = json.loads((copied.data_dir / "fire.json").read_text(encoding="utf-8"))
        assert list(exported["plans"]) == ["B07"], "saving exports the fire-protection plans at once"
        # a name typed on a surface, then saved
        tab.canvas.resetTransform()
        _draw(tab, _square(100, 100))
        tab.zone_label.setText("Treppenhaus")
        tab.on_zone_label()
        assert tab.save()
        saved = fire.read_source(folder / "B07.json")
        assert saved["zones"][0]["label"] == "Treppenhaus" and saved["zones"][0]["kind"] == "horizontal" and saved["schema_version"] == fire.SOURCE_SCHEMA_VERSION
        # a duplicate is another plan, with the next free id
        tab.duplicate()
        assert tab.source["id"] == "B01" and tab.current_id is None and tab.dirty
        assert [row for row in tab.list.ids() if row == "<new>"], "the draft is listed"
        assert tab.save()
        assert fire.read_source(folder / "B01.json")["zones"][0]["label"] == "Treppenhaus"
        # an id taken is refused, whatever its case
        tab.duplicate()
        tab.id_edit.setText("b07")
        assert tab.source["id"] == "b07" and not tab.save()
        assert sorted(p.name for p in folder.glob("*.json")) == ["B01.json", "B07.json"]
        tab.dirty = False
        tab.load("B07")
        tab.reload_list("B07")
        tab.delete()
        assert not (folder / "B07.json").exists(), "«Supprimer» takes the plan out of the folder the export reads"
        archived = list(source_archive.folder(folder).glob("*.json"))
        assert len(archived) == 1 and "id" not in json.loads(archived[0].read_text(encoding="utf-8")), "archived with its id removed"
        assert [p.name for p in folder.glob("*.json")] == ["B01.json"]
        again = json.loads((copied.data_dir / "fire.json").read_text(encoding="utf-8"))
        assert list(again["plans"]) == ["B01"], "an archived plan leaves the export with the folder"


def test_a_plan_with_one_of_everything_is_saved_and_read_again_by_the_model_and_every_source_the_tools_make_is_valid():
    from norms import vkf
    with _tab("fire_tab_save_all") as (window, tab, copied):
        tab.open_source(fire.new_source("B07", "Pavillon"), None, True)
        tab.reload_list(select=None)
        tab.canvas.resetTransform()
        canvas = tab.canvas
        for kind in fire.SURFACES:
            tab.surface_combo.setCurrentIndex(tab.surface_combo.findData(kind))
            _draw(tab, _square(100 + 250 * fire.SURFACES.index(kind), 100))
            fire.check_source(tab.source, "t")
        _line(tab, "wall", [(400, 400), (600, 400), (600, 600)])
        for kind in fire.DOOR_KINDS:
            for cls in vkf.door_classes() + [""]:
                tab.door_kind_combo.setCurrentIndex(tab.door_kind_combo.findData(kind))
                tab.door_class_combo.setCurrentIndex(tab.door_class_combo.findData(cls))
                n = len(tab.source.get("doors", []))
                _door(tab, (100, 300 + 30 * n), (190, 300 + 30 * n), (150, 310 + 30 * n))
                door = tab.source["doors"][-1]
                assert ("class" in door) == bool(cls) and door.get("class", "") == cls and door["kind"] == kind
                fire.check_source(tab.source, "t")
        _line(tab, "route", [(400, 700), (600, 700)])
        tab.route_text_edit.setText("Ausgang")
        tab.on_route_text()
        tab.choose_tool("exit")
        canvas.add_point((700, 100))
        canvas.add_point((780, 100))
        tab.choose_tool("width")
        canvas.add_point((700, 300))
        canvas.add_point((736, 300))
        tab.legend_check.setChecked(True)
        fire.check_source(tab.source, "t")
        assert tab.save()
        saved = fire.read_source(copied.fire_dir / "B07.json")
        assert [zone["kind"] for zone in saved["zones"]] == list(fire.SURFACES)
        assert saved["walls"] == [{"id": "W1", "class": "EI 30", "points": [[400, 400], [600, 400], [600, 600]]}]
        assert len(saved["doors"]) == 6 and len(saved["exits"]) == 1 and len(saved["widths"]) == 1
        assert saved["routes"] == [{"id": "F1", "points": [[400, 700], [600, 700]], "text": "Ausgang"}] and saved["legend"] == fire.legend_default(tab.frame())
        tab.dirty = False
        tab.open_source(fire.new_source("Other"), None, False)
        tab.load("B07")
        assert [tree.topLevelItemCount() for tree in tab.tree_list] == [3, 1, 6, 3] and tab.legend_check.isChecked() and not tab.dirty


def test_the_draft_and_the_choices_of_the_bar_survive_a_rebuild_of_the_window():
    with _tab("fire_tab_state") as (window, tab, copied):
        _fresh(tab, "Pavillon")
        _draw(tab, _square(100, 100))
        tab.surface_combo.setCurrentIndex(tab.surface_combo.findData("clear"))
        tab.wall_combo.setCurrentIndex(tab.wall_combo.findData("EI 90"))
        tab.door_kind_combo.setCurrentIndex(tab.door_kind_combo.findData("slide"))
        tab.door_class_combo.setCurrentIndex(tab.door_class_combo.findData(""))
        tab.choose_tool("door")
        tab.id_edit.setText("Entwurf")
        state = tab.view_state()
        # a rebuild is a way of leaving the plan: it is saved on the way (autosave, v0.114) -- or, where it cannot be, carried as its draft
        saved = (copied.fire_dir / "Entwurf.json").is_file()
        assert state["draft"]["zones"] and (state["dirty"] or saved) and state["tool"] == "door"
        assert (state["zone_kind"], state["wall_class"], state["door_kind"], state["door_class"]) == ("clear", "EI 90", "slide", None)
        # the others chosen, a plan opened: restoring puts back the plan, the tool and every choice
        tab.surface_combo.setCurrentIndex(tab.surface_combo.findData("vertical"))
        tab.wall_combo.setCurrentIndex(tab.wall_combo.findData("EI 30"))
        tab.door_kind_combo.setCurrentIndex(tab.door_kind_combo.findData("swing"))
        tab.door_class_combo.setCurrentIndex(tab.door_class_combo.findData("E 30"))
        tab.open_source(fire.new_source("Other"), None, False)
        tab.restore(state)
        assert tab.source["id"] == "Entwurf" and tab.source["plan"] == "Pavillon" and len(tab.source["zones"]) == 1
        assert (tab.dirty or saved) and tab.canvas.tool == "door" and tab.id_edit.text() == "Entwurf"
        canvas = tab.canvas
        assert (canvas.zone_kind, canvas.wall_class, canvas.door_kind, canvas.door_class) == ("clear", "EI 90", "slide", None)
        assert tab.surface_combo.currentData() == "clear" and tab.door_class_combo.currentData() == "" and tab.door_kind_combo.currentData() == "slide"
        # the window itself rebuilds every tab from view_state() on a language switch
        window.views = {key: t.view_state() for (key, _factory), t in zip(__import__("woodcore_gui").TABS, window.tabs)}
        window.rebuild()
        again = next(t for t in window.tabs if type(t).__name__ == "FireTab")
        assert again.source["id"] == "Entwurf" and (again.dirty or (copied.fire_dir / "Entwurf.json").is_file()), "the draft was neither carried nor saved"
        assert (again.canvas.zone_kind, again.canvas.wall_class, again.canvas.door_kind, again.canvas.door_class) == ("clear", "EI 90", "slide", None)
        assert again.canvas.lang == again.app.lang
        again.dirty = False


def test_a_project_opened_read_only_saves_nothing():
    with _tab("fire_tab_readonly") as (window, tab, copied):
        tab.open_source(fire.new_source("B09", "Pavillon"), None, True)
        window.read_only = True
        try:
            assert tab.save() is False
        finally:
            window.read_only = False
        assert not (copied.fire_dir / "B09.json").exists()


def test_the_words_of_the_new_tools_are_in_each_language_and_name_what_they_are():
    _qt()
    import fire_tab
    keys = ("fp_zones", "fp_walls", "fp_doors", "fp_escape", "fp_group_escape", "fp_col_kind", "fp_col_class", "fp_col_length", "fp_col_width", "fp_col_symbol",
            "fp_col_value", "fp_col_text", "fp_symbol_length", "fp_symbol_exit", "fp_symbol_width", "fp_tool_polygon", "fp_tool_wall", "fp_tool_door", "fp_tool_route",
            "fp_tool_exit", "fp_tool_width", "fp_hint_polygon", "fp_hint_wall", "fp_hint_door", "fp_hint_route", "fp_hint_exit", "fp_hint_width", "fp_surface_kind_tip",
            "fp_door_kind_tip", "fp_door_class_tip", "fp_door_swing", "fp_door_slide", "fp_door_plain", "fp_flip_hinge", "fp_flip_hinge_tip", "fp_flip_side",
            "fp_flip_side_tip", "fp_group_legend", "fp_legend_show", "fp_legend_note", "fp_width", "fp_width_value", "fp_mixed", "fp_delete_selection",
            "fp_kind_zones", "fp_kind_walls", "fp_kind_doors", "fp_kind_routes", "fp_kind_exits", "fp_kind_widths")
    for lang, words in fire_tab.STRINGS.items():
        for key in keys:
            assert words.get(key, "").strip(), (lang, key)
            assert "ß" not in words[key], (lang, key)
        assert "{width}" in words["fp_width_value"] and "{detail}" in words["fp_mixed"] and "{count}" in words["fp_mixed"], lang
        assert all("{n}" in words[f"fp_kind_{collection}"] for collection in fire.COLLECTIONS), lang
    names = {lang: (words["fp_tool_polygon"], words["fp_tool_wall"], words["fp_tool_door"], words["fp_legend_show"], words["fp_door_plain"])
             for lang, words in fire_tab.STRINGS.items()}
    assert names == {"fr": ("Surface", "Paroi", "Porte", "Légende sur le plan", "Sans résistance"),
                     "de": ("Fläche", "Wand", "Türe", "Legende auf dem Plan", "Ohne Widerstand"),
                     "en": ("Surface", "Wall", "Door", "Legend on the plan", "No resistance")}, names
    # the French calls a zone a «surface»
    assert "zone" not in " ".join(text.lower() for key, text in fire_tab.STRINGS["fr"].items() if not key.startswith("warn_")), "the window says surface"


# --- the right pane: sizes, opacity, text, legend, crop, calls, export ----------------------------------

def _everything(tab):
    """A draft with one entry of every kind, drawn through the canvas's own tools: a surface Z1, a wall W1, a door T1, an escape route's length F1, an emergency exit N1 and a width B1. The selection tool is chosen at the end; the last entry drawn is the one selected."""
    _fresh(tab)
    _draw(tab, _square(100, 100))
    _line(tab, "wall", [(400, 400), (600, 400)])
    _door(tab, (100, 300), (190, 300), (150, 310))
    _line(tab, "route", [(400, 700), (600, 700)])
    tab.choose_tool("exit")
    tab.canvas.add_point((700, 100))
    tab.canvas.add_point((780, 100))
    tab.choose_tool("width")
    tab.canvas.add_point((700, 300))
    tab.canvas.add_point((736, 300))
    tab.choose_tool("select")
    return tab.source


def _hold(slider, values):
    """A slider dragged: pressed, taken through `values`, released -- what one drag of the mouse is."""
    slider.sliderPressed.emit()
    for value in values:
        slider.setValue(value)
    slider.sliderReleased.emit()


def test_the_plans_two_sliders_state_the_strokes_and_the_texts_one_step_per_drag_and_show_the_values_of_a_loaded_plan():
    with _tab("fire_tab_style") as (window, tab, copied):
        _fresh(tab)
        assert list(tab.style_sliders) == ["line", "text"], "the symbols placed on a point are drawn by nothing here"
        assert [slider.value() for slider in tab.style_sliders.values()] == [100, 100] and "style" not in tab.source
        steps = len(tab.undo_stack)
        _hold(tab.style_sliders["line"], (120, 150, 180))
        assert tab.source["style"] == {"line": 1.8} and len(tab.undo_stack) == steps + 1 and tab.dirty, "the whole drag is one step"
        fire.check_source(tab.source, "t")
        tab.style_sliders["text"].setValue(60)   # a value set without a drag is a step of its own
        assert tab.source["style"] == {"line": 1.8, "text": 0.6} and len(tab.undo_stack) == steps + 2
        tab.undo()
        assert tab.source["style"] == {"line": 1.8} and tab.style_sliders["text"].value() == 100, "the sliders follow a step undone"
        tab.undo()
        assert "style" not in tab.source and tab.style_sliders["line"].value() == 100
        tab.redo()
        assert tab.style_sliders["line"].value() == 180 and tab.source["style"] == {"line": 1.8}
        # a plan loaded shows what it states, and writes nothing and leaves no step doing so
        source = fire.new_source("S1")
        source["style"] = {"line": 2.0, "text": 0.5}
        tab.open_source(source, None, False)
        assert [slider.value() for slider in tab.style_sliders.values()] == [200, 50]
        assert tab.source["style"] == {"line": 2.0, "text": 0.5} and tab.undo_stack == [] and not tab.dirty
        # and a plan that states none shows 100 % again
        tab.open_source(fire.new_source("S2"), None, False)
        assert [slider.value() for slider in tab.style_sliders.values()] == [100, 100] and "style" not in tab.source
        # a rebuild of the window gives them back too
        tab.open_source(source, None, False)
        state = tab.view_state()
        tab.open_source(fire.new_source("Other"), None, False)
        tab.restore(state)
        assert [slider.value() for slider in tab.style_sliders.values()] == [200, 50]
        # they are the plan's and not its frame's: a plan that follows a position plan keeps them
        _fresh(tab, "Pavillon")
        assert not tab.own_frame() and all(slider.isEnabled() for slider in tab.style_sliders.values())
        tab.style_sliders["text"].setValue(80)
        assert tab.source["style"] == {"text": 0.8}


def test_the_selections_own_size_offers_the_factors_every_entry_selected_may_state_and_states_them_on_all_of_them():
    import theme
    with _tab("fire_tab_own_size") as (window, tab, copied):
        source = _everything(tab)
        canvas = tab.canvas
        rows = tab.entry_style.rows

        def offered():
            return [key for key in figure_style.KEYS if rows[key]["name"].isVisibleTo(tab.own_card)]

        def card_shown():
            return tab.own_card.isVisibleTo(tab.selection_group)

        canvas.select_ids([])
        assert not card_shown(), "nothing selected, nothing to size"
        for ids, expected in ((["Z1"], ["line", "text"]), (["W1"], ["line"]), (["T1"], ["line"]), (["F1"], ["line", "text"]), (["B1"], ["text"]),
                              (["Z1", "W1"], ["line"]), (["Z1", "F1"], ["line", "text"])):
            canvas.select_ids(ids)
            assert offered() == expected and card_shown(), (ids, offered())
        # an emergency exit states no factor, and its card is only its opacity
        canvas.select_ids(["N1"])
        assert offered() == [] and card_shown() and tab.entry_opacity["name"].isVisibleTo(tab.own_card)
        # a wall and a width have no factor in common, and no opacity or text of the width's to give: nothing to show
        canvas.select_ids(["W1", "B1"])
        assert offered() == [] and not tab.entry_opacity["name"].isVisibleTo(tab.own_card) and not card_shown()
        # one wall: setting a factor states it, in orange with «Reprendre»; 100 % is still stated; «Reprendre» takes it off with the `style`
        canvas.select_ids(["W1"])
        wall = source["walls"][0]
        row = rows["line"]
        assert not row["back"].isVisibleTo(tab.own_card) and "color" not in row["name"].styleSheet() and row["slider"].value() == 100
        steps = len(tab.undo_stack)
        row["slider"].setValue(150)
        assert wall["style"] == {"line": 1.5} and len(tab.undo_stack) == steps + 1 and tab.dirty
        orange = theme.colour("override")
        assert orange in row["name"].styleSheet() and orange in row["readout"].styleSheet() and row["back"].isVisibleTo(tab.own_card)
        row["slider"].setValue(100)
        assert wall["style"] == {"line": 1.0}, "100 % states it all the same: «Reprendre» is the one way back"
        fire.check_source(source, "t")
        row["back"].click()
        assert "style" not in wall and not row["back"].isVisibleTo(tab.own_card) and "color" not in row["name"].styleSheet()
        # a drag is one step
        steps = len(tab.undo_stack)
        _hold(row["slider"], (110, 140, 190))
        assert wall["style"] == {"line": 1.9} and len(tab.undo_stack) == steps + 1
        tab.undo()
        wall = source["walls"][0]   # a step undone puts back a copy of the source: its entries are other dictionaries
        assert "style" not in wall and row["slider"].value() == 100 and not row["back"].isVisibleTo(tab.own_card), "the card follows a step undone"
        # several entries: all of them take it, and «Reprendre» takes it off all of them -- the surface keeps its own text factor
        zone = source["zones"][0]
        zone["style"] = {"text": 0.5}
        canvas.select_ids(["Z1", "W1"])
        row["slider"].setValue(200)
        assert zone["style"] == {"text": 0.5, "line": 2.0} and wall["style"] == {"line": 2.0}
        fire.check_source(source, "t")
        row["back"].click()
        assert zone["style"] == {"text": 0.5} and "style" not in wall
        # a factor stated by one of the entries is shown, orange, at the first value found
        wall["style"] = {"line": 1.3}
        canvas.select_ids([])
        canvas.select_ids(["Z1", "W1"])
        assert row["slider"].value() == 130 and row["back"].isVisibleTo(tab.own_card) and orange in row["name"].styleSheet()
        # a width's text factor, and nothing else
        canvas.select_ids(["B1"])
        rows["text"]["slider"].setValue(70)
        assert source["widths"][0]["style"] == {"text": 0.7}
        fire.check_source(source, "t")


def test_the_selections_opacity_is_the_default_of_its_kind_until_stated_and_is_not_offered_for_a_width():
    import theme
    with _tab("fire_tab_opacity") as (window, tab, copied):
        source = _everything(tab)
        canvas = tab.canvas
        row = tab.entry_opacity
        zone, wall = source["zones"][0], source["walls"][0]

        def shown():
            return row["name"].isVisibleTo(tab.own_card)

        canvas.select_ids(["B1"])
        assert not shown(), "a width is a text: it has no opacity"
        canvas.select_ids(["Z1"])
        assert shown() and row["slider"].value() == 65 and not row["back"].isVisibleTo(tab.own_card) and "color" not in row["name"].styleSheet()
        zone["kind"] = "clear"
        canvas.select_ids([])
        canvas.select_ids(["Z1"])
        assert row["slider"].value() == 100, "a surface to be kept clear is hatched, not tinted: it is drawn full"
        zone["kind"] = "horizontal"
        canvas.select_ids([])
        canvas.select_ids(["Z1"])
        steps = len(tab.undo_stack)
        row["slider"].setValue(40)
        assert zone["opacity"] == 0.4 and len(tab.undo_stack) == steps + 1 and tab.dirty
        orange = theme.colour("override")
        assert orange in row["name"].styleSheet() and orange in row["readout"].styleSheet() and row["back"].isVisibleTo(tab.own_card)
        fire.check_source(source, "t")
        tab.undo()
        zone = source["zones"][0]   # a step undone puts back a copy of the source: its entries are other dictionaries
        assert "opacity" not in zone and row["slider"].value() == 65 and not row["back"].isVisibleTo(tab.own_card), "the row follows a step undone"
        tab.redo()
        zone = source["zones"][0]
        assert zone["opacity"] == 0.4 and row["slider"].value() == 40
        row["back"].click()
        assert "opacity" not in zone and row["slider"].value() == 65 and not row["back"].isVisibleTo(tab.own_card)
        # a drag is one step, and several entries take it together; a width in the selection takes the row away
        zone, wall = source["zones"][0], source["walls"][0]
        canvas.select_ids(["Z1", "W1"])
        steps = len(tab.undo_stack)
        _hold(row["slider"], (90, 50, 30))
        assert zone["opacity"] == 0.3 and wall["opacity"] == 0.3 and len(tab.undo_stack) == steps + 1
        fire.check_source(source, "t")
        canvas.select_ids(["Z1", "B1"])
        assert not shown()
        # a wall's default is whole
        wall.pop("opacity")
        canvas.select_ids([])
        canvas.select_ids(["W1"])
        assert row["slider"].value() == 100


def test_a_text_dragged_on_the_plan_stays_where_it_was_put_and_the_selections_card_puts_it_back_in_one_step():
    from domains import fire_svg
    with _tab("fire_tab_text_place") as (window, tab, copied):
        _fresh(tab)
        canvas = tab.canvas
        _draw(tab, _square(100, 100))
        tab.zone_label.setText("Halle")
        tab.on_zone_label()
        tab.on_zone_label_done()
        _draw(tab, [(400, 100), (600, 100), (600, 300), (400, 300)])
        canvas.select_ids(["Z1"])
        zone = tab.source["zones"][0]
        assert tab.text_place.isVisibleTo(tab.own_card) and tab.text_home.isVisibleTo(tab.text_place) and not tab.text_reset_button.isVisibleTo(tab.text_place)
        home = next(item for item in fire_svg.text_frames(tab.source, tab.frame(), editing=True) if item["id"] == "Z1")["at"]
        tab.choose_tool("select")
        steps = len(tab.undo_stack)
        _drag(canvas, home, [(home[0] + 20, home[1] + 10), (home[0] + 60, home[1] + 40)])
        assert "label_offset" in zone and abs(zone["label_offset"][0] - 60) < 3 and abs(zone["label_offset"][1] - 40) < 3, zone.get("label_offset")
        assert len(tab.undo_stack) == steps + 1, "the whole drag is one step"
        fire.check_source(tab.source, "t")
        assert tab.text_reset_button.isVisibleTo(tab.text_place) and not tab.text_home.isVisibleTo(tab.text_place), "the card follows the canvas"
        tab.text_reset_button.click()
        assert "label_offset" not in zone and len(tab.undo_stack) == steps + 2
        assert tab.text_home.isVisibleTo(tab.text_place) and not tab.text_reset_button.isVisibleTo(tab.text_place)
        tab.undo()
        zone = tab.source["zones"][0]   # a step undone puts back a copy of the source: its entries are other dictionaries
        assert "label_offset" in zone and tab.text_reset_button.isVisibleTo(tab.text_place)
        # two entries have no one text to move; a wall writes none, an escape route its length and a width its figure
        canvas.select_ids(["Z1", "Z2"])
        assert not tab.text_place.isVisibleTo(tab.own_card)
        _everything(tab)
        canvas.select_ids(["W1"])
        assert not tab.text_place.isVisibleTo(tab.own_card)
        canvas.select_ids(["F1"])
        assert tab.text_place.isVisibleTo(tab.own_card), "an escape route writes its length"
        canvas.select_ids(["B1"])
        assert tab.text_place.isVisibleTo(tab.own_card), "a width writes its figure"


def test_the_legends_size_is_a_slider_enabled_only_while_there_is_a_legend_and_it_resizes_the_box():
    from domains import fire_svg
    with _tab("fire_tab_legend_size") as (window, tab, copied):
        _fresh(tab)
        slider = tab.legend_slider
        assert not slider.isEnabled() and not tab.legend_size.isEnabled()
        assert slider.toolTip() == tab.t("fp_legend_size_tip") and tab.legend_size.toolTip() == tab.t("fp_legend_size_tip"), "a disabled control says why"
        tab.legend_check.setChecked(True)
        assert slider.isEnabled() and slider.value() == 100 and slider.toolTip() == ""
        before = fire_svg.legend_box(tab.source, tab.frame(), tab.app.lang)
        steps = len(tab.undo_stack)
        _hold(slider, (120, 160, 200))
        legend = tab.source["legend"]
        assert legend["scale"] == 2.0 and (legend["x"], legend["y"]) == (before[0], before[1]) and len(tab.undo_stack) == steps + 1
        fire.check_source(tab.source, "t")
        assert fire.legend_scale(tab.source) == 2.0
        after = fire_svg.legend_box(tab.source, tab.frame(), tab.app.lang)
        assert after[2] > 1.9 * before[2] and after[3] > 1.9 * before[3], (before, after)
        tab.undo()
        assert "scale" not in tab.source["legend"] and slider.value() == 100
        tab.redo()
        assert slider.value() == 200
        # off, its size is forgotten with the legend, and the slider says why it is greyed
        tab.legend_check.setChecked(False)
        assert "legend" not in tab.source and not slider.isEnabled() and slider.toolTip() == tab.t("fp_legend_size_tip") and slider.value() == 100
        # a plan loaded shows the size it states, enabled
        source = fire.new_source("L")
        source["legend"] = {"x": 20.0, "y": 30.0, "scale": 0.5}
        tab.open_source(source, None, False)
        assert slider.isEnabled() and slider.value() == 50 and tab.source["legend"]["scale"] == 0.5 and tab.undo_stack == []


def test_a_plan_following_a_position_plan_states_a_crop_of_its_own_draws_it_with_the_canvas_and_takes_the_position_plans_again():
    with _tab("fire_tab_crop") as (window, tab, copied):
        pav = fire.plan_frames(copied.plans_dir)["Pavillon"]
        _fresh(tab, "Pavillon")
        canvas = tab.canvas
        loaded = []
        canvas.load_background = lambda: loaded.append(1)   # a crop does not touch the background: it must not be loaded again

        def card():
            return tab.crop_group

        def rect():
            r = canvas.crop_item.rect()
            return [r.x(), r.y(), r.width(), r.height()]

        def crop_of(frame):
            return [frame["crop"][key] for key in ("x", "y", "w", "h")]

        # the position plan's crop, followed: its words, no «Reprendre», no «Feuille entière», and the tool to draw one of its own
        assert "crop" not in tab.source
        assert tab.crop_state.isVisibleTo(card()) and tab.crop_state.text() == tab.t("fp_crop_followed", plan="Pavillon")
        assert not tab.crop_take_back_button.isVisibleTo(card()) and not tab.reset_crop_button.isVisibleTo(card())
        assert tab.crop_draw_button.isEnabled() and crop_of(canvas.frame_source()) == crop_of(pav) and rect() == crop_of(pav)
        # drawn by the canvas's own crop tool: it states `crop` in the source, and one step of the history
        steps = len(tab.undo_stack)
        tab.crop_draw_button.click()
        assert canvas.tool == "crop"
        canvas.resetTransform()   # the crop tool shows the whole page and fits it (v0.114): back to a pixel a unit, so the drag lands where it is aimed
        w, h = pav["sheet"]["width"], pav["sheet"]["height"]
        start, stop = (0.1 * w, 0.2 * h), (0.5 * w, 0.6 * h)
        _drag(canvas, start, [(0.3 * w, 0.4 * h), stop])
        assert "crop" in tab.source and len(tab.undo_stack) == steps + 1 and tab.dirty and canvas.tool == "select"
        mine = tab.source["crop"]
        assert abs(mine["x"] - start[0]) < 2 and abs(mine["y"] - start[1]) < 2 and abs(mine["w"] - 0.4 * w) < 3 and abs(mine["h"] - 0.4 * h) < 3, mine
        fire.check_source(tab.source, "t")
        # ... and the canvas draws over it, the line turns «own», in orange, with «Reprendre»
        import theme
        assert crop_of(canvas.frame_source()) == [mine["x"], mine["y"], mine["w"], mine["h"]] and rect() == crop_of(canvas.frame_source())
        assert tab.frame()["crop"] == mine and tab.frame()["sheet"] == pav["sheet"], "the rest of the frame is still the position plan's"
        assert tab.crop_state.text() == tab.t("fp_crop_own") and theme.colour("override") in tab.crop_state.styleSheet()
        assert tab.crop_take_back_button.isVisibleTo(card()) and tab.crop_take_back_button.toolTip() == tab.t("fp_crop_take_back_tip", plan="Pavillon")
        assert not tab.reset_crop_button.isVisibleTo(card())
        # undone, the position plan's crop is back, everywhere; redone, the plan's own
        tab.undo()
        assert "crop" not in tab.source and crop_of(canvas.frame_source()) == crop_of(pav) and rect() == crop_of(pav)
        assert tab.crop_state.text() == tab.t("fp_crop_followed", plan="Pavillon") and not tab.crop_take_back_button.isVisibleTo(card())
        tab.redo()
        assert tab.source["crop"] == mine and rect() == [mine["x"], mine["y"], mine["w"], mine["h"]] and tab.crop_take_back_button.isVisibleTo(card())
        # «Reprendre» takes the position plan's again, in one step
        steps = len(tab.undo_stack)
        tab.crop_take_back_button.click()
        assert "crop" not in tab.source and len(tab.undo_stack) == steps + 1
        assert crop_of(canvas.frame_source()) == crop_of(pav) and rect() == crop_of(pav) and tab.frame()["crop"] == pav["crop"]
        assert tab.crop_state.text() == tab.t("fp_crop_followed", plan="Pavillon") and not tab.crop_take_back_button.isVisibleTo(card())
        assert loaded == [], "the background was loaded again for a crop"
        # a plan with a frame of its own has neither state nor «Reprendre»: it draws a crop and takes the whole sheet back
        _scaled(tab)
        assert not tab.crop_state.isVisibleTo(card()) and not tab.crop_take_back_button.isVisibleTo(card())
        assert tab.reset_crop_button.isVisibleTo(card()) and tab.crop_draw_button.isEnabled()
        sheet = tab.source["sheet"]
        tab.crop_draw_button.click()
        tab.canvas.resetTransform()
        _drag(tab.canvas, (0.2 * sheet["width"], 0.2 * sheet["height"]), [(0.6 * sheet["width"], 0.6 * sheet["height"])])
        assert "crop" in tab.source and abs(tab.source["crop"]["w"] - 0.4 * sheet["width"]) < 3
        assert crop_of(tab.frame()) == [tab.source["crop"][key] for key in ("x", "y", "w", "h")]
        tab.reset_crop_button.click()
        assert "crop" not in tab.source
        r = tab.canvas.crop_item.rect()
        assert (r.x(), r.y(), r.width(), r.height()) == (0.0, 0.0, sheet["width"], sheet["height"])


def test_the_command_entry_builds_show_fire_plan():
    """The «Commande Typst» entry of the left pane is the position plan's builder with #show-fire-plan's options (plan_command_builder.FireCommandOptions): chosen, its preview in the middle and its options on the right, its command a #show-fire-plan of the plans the export carries."""
    with _tab("fire_tab_builder", own_plans=True) as (window, tab, copied):
        tab.export("", "exported")
        tab.set_view("typst")   # the «Commande Typst» row of v0.114 is the «Typst» view since v0.117
        assert tab.view_kind == "command" and tab.view == "typst"
        assert tab.center.currentWidget() is tab.builder.preview and tab.right.currentWidget().isAncestorOf(tab.builder.options)
        assert tab.builder.command().startswith("#show-fire-plan("), tab.builder.command()
        tab.builder.stop()
        tab.show_plan_view()
        assert tab.center.currentWidget() is tab.center.widget(0) and tab.view == "draw"


def test_saving_exports_the_plans_a_failing_export_leaves_the_plan_saved_and_says_why_and_the_exports_warnings_are_shown_under_the_plan():
    from PySide6.QtWidgets import QMessageBox
    with _tab("fire_tab_export") as (window, tab, copied):
        shown, statuses = [], []
        QMessageBox.warning = staticmethod(lambda parent, title, text, *a, **k: shown.append(text) or QMessageBox.StandardButton.Ok)
        said = conftest.notices_said(lambda notice: shown.append(notice.text))   # what was a box is a notice since v0.117
        said.__enter__()
        window.set_status = lambda text, *a, **k: statuses.append(text)
        # a failing export: the file is written, the plan is saved, the engineer is told, data/ is as it was
        original = fire.export

        def boom(*args, **kwargs):
            raise OSError("disk full")

        fire.export = boom
        try:
            tab.open_source(fire.new_source("B07", "Pavillon"), None, True)
            tab.reload_list(select=None)
            assert tab.save() is True
        finally:
            fire.export = original
        assert fire.read_source(copied.fire_dir / "B07.json")["id"] == "B07" and tab.current_id == "B07" and not tab.dirty
        assert not (copied.data_dir / "fire.json").exists()
        assert len(shown) == 1 and shown[0] == tab.t("fp_export_failed", id="B07", error=OSError("disk full")) and "disk full" in shown[0] and "B07" in shown[0], shown
        # exported: the plan is in data/fire.json, and the status line says it is saved
        shown.clear()
        statuses.clear()
        tab.source["zones"].append({"id": "Z1", "kind": "horizontal", "points": [[100, 100], [300, 100], [300, 300]]})
        assert tab.save() is True and not shown
        assert list(json.loads((copied.data_dir / "fire.json").read_text(encoding="utf-8"))["plans"]) == ["B07"]
        assert tab.export_notes == [] or all(str(n).startswith("fire-protection plan B07:") for n in tab.export_notes)
        # a warning of the export: its own crop leaves the sheet of the position plan it follows -- counted, and shown under the plan in the window's language
        statuses.clear()
        tab.source["crop"] = {"x": -50.0, "y": 0.0, "w": 100.0, "h": 100.0}
        assert tab.save() is True and not shown
        codes = [n.code for n in tab.export_notes]
        assert "fire_crop_outside" in codes and all(str(n).startswith("fire-protection plan B07:") for n in tab.export_notes), codes
        assert statuses[-1] == tab.t("fp_saved_warnings", id="B07", n=len(tab.export_notes)), statuses
        assert window.note_text(next(n for n in tab.export_notes if n.code == "fire_crop_outside")) in tab.message.toPlainText()
        # one the plan's own checks do not make: the position plan it follows is not in the export yet -- shown too, once saved
        plans = copied.data_dir / "plans.json"
        data = json.loads(plans.read_text(encoding="utf-8"))
        del data["plans"]["Pavillon"]
        plans.write_text(json.dumps(data), encoding="utf-8")
        tab.source.pop("crop")
        statuses.clear()
        assert tab.save() is True
        assert "fire_plan_unexported" in [n.code for n in tab.export_notes], [n.code for n in tab.export_notes]
        unexported = next(n for n in tab.export_notes if n.code == "fire_plan_unexported")
        assert window.note_text(unexported) in tab.message.toPlainText() and tab.t("warn_fire_plan_unexported", fire="B07", plan="Pavillon") in tab.message.toPlainText()
        assert statuses[-1] == tab.t("fp_saved_warnings", id="B07", n=len(tab.export_notes))
        # the notes are of the plan last saved, and go when another is opened
        tab.open_source(fire.new_source("Other"), None, False)
        assert tab.export_notes == [] and "Pavillon" not in tab.message.toPlainText()
        # a drop into a folder and an archive export at once: «Supprimer» takes the plan out of data/fire.json
        tab.dirty = False
        tab.load("B07")
        tab.reload_list("B07")
        tab.delete()
        assert json.loads((copied.data_dir / "fire.json").read_text(encoding="utf-8"))["plans"] == {}
        # a failing export after an archive says so with the folder's own sentence
        shown.clear()
        fire.export = boom
        try:
            assert tab.export_plans("done") is False
        finally:
            fire.export = original
        assert shown == [tab.t("fp_export_failed", id="", error=OSError("disk full"))]


def test_the_words_of_the_right_pane_are_in_each_language_with_their_holes_and_every_warning_the_exports_makes_has_a_sentence():
    _qt()
    import fire_tab
    import woodcore_gui
    keys = ("fp_group_own", "fp_style_own_note", "fp_opacity", "fp_text_where", "fp_text_home", "fp_text_reset", "fp_legend_size", "fp_legend_size_tip",
            "fp_crop_followed", "fp_crop_own", "fp_crop_take_back_tip", "fp_export_failed", "fp_saved_warnings", "warn_fire_crop_outside", "warn_fire_plan_unexported")
    holes = {"fp_crop_followed": ("{plan}",), "fp_crop_take_back_tip": ("{plan}",), "fp_export_failed": ("{id}", "{error}"), "fp_saved_warnings": ("{id}", "{n}"),
             "warn_fire_crop_outside": ("{fire}", "{plan}"), "warn_fire_plan_unexported": ("{fire}", "{plan}")}
    for lang, words in fire_tab.STRINGS.items():
        for key in keys:
            assert words.get(key, "").strip() and "ß" not in words[key], (lang, key)
            for hole in holes.get(key, ()):
                assert hole in words[key], (lang, key, hole)
    # every code a Note of the fire module carries -- from `warnings` and from `prepare` -- has its sentence, in each language, naming what it is about
    codes = {"fire_plan_gone", "fire_no_scale", "fire_crop_outside", "fire_zone_outside", "fire_plan_unexported"}
    for lang in ("fr", "de", "en"):
        for code in codes:
            assert "warn_" + code in woodcore_gui.STRINGS[lang], (lang, code)
            assert "{fire}" in woodcore_gui.STRINGS[lang]["warn_" + code], (lang, code)
    outside = {"id": "B3", "label": "", "plan": "Pavillon", "crop": {"x": -10, "y": 0, "w": 50, "h": 50}, "zones": []}
    frames = {"Pavillon": {"sheet": {"width": 100, "height": 100}, "crop": {"x": 0, "y": 0, "w": 100, "h": 100}}}
    note = next(n for n in fire.warnings(outside, frames) if n.code == "fire_crop_outside")
    for lang in ("fr", "de", "en"):
        text = woodcore_gui.note_text(note, lang)
        assert text != str(note) and "{" not in text and "B3" in text and "Pavillon" in text, (lang, text)


def test_the_right_pane_asks_for_no_more_width_than_the_position_plans_whatever_is_selected():
    """The cards are a column that is never narrower than its widest card (cards.py), so a card that sets a width of its own sets the pane's: the crop's, the legend's size row, the selection's own size and the calls are measured against the position plan's own pane in the same font, with every layout settled -- a hidden button stays in a layout's minimum until the layout is activated again, which is not what an engineer sees."""
    from PySide6.QtWidgets import QWidget
    app = _qt()
    with _tab("fire_tab_pane_width") as (window, tab, copied):
        plan_pane = next(t for t in window.tabs if type(t).__name__ == "PlanTab").splitter.widget(2)
        pane = tab.splitter.widget(2)

        def settled(widget):
            for _ in range(3):   # the events a hidden widget posts are handled between two passes, and a pass sees what the one before it hid
                app.processEvents()
                for child in widget.findChildren(QWidget) + [widget]:
                    if child.layout() is not None:
                        child.layout().invalidate()
                for child in [widget] + widget.findChildren(QWidget):
                    if child.layout() is not None:
                        child.layout().activate()
            return widget.minimumSizeHint().width()

        reference = settled(plan_pane)
        _everything(tab)
        for ids in ([], ["Z1"], ["W1"], ["F1"], ["N1"], ["B1"], ["Z1", "W1"]):
            tab.canvas.select_ids(ids)
            assert settled(pane) <= reference, (ids, settled(pane), reference)
        for source in (fire.new_source("P1", "Pavillon"), fire.new_source("P2")):
            tab.open_source(source, None, False)
            assert settled(pane) <= reference, (source["id"], settled(pane), reference)
        tab.crop_group.layout().activate()
        tab.open_source(fire.new_source("P3", "Pavillon"), None, False)
        tab.source["crop"] = {"x": 10.0, "y": 10.0, "w": 100.0, "h": 100.0}
        tab.on_changed()
        assert tab.crop_take_back_button.isVisibleTo(tab.crop_group) and settled(pane) <= reference, "the plan's own crop shows «Reprendre» and still fits"


# --- the example project's own plans ------------------------------------------------------------------

def test_the_example_projects_own_two_plans_open_in_the_tab_and_are_saved_and_exported_as_they_are():
    """The two plans the worked examples of `show-fire-plan` name are the example project's own sources: one follows the position plan «Pavillon», the other carries a sheet, a scale, a legend of a size of its own, a wall drawn at a factor of its own and a width whose text was moved. Each opens in the tab as the right pane says it, and saving one writes back the very source it was read as -- so the tab loses nothing the model carries."""
    with _tab("fire_tab_example_plans", own_plans=True) as (window, tab, copied):
        ids = [fid for fid, *_rest in __import__("fire_tab").list_fire_plans(copied.fire_dir)]
        assert ids == ["Pavillon-EG", "Treppenhaus"], ids
        for fid in ids:
            before = json.loads((copied.fire_dir / f"{fid}.json").read_text(encoding="utf-8"))
            tab.dirty = False
            tab.load(fid)
            assert tab.current_id == fid and tab.source == before and not tab.dirty
            fire.check_source(tab.source, f"{fid}.json")
            assert tab.style_sliders["line"].value() == int(round(100 * fire.drawing_factors(before)["line"]))
            assert tab.legend_check.isChecked() == ("legend" in before)
            assert tab.legend_slider.value() == int(round(100 * fire.legend_scale(before)))
            assert tab.save()
            # written back as it was read -- as 2.0, the one thing that changes: Gian's 1.0 sources are upgraded when they are saved, and not before (v0.115)
            assert json.loads((copied.fire_dir / f"{fid}.json").read_text(encoding="utf-8")) == dict(before, schema_version=fire.SOURCE_SCHEMA_VERSION), f"{fid} is written back as it was read"
        exported = json.loads((copied.data_dir / fire.EXPORT_FILE).read_text(encoding="utf-8"))
        assert list(exported["plans"]) == ids and exported["plans"]["Pavillon-EG"]["plan"] == "Pavillon"
        # the plan that follows a position plan says whose crop it shows; the one with a sheet of its own offers «Feuille entière»
        tab.dirty = False
        tab.load("Pavillon-EG")
        assert tab.crop_state.isVisibleTo(tab.crop_group) and not tab.reset_crop_button.isVisibleTo(tab.crop_group)
        tab.load("Treppenhaus")
        assert tab.reset_crop_button.isVisibleTo(tab.crop_group) and not tab.crop_state.isVisibleTo(tab.crop_group)
        # the wall that states a factor of its own shows it in orange, with «Reprendre»
        stated = [wall["id"] for wall in tab.source["walls"] if "style" in wall]
        assert stated, "the example's own plan carries a wall at a factor of its own"
        tab.canvas.select_ids(stated[:1])
        row = tab.entry_style.rows["line"]
        assert row["back"].isVisibleTo(tab.own_card) and row["slider"].value() == int(round(100 * tab.source["walls"][[w["id"] for w in tab.source["walls"]].index(stated[0])]["style"]["line"]))


# --- v0.115: the position plan's tab a second time -- shared documents, pages ticked, both kinds turned together -------------------------------
#
# One window for the section, on a copy of the example project whose position plans are drawn on no file (the copy carries none) and which holds no fire plan, the documents tests/fixtures/layered_pdf.py's PDF written into the copy -- the arrangement of tests/test_plan_tab_rework.py. Every box shown is recorded, so a test can say that none was.

_DOCS = {}


def _doc_window():
    if "window" not in _DOCS:
        app = _qt()
        here = conftest.project_copy("fire_tab_documents")
        _without_fire_plans(here)
        from domains import plan_documents
        _DOCS["cache"] = plan_documents.CACHE_ROOT
        plan_documents.CACHE_ROOT = conftest.tmpdir("fire_tab_documents_cache")
        (here.root / "01_Pläne").mkdir(exist_ok=True)
        for path in here.plans_dir.glob("*.json"):
            source = json.loads(path.read_text(encoding="utf-8"))
            source.pop("background", None)
            path.write_text(json.dumps(source, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        with project.using(here), _recorded():
            import woodcore_gui
            window = woodcore_gui.MainWindow()
        window.reexport = lambda **kwargs: None
        _DOCS.update(app=app, window=window, here=here)
    return _DOCS["window"], _DOCS["here"]


def _doc_tabs():
    window, here = _doc_window()
    plan_tab = next(t for t in window.tabs if type(t).__name__ == "PlanTab")
    fire_tab = next(t for t in window.tabs if type(t).__name__ == "FireTab")
    for tab in (plan_tab, fire_tab):
        tab.dirty = False
    return plan_tab, fire_tab, here


@contextlib.contextmanager
def _recorded(answer=None, file=None, length=None):
    """Every box recorded; a question answered by `answer` (Yes where none is given); the file dialog answers `file`; the length asked for a calibration `length`."""
    from PySide6.QtWidgets import QFileDialog, QInputDialog, QMessageBox
    shown = []

    def box(kind):
        def show(_parent, _title, text, *args, **kwargs):
            shown.append((kind, text))
            if kind == "question":
                return answer if answer is not None else QMessageBox.StandardButton.Yes
            return QMessageBox.StandardButton.Ok
        return staticmethod(show)
    saved = {(QMessageBox, n): QMessageBox.__dict__[n] for n in ("question", "warning", "information", "critical")}
    saved[(QFileDialog, "getOpenFileName")] = QFileDialog.__dict__["getOpenFileName"]
    saved[(QInputDialog, "getDouble")] = QInputDialog.__dict__["getDouble"]
    for name in ("question", "warning", "information", "critical"):
        setattr(QMessageBox, name, box(name))
    QFileDialog.getOpenFileName = staticmethod(lambda *a, **k: (str(file) if file else "", ""))
    QInputDialog.getDouble = staticmethod(lambda *a, **k: (length, length is not None))
    try:
        yield shown
    finally:
        for (owner, name), original in saved.items():
            setattr(owner, name, original)


def _settle(tab, timeout=60):
    import time
    app = _DOCS["app"]
    end = time.monotonic() + timeout
    while tab.doc_view.is_busy():
        if time.monotonic() > end:
            raise AssertionError("the document view is still busy")
        app.processEvents()
        time.sleep(0.01)


def _imported(plan_tab, fire_tab, here, name, pages=2):
    """A PDF of `pages` pages imported ONCE, in the position plan tab, and listed in the fire tab too -- the documents are shared."""
    from fixtures import layered_pdf as fx
    path = fx.write(here.root / "01_Pläne" / name, pages=pages)
    with _recorded(file=path) as shown:
        assert plan_tab.import_document(), shown
    docid = plan_tab.doc_id
    fire_tab.reload_documents()
    fire_tab.open_document(docid)
    return docid


def _json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _done(*tabs):
    for tab in tabs:
        tab.doc_view.set_document(None, None)
        _settle(tab)
        tab.show_plan_view()
        tab.dirty = False


def test_the_fire_tab_is_right_under_the_position_plan_in_the_base_and_the_report_and_not_in_the_convention():
    """Registered as the engineer asked: in TABS and in the «Projet» group right after «Plan de positions», with the flame, «Plan de protection incendie» in three languages -- and shown in the base de projet and the report, never in the convention d'utilisation."""
    _qt()
    import chrome
    import fire_tab
    import woodcore_gui
    keys = [key for key, _cls in woodcore_gui.TABS]
    assert keys[keys.index("tab_plan") + 1] == "tab_fire", keys
    group = dict(woodcore_gui.NAV_GROUPS)["nav_project"]
    assert group[:2] == ("tab_plan", "tab_fire"), group
    assert "tab_fire" in chrome.ICONS and dict(woodcore_gui.TABS)["tab_fire"] is fire_tab.FireTab
    titles = {lang: woodcore_gui.STRINGS[lang]["tab_fire"] for lang in ("fr", "de", "en")}
    assert titles == {"fr": "Plan de protection incendie", "de": "Brandschutzplan", "en": "Fire protection plan"}, titles
    assert "tab_fire" not in woodcore_gui.mode_tabs("cu")
    assert "tab_fire" in woodcore_gui.mode_tabs("bp") and "tab_fire" in woodcore_gui.mode_tabs("rs")
    for lang, words in fire_tab.STRINGS.items():
        assert not [key for key, text in words.items() if "ß" in text], lang
    assert not [key for key, text in fire_tab.STRINGS["fr"].items() if " :" in text or " ;" in text], "a French colon or semicolon after an ordinary space"
    assert issubclass(fire_tab.FireTab, __import__("drawing_tab").DrawingTab)


def test_a_page_ticked_follows_its_one_position_plan_and_otherwise_has_a_frame_of_its_own_and_unticking_archives():
    """The documents are the position plan tab's, imported once. A page carrying exactly one position plan, ticked in the fire tab: a fire plan that FOLLOWS it; a page with none: a fire plan with a frame of its own on that page -- its sheet the page's, the document named in its background. Unticking archives the fire plans, never deletes them, and the position plan's page stays ticked in its own tab."""
    plan_tab, fire_tab, here = _doc_tabs()
    with project.using(here), _recorded():
        docid = _imported(plan_tab, fire_tab, here, "Ticked.pdf")
        before = set(plan_tab.taken_ids())
        plan_tab.on_page_toggled(1, True)
        (pid,) = set(plan_tab.taken_ids()) - before
        with _recorded() as shown:
            fire_tab.on_page_toggled(1, True)
            fire_tab.on_page_toggled(2, True)
        assert not shown, shown
        plans = {fid: _json(here.fire_dir / f"{fid}.json") for fid in fire_tab.taken_ids()}
        following = [fid for fid, s in plans.items() if s.get("plan") == pid]
        own = [fid for fid, s in plans.items() if "plan" not in s]
        assert len(following) == 1 and len(own) == 1, plans
        source = plans[own[0]]
        assert source["background"]["document"] == docid and source["background"]["page"] == 2
        assert source["sheet"] == {"width": 300.0, "height": 100.0} and source["schema_version"] == fire.SOURCE_SCHEMA_VERSION
        assert not [key for key in fire.FRAME_KEYS if key in plans[following[0]]], "a plan that follows carries no frame of its own"
        assert fire_tab.doc_view.used_pages() == [1, 2]
        records = json.loads((here.data_dir / fire.EXPORT_FILE).read_text(encoding="utf-8"))["plans"]
        assert set(plans) <= set(records), "the fire plans made are not exported"
        # the position plan's crop is drawn muted on its page, never hit, and its page marked
        fire_tab.refresh_document_view()
        assert 1 in fire_tab.doc_view.other_pages()
        assert all(crop.get("other") for crop in fire_tab.doc_view.area.crops.get(1, []) if crop.get("plan") == pid)
        # unticked: archived, not deleted
        with _recorded() as shown:
            fire_tab.on_page_toggled(2, False)
        assert not shown and own[0] not in fire_tab.taken_ids()
        archived = list((here.fire_dir / "archives").glob(f"*-{own[0]}.json"))
        assert archived, "an unticked fire plan was not archived"
        assert plan_tab.doc_view.used_pages() == [1] or pid in plan_tab.taken_ids()
        _done(plan_tab, fire_tab)


def test_the_crop_drawn_on_a_page_is_shown_alone_and_a_calibration_is_refused_on_a_plan_that_follows():
    """A crop drawn on the page of a fire plan that follows a position plan is that fire plan's own crop -- shown alone on its canvas, «Afficher toute la page» showing the page --, «Reprendre» takes the position plan's again; a calibration drawn there is refused with a word in the status line, the scale being the position plan's; on a plan with a frame of its own it is taken."""
    plan_tab, fire_tab, here = _doc_tabs()
    with project.using(here), _recorded():
        _imported(plan_tab, fire_tab, here, "Cropped.pdf")
        before = set(plan_tab.taken_ids())
        plan_tab.on_page_toggled(1, True)
        (pid,) = set(plan_tab.taken_ids()) - before
        before = set(fire_tab.taken_ids())
        fire_tab.on_page_toggled(1, True)
        (fid,) = set(fire_tab.taken_ids()) - before
        with _recorded() as shown:
            fire_tab.on_doc_crop(1, (10.0, 20.0, 150.0, 60.0))
        assert not shown, shown
        source = _json(here.fire_dir / f"{fid}.json")
        assert source["plan"] == pid and source["crop"] == {"x": 10.0, "y": 20.0, "w": 150.0, "h": 60.0}
        assert "crop" not in _json(here.plans_dir / f"{pid}.json") or _json(here.plans_dir / f"{pid}.json")["crop"] != source["crop"], "the position plan's crop was written"
        fire_tab.open_plan(fid)
        assert fire_tab.current_id == fid and fire_tab.canvas.clipped()
        rect = fire_tab.canvas.shown_rect()
        assert (rect.x(), rect.y(), rect.width(), rect.height()) == (10.0, 20.0, 150.0, 60.0)
        fire_tab.show_outside_box.setChecked(True)
        assert not fire_tab.canvas.clipped() and fire_tab.canvas.shown_rect().width() == 300.0
        fire_tab.show_outside_box.setChecked(False)
        assert fire_tab.crop_take_back_button.isVisibleTo(fire_tab.crop_group)
        # a calibration on the page of a plan that follows: refused, nothing written, no box
        statuses = []
        set_status = fire_tab.app.set_status
        fire_tab.app.set_status = lambda text: statuses.append(text)
        try:
            with _recorded(length=2.5) as shown:
                fire_tab.open_document(fire_tab.doc_id)
                fire_tab.on_doc_calibrated(1, [(0.0, 0.0), (100.0, 0.0)])
        finally:
            fire_tab.app.set_status = set_status
        assert not shown, shown
        assert "scale" not in _json(here.fire_dir / f"{fid}.json")
        assert statuses and pid in statuses[-1] and fid in statuses[-1], statuses
        # on a page of its own: taken
        before = set(fire_tab.taken_ids())
        fire_tab.on_page_toggled(2, True)
        (own,) = set(fire_tab.taken_ids()) - before
        with _recorded(length=2.5):
            fire_tab.on_doc_calibrated(2, [(0.0, 0.0), (100.0, 0.0)])
        assert _json(here.fire_dir / f"{own}.json")["scale"] == {"mode": "calibration", "points": [[0.0, 0.0], [100.0, 0.0]], "length_m": 2.5}
        _done(plan_tab, fire_tab)


def test_a_page_turned_in_either_tab_turns_the_position_plans_and_the_fire_plans_drawn_on_it():
    """plan_pages.rotate_page from both tabs: a position plan's column at (10, 20) of a page 100 high lands at (80, 10), and so does a fire plan's surface corner, whether it follows the position plan or has a frame of its own on that page -- turned from the fire tab, then back from the position plan's."""
    plan_tab, fire_tab, here = _doc_tabs()
    with project.using(here), _recorded():
        docid = _imported(plan_tab, fire_tab, here, "Turned.pdf")
        before = set(plan_tab.taken_ids())
        plan_tab.on_page_toggled(1, True)
        (pid,) = set(plan_tab.taken_ids()) - before
        position = _json(here.plans_dir / f"{pid}.json")
        position["elements"] = [{"type": "S", "label": "S001", "points": [[10, 20]]}]
        plan_tab.write_plan(position)
        before = set(fire_tab.taken_ids())
        fire_tab.on_page_toggled(1, True)
        (fid,) = set(fire_tab.taken_ids()) - before
        source = _json(here.fire_dir / f"{fid}.json")
        source["zones"] = [{"id": "Z1", "kind": "horizontal", "points": [[10, 20], [60, 20], [60, 50]]}]
        fire_tab.write_plan(source)
        with _recorded() as shown:
            assert fire_tab.rotate_page(docid, 1, 90)
        assert not shown, shown
        from domains import plan_documents
        assert plan_documents.rotation(plan_documents.read(here, docid), 1) == 90
        assert _json(here.plans_dir / f"{pid}.json")["elements"][0]["points"] == [[80, 10]]
        assert _json(here.fire_dir / f"{fid}.json")["zones"][0]["points"][0] == [80, 10]
        with _recorded() as shown:
            assert plan_tab.rotate_page(docid, 1, -90)
        assert not shown, shown
        assert plan_documents.rotation(plan_documents.read(here, docid), 1) == 0
        assert _json(here.plans_dir / f"{pid}.json")["elements"][0]["points"] == [[10, 20]]
        assert _json(here.fire_dir / f"{fid}.json")["zones"][0]["points"][0] == [10, 20]
        # a layer switched in the fire tab writes the shared document and exports both kinds
        with _recorded() as shown:
            fire_tab.on_layers_changed(["Walls"])
        assert not shown, shown
        assert plan_documents.read(here, docid)["layers_off"] == ["Walls"]
        assert (here.data_dir / "plans.json").is_file() and (here.data_dir / fire.EXPORT_FILE).is_file()
        _done(plan_tab, fire_tab)


def test_archiving_a_position_plan_that_fire_plans_follow_names_them_and_detaches_them():
    """Unticking a position plan's page -- or archiving it from its list -- asks first, naming the fire plans that follow it, and on a yes gives each the frame it followed (fire.detach): none is left over a frame that is gone."""
    plan_tab, fire_tab, here = _doc_tabs()
    with project.using(here), _recorded():
        docid = _imported(plan_tab, fire_tab, here, "Detached.pdf")
        before = set(plan_tab.taken_ids())
        plan_tab.on_page_toggled(1, True)
        (pid,) = set(plan_tab.taken_ids()) - before
        plan_tab.on_doc_crop(1, (5.0, 5.0, 200.0, 80.0))
        before = set(fire_tab.taken_ids())
        fire_tab.on_page_toggled(1, True)
        (fid,) = set(fire_tab.taken_ids()) - before
        assert _json(here.fire_dir / f"{fid}.json")["plan"] == pid
        plan_tab.open_document(docid)
        from PySide6.QtWidgets import QMessageBox
        with _recorded(answer=QMessageBox.StandardButton.No) as shown:
            plan_tab.on_page_toggled(1, False)
        assert [k for k, _t in shown] == ["question"] and fid in shown[0][1], shown
        assert pid in plan_tab.taken_ids() and _json(here.fire_dir / f"{fid}.json")["plan"] == pid, "a no detached or archived something"
        with _recorded() as shown:
            plan_tab.on_page_toggled(1, False)
        assert pid not in plan_tab.taken_ids()
        detached = _json(here.fire_dir / f"{fid}.json")
        assert "plan" not in detached and detached["background"]["document"] == docid and detached["crop"] == {"x": 5.0, "y": 5.0, "w": 200.0, "h": 80.0}
        fire.check_source(detached, f"{fid}.json")
        # and from the list's «Supprimer», through source_archive.Actions
        before = set(plan_tab.taken_ids())
        plan_tab.on_page_toggled(2, True)
        (pid2,) = set(plan_tab.taken_ids()) - before
        fire_tab.reload_documents()
        fire_tab.open_document(docid)
        before_fire = set(fire_tab.taken_ids())
        fire_tab.on_page_toggled(2, True)
        (fid2,) = set(fire_tab.taken_ids()) - before_fire
        assert _json(here.fire_dir / f"{fid2}.json").get("plan") == pid2
        with _recorded() as shown:
            plan_tab.archive.archive([pid2])
        assert shown and fid2 in shown[0][1], shown
        assert "plan" not in _json(here.fire_dir / f"{fid2}.json")
        _done(plan_tab, fire_tab)


def test_a_1_0_plan_of_gian_s_is_opened_without_being_written_and_written_as_2_0_once_left_changed():
    """The example project's two fire plans are Gian's 1.0 sources: opened, chosen, left -- not a byte written; changed and left, saved as 2.0 without a question (the position plan's autosave)."""
    _qt()
    copied = conftest.project_copy("fire_tab_one_zero")
    with project.using(copied), _recorded():
        import woodcore_gui
        before = {path.name: path.read_bytes() for path in copied.fire_dir.glob("*.json")}
        assert {json.loads(raw)["schema_version"] for raw in before.values()} == {"1.0"}
        window = woodcore_gui.MainWindow()
        try:
            tab = next(t for t in window.tabs if type(t).__name__ == "FireTab")
            ids = tab.taken_ids()
            assert sorted(ids) == ["Pavillon-EG", "Treppenhaus"], ids
            for fid in ids:
                tab.on_list_change(fid)
                assert tab.current_id == fid and not tab.dirty
            tab.on_list_change(ids[0])
            tab.hide()
            after = {path.name: path.read_bytes() for path in copied.fire_dir.glob("*.json")}
            assert after == before, "a 1.0 source was written though nothing was changed"
            tab.label_edit.setText("Geändert")
            tab.on_meta()
            assert tab.dirty
            with _recorded() as shown:
                tab.on_list_change(ids[1])
            assert not [k for k, _t in shown if k == "question"], shown
            written = _json(copied.fire_dir / f"{ids[0]}.json")
            assert written["schema_version"] == fire.SOURCE_SCHEMA_VERSION and written["label"] == "Geändert"
            assert (copied.fire_dir / f"{ids[1]}.json").read_bytes() == before[f"{ids[1]}.json"]
        finally:
            for t in window.tabs:
                if hasattr(t, "dirty"):
                    t.dirty = False
            conftest.dispose(window)
def test_every_writer_the_fire_tab_reaches_is_guarded_and_refuses_on_a_project_held_read_only():
    """woodcore_gui.WRITERS wraps writers by name on the classes its loop lists: the fire tab's own «Enregistrer» and the base's «Supprimer», drop, document and sheet archive must all be the guarded wrapper, and refuse read-only; «replace_source», the fire tab's own undo helper, is none."""
    _qt()
    import types
    import fire_tab
    import woodcore_gui
    # the fire tab's own: the class or one of its mixins (woodcore_gui.own_classes, issue #30)
    assert "replace_source" not in woodcore_gui.WRITERS and any("replace_source" in vars(k) for k in woodcore_gui.own_classes(fire_tab.FireTab))
    reached = []
    for name in woodcore_gui.WRITERS:
        if not hasattr(fire_tab.FireTab, name):
            continue
        reached.append(name)
        for cls in fire_tab.FireTab.__mro__:
            if name in vars(cls):
                assert hasattr(vars(cls)[name], "__wrapped__"), f"{cls.__name__}.{name} is not guarded"
    assert {"save", "delete", "on_moved", "delete_document", "delete_sheet"} <= set(reached), reached
    refused = []
    app = types.SimpleNamespace(read_only=True, refuse_read_only=lambda: refused.append(True))
    fake = types.SimpleNamespace(app=app)
    for name in reached:
        assert getattr(fire_tab.FireTab, name)(fake) is False, name
    assert len(refused) == len(reached)


def test_the_end_of_the_documents_section_puts_the_caches_back():
    """Last of the file: the document views and the canvases let go of the PDFs they hold -- the run's own folder is removed afterwards, which Windows refuses for a file held open --, the window closed and plan_documents' cache put back."""
    if "window" in _DOCS:
        import time
        plan_tab, fire_tab, _here = _doc_tabs()
        _done(plan_tab, fire_tab)
        app = _DOCS["app"]
        for tab in (plan_tab, fire_tab):
            canvas = tab.canvas
            end = time.monotonic() + 30
            while canvas.busy() and time.monotonic() < end:
                app.processEvents()
                time.sleep(0.01)
            if canvas.pages is not None:
                canvas.pages.drop()
                canvas.retired.append(canvas.pages)
                canvas.pages = None
            canvas.collect()
        _DOCS["window"].close()
        app.processEvents()
        from domains import plan_documents
        plan_documents.CACHE_ROOT = _DOCS["cache"]
