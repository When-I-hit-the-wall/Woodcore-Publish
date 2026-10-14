"""The plan tabs' panes reworked (v0.116, calc/tools/drawing_tab.py, plan_tab.py, fire_tab.py; docs/domain/position-plans.md §3.3sexies, docs/domain/fire-plans.md §3.3vicies, docs/ui/window.md §10quater): the crop and the calibration out of the tool bar and into the right pane; the right pane following the selection -- the plan's own modules while nothing is selected (Plan, Fond, Cadrage above Échelle, Taille des symboles), the selection's card and «Taille des symboles» while something is --; the left pane four boxes in a vertical splitter the engineer drags, scrolling up and down when they are taller than the window; and the list of plans named «Plans de position». The same in the fire-protection plan's tab, built on the same base.

The engineer, 06.10.2026: «dans les outils, il ne doit plus y avoir le cadrage ni le calibrage» · «le volet de droite doit davantage être dépendant de ce que l'on sélectionne» · «le cadrage … doit se trouver au-dessus de l'échelle» · «lorsque l'on sélectionne un objet … on gardera la taille des symboles et la taille propre» · «on doit pouvoir redimensionner la taille des boxes … et scroll». The window is built once, off-screen, on a copy of the example project (conftest.project_copy); every dialog is stubbed -- a modal off-screen never comes back.
"""

import contextlib
import os
import sys

import conftest
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


