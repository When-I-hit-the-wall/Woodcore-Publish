"""The superposition of another plan (v0.116, WP-F; calc/domains/plan.py's `superposition`, calc/tools/plan_canvas.py, calc/tools/plan_superposition.py; docs/domain/position-plans.md §3.3sexies, docs/domain/fire-plans.md §3.3vicies, docs/ui/window.md §10quater): another plan of the same tab shown over the plan open, with or without its elements, as opaque as asked, in its colours, in grey or in one of five colours, aligned by two clicks -- a drawing aid, never printed or exported, nothing in it selectable.

The engineer, 06.10.2026: «superposer au plan un autre plan déjà existant avec ou sans les éléments … en transparence … ses couleurs normales ou le dessin en gris avec ses éléments en couleur ou le dessin et les éléments en gris ou … vert, bleu, jaune, rouge … rose … faire correspondre le point d'un plan au point d'un autre plan … deux clics … les éléments du plan rajouté … ne doivent pas pouvoir être sélectionnés». The window is built once, off-screen, on a copy of the example project; every dialog is stubbed.
"""

import contextlib
import copy
import json
import os
import sys

import conftest
from conftest import ROOT, Skip

import project
import validation
from domains import fire
from domains import plan

_STATE = {}


# --- the field ---------------------------------------------------------------------------------

def _sourced(_none=None, **spec):
    """Plan PA, 100 x 100, a column at (20, 20) -- with a superposition where `spec` gives one (`_sourced(None)`: none)."""
    source = plan.new_source("PA")
    source["sheet"] = {"width": 100.0, "height": 100.0}
    source["elements"] = [{"type": "S", "label": "S001", "points": [[20.0, 20.0]]}]
    if spec:
        source["superposition"] = spec
    return source


def _refused(source):
    try:
        plan.check_source(source, "PA.json")
    except validation.ValidationError as exc:
        return str(exc)
    return None


def test_the_field_is_checked_and_a_plan_that_is_gone_is_no_error():
    good = _sourced(plan="PB", elements=False, opacity=0.4, colour="pink", tint_elements=True, offset=[12.5, -3])
    assert _refused(good) is None
    assert _refused(_sourced(plan="GONE")) is None, "a plan archived since is said in the window, never refused"
    for bad, words in ((dict(plan="PB", colour="purple"), "colour"), (dict(plan="PB", opacity=0.0), "opacity"),
                       (dict(plan="PB", opacity=1.5), "opacity"), (dict(plan="PA"), "the plan itself"),
                       (dict(plan="P B"), "superposition.plan"), (dict(plan="PB", offset=[1]), "offset"),
                       (dict(plan="PB", elements="yes"), "elements")):
        message = _refused(_sourced(**bad))
        assert message and words in message, (bad, message)
    # filled with its defaults where it states none, and none where it names no plan
    assert plan.superposition_of(_sourced(plan="PB")) == {"plan": "PB", **plan.SUPERPOSITION_DEFAULT}
    assert plan.superposition_of(_sourced(plan="")) is None and plan.superposition_of(plan.new_source("X")) is None
    # a fire plan carries the same field, checked by the same rules
    fsource = fire.new_source("F1")
    fsource["sheet"] = {"width": 100.0, "height": 100.0}
    fsource["superposition"] = {"plan": "F2", "colour": "blue"}
    fire.check_source(fsource, "F1.json")
    fsource["superposition"]["colour"] = "orange"
    try:
        fire.check_source(fsource, "F1.json")
    except validation.ValidationError as exc:
        assert "colour" in str(exc)
    else:
        raise AssertionError("a fire plan's superposition of an unknown colour was let through")


def test_the_field_reaches_no_export():
    bare = _sourced(None)
    stated = copy.deepcopy(bare)
    stated["superposition"] = {"plan": "PB", "offset": [3, 4], "colour": "red"}
    assert plan.build_record(stated, (100, 100)) == plan.build_record(bare, (100, 100))
    assert "superposition" not in json.dumps(plan.build_record(stated, (100, 100)))