@contextlib.contextmanager
def _dialogs(length=2.5):
    """Nothing modal can block the run: a question says yes, the length asked for a calibration is `length`."""
    from PySide6.QtWidgets import QFileDialog, QInputDialog, QMessageBox
    stubs = {
        (QMessageBox, "warning"): staticmethod(lambda *a, **k: QMessageBox.StandardButton.Ok),
        (QMessageBox, "critical"): staticmethod(lambda *a, **k: QMessageBox.StandardButton.Ok),
        (QMessageBox, "information"): staticmethod(lambda *a, **k: QMessageBox.StandardButton.Ok),
        (QMessageBox, "question"): staticmethod(lambda *a, **k: QMessageBox.StandardButton.Yes if len(a) < 4 else QMessageBox.StandardButton.Discard),
        (QFileDialog, "getOpenFileName"): staticmethod(lambda *a, **k: ("", "")),
        (QInputDialog, "getDouble"): staticmethod(lambda *a, **k: (length, length is not None)),
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
        here = conftest.project_copy("plan_panes_v0116")
        with project.using(here), _dialogs():
            import woodcore_gui
            window = woodcore_gui.MainWindow()
        _STATE.update(app=app, window=window, here=here)
    return _STATE["window"], _STATE["here"]


def _tab(kind):
    window, here = _window()
    tab = next(t for t in window.tabs if type(t).__name__ == kind)
    tab.dirty = False
    return tab, here


def _plan_source(section=False):
    """A position plan of one column and one axis -- on a section, one storey line and one storey box as well -- shown unsaved."""
    from domains import plan as model
    source = model.new_source("P99", floor="0")
    source["elements"] = [{"type": "S", "label": "S001", "points": [[50.0, 50.0]]}]
    source["axes"] = [{"label": "A", "point": [100.0, 100.0], "angle": 90.0, "bubbles": "both"}]
    if section:
        source["role"] = "section"
        source["storey_lines"] = [{"storey": "EG", "points": [[0.0, 200.0], [400.0, 200.0]]}]
        source["storey_boxes"] = [{"storey": "EG", "x": 10.0, "y": 10.0, "w": 100.0, "h": 50.0}]
    return source


def _open_plan(tab, source):
    tab.open_source(source, None, False)
    tab.show_plan_view()
    tab.canvas.select(None)
    tab.dirty = False


def _titles(tab):
    return [card.title() for card in tab.visible_modules()]


# --- the tool bar --------------------------------------------------------------------------------

def test_the_crop_and_the_calibration_are_no_tools_of_the_bar():
    import fire_tab
    import plan_tab
    assert "crop" not in plan_tab.TOOLS and "calibrate" not in plan_tab.TOOLS and plan_tab.PANE_TOOLS == ("crop", "calibrate")
    assert "crop" not in fire_tab.TOOLS and "calibrate" not in fire_tab.TOOLS and fire_tab.PANE_TOOLS == ("crop", "calibrate")
    from PySide6.QtWidgets import QToolButton
    for kind in ("PlanTab", "FireTab"):
        tab, here = _tab(kind)
        with project.using(here), _dialogs():
            assert "crop" not in tab.tool_buttons and "calibrate" not in tab.tool_buttons, kind
            words = {tab.t("plan_tool_crop"), tab.t("plan_tool_calibrate")}
            on_bar = [b.text() for row in tab.tool_rows for b in row.findChildren(QToolButton)]
            assert not words & set(on_bar), (kind, on_bar)
            # in the right pane instead: «Dessiner le cadre» in «Cadrage», «Calibrer…» in «Échelle»
            assert tab.crop_draw_button.text() == tab.t("plan_crop_draw") and tab.crop_group.isAncestorOf(tab.crop_draw_button), kind
            assert tab.calibrate_button.text() == tab.t("plan_calibrate") and tab.scale_group.isAncestorOf(tab.calibrate_button), kind


def test_dessiner_le_cadre_starts_the_crop_for_one_drag_and_hands_back_the_selection():
    tab, here = _tab("PlanTab")
    with project.using(here), _dialogs():
        _open_plan(tab, _plan_source())
        tab.choose_tool("select")
        assert tab.tool_buttons["select"].isChecked()
        tab.crop_draw_button.click()
        assert tab.canvas.tool == "crop"
        assert tab.tool_group.checkedButton() is None, "a tool of the bar stays checked while the crop is drawn"
        assert tab.hint.text() == tab.t("plan_hint_crop")
        tab.canvas.tool_done.emit()   # what the canvas says once the rectangle is dragged
        assert tab.canvas.tool == "select" and tab.tool_buttons["select"].isChecked()


def test_calibrer_starts_the_calibration_whatever_the_scale_and_sets_it():
    tab, here = _tab("PlanTab")
    with project.using(here), _dialogs(length=2.5):
        _open_plan(tab, _plan_source())
        assert tab.scale_mode.currentIndex() == 0
        assert tab.calibrate_button.isEnabled(), "«Calibrer…» is the one way to the calibration: it is never greyed by the scale's mode"
        tab.calibrate_button.click()
        assert tab.canvas.tool == "calibrate" and tab.tool_group.checkedButton() is None
        tab.canvas.calibrated.emit([(0.0, 0.0), (100.0, 0.0)])
        tab.canvas.tool_done.emit()
        assert tab.source["scale"] == {"mode": "calibration", "points": [[0.0, 0.0], [100.0, 0.0]], "length_m": 2.5}
        assert tab.scale_mode.currentIndex() == 2 and tab.canvas.tool == "select"
        tab.dirty = False


# --- the right pane, by what is selected ----------------------------------------------------------

def test_with_nothing_selected_the_plan_s_modules_show_the_crop_above_the_scale():
    tab, here = _tab("PlanTab")
    with project.using(here), _dialogs():
        _open_plan(tab, _plan_source())
        assert not tab.has_selection()
        expected = [tab.t("plan_group_plan"), tab.t("plan_group_background"), tab.t("plan_group_crop"), tab.t("plan_group_scale"), tab.t("plan_group_snap"), tab.t("plan_group_style"),
                    tab.superposition.card.title()]   # «Superposition» after the sizes (WP-F)
        assert _titles(tab) == expected, _titles(tab)
        assert tab.selection_group.isHidden()
        layout = tab.properties_layout
        assert layout.indexOf(tab.crop_group) < layout.indexOf(tab.scale_group) < layout.indexOf(tab.style_group)
        # the place under the ID where the plan's type will stand
        assert tab.plan_form.itemAt(tab.plan_type_row - 1, tab.plan_form.ItemRole.FieldRole).widget() is tab.id_edit


def test_an_object_selected_hides_the_plan_s_modules_and_keeps_the_sizes():
    tab, here = _tab("PlanTab")
    with project.using(here), _dialogs():
        _open_plan(tab, _plan_source(section=True))
        from PySide6.QtWidgets import QGroupBox
        for selection in (("element", 0), ("axis", 0)):
            tab.canvas.select(selection)
            assert tab.has_selection(), selection
            assert _titles(tab) == [tab.t("plan_group_selection"), tab.t("plan_group_style")], (selection, _titles(tab))
            own = [b for b in tab.selection_group.findChildren(QGroupBox) if b.title() == tab.t("plan_style_own")]
            assert own, f"«Taille propre» is missing for {selection}"
            for card in (tab.plan_group, tab.background_group, tab.crop_group, tab.scale_group):
                assert card.isHidden(), (selection, card.title())
        # a section's storey line and storey box are objects too: their card, and the plan's modules gone
        for selection in (("storey-line", 0), ("storey-box", 0)):
            tab.canvas.select(selection)
            assert tab.has_selection(), selection
            assert _titles(tab) == [tab.t("plan_group_selection"), tab.t("plan_group_style")], (selection, _titles(tab))
        # nothing selected again: the plan's modules come back
        tab.canvas.select(None)
        assert _titles(tab)[0] == tab.t("plan_group_plan") and tab.selection_group.isHidden()
        tab.dirty = False


def test_a_later_module_takes_its_place_after_the_sizes_and_follows_the_selection():
    """insert_module: where «Superposition» (WP-F) goes -- right after «Taille des symboles», a plan module, hidden while something is selected."""
    tab, here = _tab("PlanTab")
    import cards
    with project.using(here), _dialogs():
        _open_plan(tab, _plan_source())
        card = cards.card("Probe")
        tab.insert_module(card, after=tab.style_group)
        try:
            layout = tab.properties_layout
            assert layout.indexOf(card) == layout.indexOf(tab.style_group) + 1
            titles = _titles(tab)
            assert titles[titles.index(tab.t("plan_group_style")) + 1] == "Probe"
            tab.canvas.select(("element", 0))
            assert card.isHidden()
            tab.canvas.select(None)
            assert not card.isHidden()
        finally:
            tab.modules = [(c, w) for c, w in tab.modules if c is not card]
            layout.removeWidget(card)
            card.deleteLater()
        tab.dirty = False


def test_the_fire_tab_s_right_pane_follows_the_selection_too():
    from domains import fire
    tab, here = _tab("FireTab")
    with project.using(here), _dialogs():
        source = fire.new_source("T1")
        source["walls"] = [{"id": "W1", "class": "EI 90", "points": [[0.0, 0.0], [200.0, 0.0]]}]
        tab.open_source(source, None, False)
        tab.show_plan_view()
        tab.canvas.select_ids([])
        assert not tab.has_selection()
        expected = [tab.t("plan_group_plan"), tab.t("fp_group_frame"), tab.t("plan_group_crop"), tab.t("plan_group_scale"),
                    tab.t("plan_group_snap"), tab.t("plan_group_style"), tab.superposition.card.title(), tab.t("fp_group_legend")]   # «Magnétisme» since v0.117   # «Superposition» after the sizes (WP-F)
        assert _titles(tab) == expected, _titles(tab)
        layout = tab.properties_layout
        assert layout.indexOf(tab.crop_group) < layout.indexOf(tab.scale_group)
        assert tab.calibrate_button.isEnabled(), "a plan with a frame of its own calibrates from the right pane"
        tab.canvas.select_ids(["W1"])
        assert tab.has_selection()
        assert _titles(tab) == [tab.t("fp_group_selection"), tab.t("plan_group_style")], _titles(tab)
        assert tab.own_card.isVisibleTo(tab.selection_group), "«Taille propre» is not shown with the selection"
        tab.canvas.select_ids([])
        assert _titles(tab) == expected
        # «Calibrer…» starts the canvas's calibration, the bar's tools all unchecked
        tab.calibrate_button.click()
        assert tab.canvas.tool == "calibrate" and tab.tool_group.checkedButton() is None
        tab.choose_tool("select")
        tab.crop_draw_button.click()
        assert tab.canvas.tool == "crop"
        tab.choose_tool("select")
        tab.dirty = False


# --- the left pane ---------------------------------------------------------------------------------

def test_the_left_pane_is_boxes_of_their_own_height_that_scroll_and_fold():
    """v0.117, the engineer (07.10.2026): «le volet de gauche doit pouvoir se scroll vers le haut et vers le bas» · «complètement réduit à l'aide d'une flèche en bas à gauche» · «les text-box du volet de gauche doivent pouvoir être … réduit vers le bas sans modifier la hauteur des autres». The splitter of v0.116 filled the height it was given -- nothing scrolled -- and a handle dragged took its height from the box beside it: each box has its own grip since (cards.SizedBox)."""
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QScrollArea
    import cards
    for kind in ("PlanTab", "FireTab"):
        tab, here = _tab(kind)
        with project.using(here), _dialogs():
            boxes = tab.left_boxes
            assert list(boxes) == ["documents", "plans", "entries", "sheets"], (kind, list(boxes))
            assert all(isinstance(box, cards.SizedBox) for box in boxes.values())
            assert boxes["documents"].isAncestorOf(tab.doc_list) and boxes["plans"].isAncestorOf(tab.list) and boxes["sheets"].isAncestorOf(tab.sheet_list)
            assert not hasattr(tab, "command_list"), "the «Commande Typst» row is the «Typst» view since v0.117"
            scroll = tab.left_scroll
            assert isinstance(scroll, QScrollArea) and tab.splitter.widget(0) is tab.left_pane and tab.left_pane.isAncestorOf(scroll), kind
            assert scroll.horizontalScrollBarPolicy() == Qt.ScrollBarPolicy.ScrollBarAlwaysOff
            for name, box in boxes.items():
                assert box.minimumSizeHint().height() > 40, (kind, name)
            # «Dessin» shows the plans and what the plan open holds: one box grown by 120 px, the other keeps its height
            tab.set_view("draw")
            plans, entries = boxes["plans"], boxes["entries"]
            entries.set_height(240)
            plans.set_height(200)
            before = entries.height_set
            plans.set_height(plans.height_set + 120)
            assert plans.height_set == 320 and entries.height_set == before, (kind, plans.height_set, entries.height_set)
            # taller than the window: the column scrolls rather than squeezing them
            scroll.resize(300, 200)
            scroll.widget().adjustSize()
            assert scroll.widget().minimumSizeHint().height() > 200, kind
            # never below what a box's content needs
            plans.set_height(5)
            assert plans.height_set >= plans.least_height() > 40, (kind, plans.height_set)
            # the heights and the fold travel through a rebuild of the window
            plans.set_height(330)
            tab.set_left_folded(True)
            assert not scroll.isVisible() or not tab.isVisible(), kind
            assert tab.left_pane.maximumWidth() < 60, (kind, tab.left_pane.maximumWidth())
            state = tab.view_state()
            assert state["left_boxes"]["plans"] == 330 and state["left_folded"], (kind, state["left_boxes"])
            tab.set_left_folded(False)
            assert tab.left_pane.maximumWidth() > 1000, kind
            plans.set_height(None)
            tab.restore(state)
            assert boxes["plans"].height_set == 330 and tab.left_folded, kind
            tab.set_left_folded(False)
            assert tab.left_fold.toolTip() == tab.t("pane_collapse"), kind
            tab.dirty = False


def test_the_list_of_plans_is_named_for_its_kind_in_three_languages():
    import fire_tab
    import plan_tab
    assert {lang: plan_tab.STRINGS[lang]["plan_list"] for lang in ("fr", "de", "en")} == {
        "fr": "Plans de position", "de": "Positionspläne", "en": "Position plans"}
    assert {lang: fire_tab.STRINGS[lang]["fp_list"] for lang in ("fr", "de", "en")} == {
        "fr": "Plans de protection incendie", "de": "Brandschutzpläne", "en": "Fire protection plans"}
    from PySide6.QtWidgets import QLabel
    for kind, key in (("PlanTab", "plan_list"), ("FireTab", "fp_list")):
        tab, _here = _tab(kind)
        texts = [label.text() for label in tab.left_boxes["plans"].findChildren(QLabel)]
        assert tab.t(key) in texts, (kind, texts)



def test_the_grip_is_dragged_the_pane_scrolls_and_the_arrow_folds_it_back_to_its_width():
    """REQ-004, REQ-005, UI-006 on a window shown: a grip dragged 120 px down with the pointer grows its box by 120 px and leaves the other its height, the column then scrolls, and a click on the arrow folds the pane to it and a second gives back the width it had."""
    from PySide6.QtCore import QPoint, Qt
    from PySide6.QtTest import QTest
    for kind in ("PlanTab", "FireTab"):
        tab, here = _tab(kind)
        window = _STATE["window"]
        with project.using(here), _dialogs():
            window.resize(1400, 520)
            window.show()
            window.tab_widget.setCurrentWidget(tab)
            tab.set_view("draw")
            _STATE["app"].processEvents()
            plans, entries = tab.left_boxes["plans"], tab.left_boxes["entries"]
            plans.set_height(220)
            entries.set_height(260)
            _STATE["app"].processEvents()
            other = entries.height()
            grip = plans.grip
            start = QPoint(grip.width() // 2, grip.height() // 2)
            QTest.mousePress(grip, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, start)
            QTest.mouseMove(grip, start + QPoint(0, 120))
            QTest.mouseRelease(grip, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, start + QPoint(0, 120))
            _STATE["app"].processEvents()
            assert plans.height_set == 340 and plans.height() == 340, (kind, plans.height_set, plans.height())
            assert entries.height() == other, (kind, entries.height(), other)
            assert tab.left_scroll.verticalScrollBar().maximum() > 0, f"{kind}: boxes taller than the window and nothing scrolls"
            width = tab.left_pane.width()
            QTest.mouseClick(tab.left_fold, Qt.MouseButton.LeftButton)
            _STATE["app"].processEvents()
            assert tab.left_folded and tab.left_pane.width() <= tab.left_fold.sizeHint().width() + 8 and not tab.left_scroll.isVisible(), (kind, tab.left_pane.width())   # hidden with the pane's content since issue #10 (chrome.FoldablePane)
            QTest.mouseClick(tab.left_fold, Qt.MouseButton.LeftButton)
            _STATE["app"].processEvents()
            assert not tab.left_folded and abs(tab.left_pane.width() - width) <= 2, (kind, tab.left_pane.width(), width)
            plans.set_height(None)
            entries.set_height(None)
            window.hide()
            tab.dirty = False