def test_the_transform_scales_by_the_two_calibrations_and_defaults_to_the_crops_corners():
    mine = {"sheet": {"width": 1000, "height": 700}, "crop": {"x": 0, "y": 0, "w": 800, "h": 600},
            "scale": {"mode": "calibration", "points": [[0, 0], [100, 0]], "length_m": 1}}
    theirs = {"sheet": {"width": 500, "height": 350}, "crop": {"x": 10, "y": 20, "w": 400, "h": 300},
              "scale": {"mode": "calibration", "points": [[0, 0], [50, 0]], "length_m": 1}}
    assert plan.superposition_scale(mine, theirs) == (2.0, True)
    assert plan.superposition_default_offset(mine, theirs) == [-20, -40]
    assert plan.superposition_transform({"offset": [5, 6]}, mine, theirs) == (2.0, 5.0, 6.0)
    # without a scale on either, sheet units as they are
    unscaled = {k: v for k, v in theirs.items() if k != "scale"}
    assert plan.superposition_scale(mine, unscaled) == (1.0, False)
    assert plan.superposition_transform({}, mine, unscaled) == (1.0, -10.0, -20.0)


def test_tinting_keeps_white_and_makes_every_other_colour_the_ink():
    _qt()
    import plan_canvas
    svg = '<svg viewBox="0 0 1 1"><rect fill="#ffffff" stroke="#2E5FAA"/><path fill="none" stroke="#000"/><text>T</text></svg>'
    out = plan_canvas.tint_svg(svg, "#d32f2f")
    assert 'fill="#ffffff"' in out and 'fill="none"' in out and 'stroke="#2E5FAA"' not in out and out.count('"#d32f2f"') == 3
    from PySide6.QtGui import QColor, QImage
    image = QImage(2, 1, QImage.Format.Format_ARGB32_Premultiplied)
    image.setPixelColor(0, 0, QColor("#000000"))
    image.setPixelColor(1, 0, QColor("#ffffff"))
    red = plan_canvas.tint_image(image, "#d32f2f")
    assert red.pixelColor(0, 0).name() == "#d32f2f" and red.pixelColor(1, 0).name() == "#ffffff"
    transparent = QImage(1, 1, QImage.Format.Format_ARGB32_Premultiplied)
    transparent.fill(QColor(0, 0, 0, 0))
    assert plan_canvas.tint_image(transparent, "#1f6fd1").pixelColor(0, 0).name() == "#ffffff", "a transparent render is paper, not ink"


# --- the window --------------------------------------------------------------------------------

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
def _dialogs():
    from PySide6.QtWidgets import QFileDialog, QInputDialog, QMessageBox
    stubs = {
        (QMessageBox, "warning"): staticmethod(lambda *a, **k: QMessageBox.StandardButton.Ok),
        (QMessageBox, "critical"): staticmethod(lambda *a, **k: QMessageBox.StandardButton.Ok),
        (QMessageBox, "information"): staticmethod(lambda *a, **k: QMessageBox.StandardButton.Ok),
        (QMessageBox, "question"): staticmethod(lambda *a, **k: QMessageBox.StandardButton.Yes if len(a) < 4 else QMessageBox.StandardButton.Discard),
        (QFileDialog, "getOpenFileName"): staticmethod(lambda *a, **k: ("", "")),
        (QInputDialog, "getDouble"): staticmethod(lambda *a, **k: (2.5, True)),
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
        here = conftest.project_copy("plan_overlay_v0116")
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


def _write_plan(here, source):
    path = here.plans_dir / f"{source['id']}.json"
    path.write_text(json.dumps(source, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def _black_png(here, name="superposed.png", size=100):
    from PySide6.QtGui import QColor, QImage
    image = QImage(size, size, QImage.Format.Format_ARGB32)
    image.fill(QColor("#000000"))
    path = here.root / name
    image.save(str(path))
    return name


def _open(tab, source):
    tab.open_source(source, None, False)
    tab.show_plan_view()
    tab.canvas.select(None)
    tab.dirty = False


def _pixel(canvas, x, y):
    """The colour the canvas's scene paints at sheet point (x, y)."""
    from PySide6.QtCore import QRectF
    from PySide6.QtGui import QColor, QImage, QPainter
    image = QImage(4, 4, QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(QColor("#ff00ff"))
    painter = QPainter(image)
    canvas.scene().render(painter, QRectF(0, 0, 4, 4), QRectF(x - 0.5, y - 0.5, 1, 1))
    painter.end()
    return image.pixelColor(2, 2)


def test_the_module_shows_with_nothing_selected_and_its_controls_write_the_field_one_step_each():
    tab, here = _tab("PlanTab")
    with project.using(here), _dialogs():
        other = _sourced(None)
        other["id"] = "PB"
        _write_plan(here, other)
        module = tab.superposition
        layout = tab.properties_layout
        assert layout.indexOf(module.card) == layout.indexOf(tab.style_group) + 1, "«Superposition» stands right after «Taille des symboles»"
        _open(tab, _sourced(None))
        assert not module.card.isHidden()
        assert module.plan_combo.findData("PB") > 0 and module.plan_combo.findData("PA") < 0, "the plans of the tab are offered, the plan open is not"
        assert not module.colour_combo.isEnabled() and not module.align_button.isEnabled()
        tab.canvas.select(("element", 0))
        assert module.card.isHidden(), "an object selected hides the plan's modules, «Superposition» among them"
        tab.canvas.select(None)
        assert not module.card.isHidden()

        steps = len(tab.undo_stack)
        module.plan_combo.setCurrentIndex(module.plan_combo.findData("PB"))
        assert tab.source["superposition"]["plan"] == "PB" and tab.source["superposition"]["offset"] == [0, 0]
        assert len(tab.undo_stack) == steps + 1 and tab.dirty
        assert tab.canvas.superposition_state == {"plan": "PB", "missing": False, "scaled": False, "scale": 1.0, "offset": [0.0, 0.0]}
        assert module.state_note.text() == module.w("unscaled")
        for widget, value, key, expected in ((module.colour_combo, "grey", "colour", "grey"), (module.elements_box, False, "elements", False),
                                             (module.tint_box, True, "tint_elements", True)):
            before = len(tab.undo_stack)
            if isinstance(value, bool):
                widget.setChecked(value)
            else:
                widget.setCurrentIndex(widget.findData(value))
            assert tab.source["superposition"][key] == expected, key
            assert len(tab.undo_stack) == before + 1, key
        # a drag of the opacity is one step of «Annuler»
        before = len(tab.undo_stack)
        slider = module.opacity.slider
        tab.on_slider_pressed()
        for value in (40, 35, 30):
            slider.setValue(value)
        tab.on_slider_released()
        assert tab.source["superposition"]["opacity"] == 0.3 and len(tab.undo_stack) == before + 1
        assert tab.canvas.sup_group.opacity() == 0.3
        tab.undo()
        assert tab.source["superposition"]["opacity"] == 0.5 and module.opacity.slider.value() == 50, "undone, and the card follows"
        # none: the field goes
        module.plan_combo.setCurrentIndex(0)
        assert "superposition" not in tab.source and not tab.canvas.sup_group.isVisible()
        tab.dirty = False


def test_a_plan_that_is_gone_shows_nothing_and_says_so():
    tab, here = _tab("PlanTab")
    with project.using(here), _dialogs():
        _open(tab, _sourced(plan="GONE", colour="red"))
        assert tab.canvas.superposition_state == {"plan": "GONE", "missing": True}
        assert not tab.canvas.sup_group.isVisible()
        module = tab.superposition
        assert module.state_note.text() == module.w("missing", plan="GONE") and not module.align_button.isEnabled()
        assert module.plan_combo.currentData() == "GONE"
        tab.dirty = False


def test_the_colours_tint_the_background_and_the_opacity_lets_the_plan_through():
    tab, here = _tab("PlanTab")
    with project.using(here), _dialogs():
        other = _sourced(None)
        other["id"] = "PB"
        other["elements"] = []
        other["background"] = {"file": _black_png(here), "page": 1, "opacity": 0.45}
        _write_plan(here, other)
        _open(tab, _sourced(plan="PB", colour="normal", opacity=1.0, elements=False))
        canvas = tab.canvas
        assert canvas.sup_group.isVisible()
        black = _pixel(canvas, 50, 50)
        assert max(black.red(), black.green(), black.blue()) < 40, black.name()
        for colour, check in (("red", lambda c: c.red() > 180 and c.green() < 90 and c.blue() < 90),
                              ("grey", lambda c: abs(c.red() - c.green()) < 8 and abs(c.green() - c.blue()) < 8 and 110 < c.red() < 170),
                              ("blue", lambda c: c.blue() > 170 and c.red() < 80),
                              ("pink", lambda c: c.red() > 200 and c.blue() > 130 and c.green() < 120)):
            tab.source["superposition"]["colour"] = colour
            canvas.invalidate()
            seen = _pixel(canvas, 50, 50)
            assert check(seen), (colour, seen.name())
        tab.source["superposition"].update(colour="normal", opacity=0.5)
        canvas.invalidate()
        half = _pixel(canvas, 50, 50)
        assert 100 < half.red() < 160, half.name()
        tab.dirty = False


def test_the_elements_are_shown_or_not_tinted_or_not_and_never_selected():
    tab, here = _tab("PlanTab")
    with project.using(here), _dialogs():
        other = _sourced(None)
        other["id"] = "PB"
        other["elements"] = [{"type": "S", "label": "S001", "points": [[70.0, 70.0]]}]
        _write_plan(here, other)
        _open(tab, _sourced(plan="PB", elements=True, colour="green", tint_elements=False))
        canvas = tab.canvas
        assert canvas.sup_elements.isVisible() and canvas.sup_points == [(70.0, 70.0)]
        assert "#2e9d4a" not in canvas.superposition_svg(other, other).lower()
        tab.source["superposition"]["tint_elements"] = True
        canvas.invalidate()
        assert "#2e9d4a" in json.loads(canvas._sup_svg_key)[3].lower(), "the elements take the colour too"
        # its column is no object of this plan: a click on it selects nothing, a click on this plan's column selects it
        canvas.set_tool("select")
        canvas.press_select((70.0, 70.0))
        assert canvas.selection is None
        canvas.press_select((20.0, 20.0))
        assert canvas.selection == ("element", 0)
        canvas.drag = None
        canvas.select(None)
        # its points are snap targets behind «Accrocher aux éléments»
        canvas.invalidate()
        assert (70.0, 70.0) in [p for _prio, kind, p in canvas.snap_index().points if kind == "vertex"]
        canvas.snap_elements = False
        canvas.invalidate()
        assert (70.0, 70.0) not in [tuple(p) for _prio, _kind, p in canvas.snap_index().points]
        canvas.snap_elements = True
        tab.source["superposition"]["elements"] = False
        canvas.invalidate()
        assert not canvas.sup_elements.isVisible() and canvas.sup_points == []
        tab.dirty = False


def test_aligner_takes_a_point_of_the_superposed_plan_then_the_matching_point_and_moves_the_offset():
    tab, here = _tab("PlanTab")
    with project.using(here), _dialogs():
        other = _sourced(None)
        other["id"] = "PB"
        other["sheet"] = {"width": 500.0, "height": 350.0}
        other["crop"] = {"x": 10.0, "y": 20.0, "w": 400.0, "h": 300.0}
        other["scale"] = {"mode": "calibration", "points": [[0, 0], [50, 0]], "length_m": 1}
        other["elements"] = [{"type": "S", "label": "S001", "points": [[60.0, 70.0]]}]
        _write_plan(here, other)
        mine = _sourced(None)
        mine["sheet"] = {"width": 1000.0, "height": 700.0}
        mine["crop"] = {"x": 0.0, "y": 0.0, "w": 800.0, "h": 600.0}
        mine["scale"] = {"mode": "calibration", "points": [[0, 0], [100, 0]], "length_m": 1}
        mine["elements"] = [{"type": "S", "label": "S001", "points": [[150.0, 130.0]]}]
        _open(tab, mine)
        module = tab.superposition
        module.plan_combo.setCurrentIndex(module.plan_combo.findData("PB"))
        canvas = tab.canvas
        assert tab.source["superposition"]["offset"] == [-20, -40]
        assert canvas.superposition_state["scale"] == 2.0 and canvas.sup_points == [(100.0, 100.0)]
        assert module.align_button.isEnabled()
        module.align_button.click()
        assert canvas.tool == "superpose-align" and tab.hint.text() == module.w("align_1")
        steps = len(tab.undo_stack)
        canvas._left_click((100.4, 99.7), False)
        assert canvas.align_from == (100.0, 100.0) and tab.hint.text() == module.w("align_2")
        canvas._left_click((150.3, 130.2), False)
        assert tab.source["superposition"]["offset"] == [30, -10]
        assert len(tab.undo_stack) == steps + 1
        assert canvas.sup_points == [(150.0, 130.0)], "the superposed column now lies on this plan's"
        assert canvas.tool == "select", "the tool hands back the selection once done"
        tab.undo()
        assert tab.source["superposition"]["offset"] == [-20, -40]
        tab.redo()
        module.reset_button.click()
        assert tab.source["superposition"]["offset"] == [-20, -40]
        tab.dirty = False


def test_the_fire_tab_has_the_module_too():
    tab, here = _tab("FireTab")
    with project.using(here), _dialogs():
        module = tab.superposition
        layout = tab.properties_layout
        assert layout.indexOf(module.card) == layout.indexOf(tab.style_group) + 1
        mine = fire.new_source("F9")
        mine["sheet"] = {"width": 100.0, "height": 100.0}
        tab.open_source(mine, None, False)
        tab.show_plan_view()
        tab.canvas.select_ids([])
        tab.dirty = False
        others = [module.plan_combo.itemData(i) for i in range(module.plan_combo.count())]
        assert {"Pavillon-EG", "Treppenhaus"} <= set(others), others
        module.plan_combo.setCurrentIndex(module.plan_combo.findData("Treppenhaus"))
        assert tab.source["superposition"]["plan"] == "Treppenhaus"
        assert tab.canvas.superposition_state and not tab.canvas.superposition_state["missing"]
        fire.check_source(tab.source, "F9.json")
        module.align_button.click()
        assert tab.canvas.tool == "superpose-align"
        tab.choose_tool("select")
        tab.dirty = False


def test_the_words_exist_in_three_languages():
    import plan_superposition
    keys = set(plan_superposition.WORDS["fr"])
    for lang in ("de", "en"):
        assert set(plan_superposition.WORDS[lang]) == keys, lang
    assert not any("ß" in text for text in plan_superposition.WORDS["de"].values())
    for colour in plan.SUPERPOSITION_COLOURS:
        assert f"colour_{colour}" in keys


def test_a_load_levels_ends_are_snap_points_but_not_for_its_own_drag():
    """WP-C's follow-up: a section's load transfer level's two ends are snap points, as a storey line's are -- but not for the level being dragged."""
    tab, here = _tab("PlanTab")
    with project.using(here), _dialogs():
        section = _sourced(None)
        section.update(role="section", plan_type="section", elements=[])
        section["load_levels"] = [{"storey": "EG", "points": [[10.0, 80.0], [90.0, 80.0]]}]
        _open(tab, section)
        canvas = tab.canvas
        vertices = [tuple(p) for _prio, kind, p in canvas.snap_index().points if kind == "vertex"]
        assert (10.0, 80.0) in vertices and (90.0, 80.0) in vertices
        vertices = [tuple(p) for _prio, kind, p in canvas.snap_index(exclude_storey=("load-level", 0)).points if kind == "vertex"]
        assert (10.0, 80.0) not in vertices
        tab.dirty = False
