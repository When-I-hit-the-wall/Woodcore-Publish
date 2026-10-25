"""The 3D model's widget (calc/tools/calc_blocks.py `Model3D`; spec 2026-10-23-onglet-vent-briques, ARCH-007, UI-008, UI-009, UI-014, UI-018), on the invented domain's box (tests/fake_domain.py `box`): no word of a domain.

What is held: the block draws its scene; a drag turns it, the wheel zooms it, bounded, the view buttons set it square, the direction's slider moves φ, a result's direction and sign are chosen -- each in the view the context holds by the block's key, shared by its bodies; a face hovered is an element hovered, and a key lit draws its face through; pinned, its window takes the window's size; the buttons wrap where the widget narrows.
"""

TIER = "fast"  # tests/run_tests.py --fast

import test_calc_tab_base as base


def _show(tab):
    """The window shown, the tab and its section of blocks with it: a scene is built only for a widget shown (ARCH-007)."""
    window = tab.window()
    window.show()
    if hasattr(window, "show_tab"):
        window.show_tab(tab)
    elif hasattr(window, "stack"):
        window.stack.setCurrentWidget(tab)
    base._form().sections["blocks"].set_folded(False, save=False)


def _model():
    base._tab()
    return base._form().blocks["model"].body


def test_the_block_draws_its_scene_and_a_drag_turns_it_and_the_wheel_zooms_it():
    from PySide6.QtCore import QPoint, QPointF, Qt
    from PySide6.QtGui import QMouseEvent, QWheelEvent
    tab = base._tab()
    model = _model()
    base._form().sections["blocks"].set_folded(False, save=False)
    _show(tab)
    model.canvas.resize(400, 300)
    model.canvas.grab()
    assert any(it["kind"] == "polygon" and it["key"] == "front" for it in model.canvas.items)
    state = tab.ctx.view_state("model")
    yaw = state["yaw"]
    press = QMouseEvent(QMouseEvent.Type.MouseButtonPress, QPointF(100, 100), QPointF(100, 100), Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
    move = QMouseEvent(QMouseEvent.Type.MouseMove, QPointF(140, 100), QPointF(140, 100), Qt.MouseButton.NoButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
    model.canvas.mousePressEvent(press)
    model.canvas.mouseMoveEvent(move)
    assert state["yaw"] == yaw + 20, "dragged 40 px: turned 20°"
    for _ in range(40):
        model.zoom_by(1.15)
    model.canvas.grab()
    from domains import model3d
    top = state["zoom"]
    assert top <= model3d.projector(base.fake_domain_box(), model3d.View(width=400, height=300, zoom=1000)).zoom_max + 1e-9
    wheel = QWheelEvent(QPointF(10, 10), QPointF(10, 10), QPoint(0, 0), QPoint(0, -120), Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier, Qt.ScrollPhase.NoScrollPhase, False)
    model.canvas.wheelEvent(wheel)
    assert state["zoom"] < top
    tab.window().hide()


def test_the_views_the_slider_and_a_result_s_buttons_set_the_context_s_view():
    tab = base._tab()
    model = _model()
    state = tab.ctx.view_state("model")
    model.view_buttons["Front"].click()
    assert (state["yaw"], state["pitch"]) == (-90.0, 0.0)
    model.slider.setValue(370 % 361)
    assert state["phi"] == 9.0
    model.direction_buttons["90°"].click()
    assert state["direction"] == "90°" and model.direction_buttons["90°"].isChecked() and not model.direction_buttons["all"].isChecked()
    model.sign_buttons["-"].click()
    assert state["sign"] == "-" and not model.sign_buttons["+"].isChecked()
    model.set_view(phi=360.0)
    assert state["phi"] == 0.0, "360° is 0°"


def test_a_face_hovered_is_an_element_and_a_key_lit_draws_it_through():
    tab = base._tab()
    model = _model()
    seen = []
    tab.ctx.litKeys.connect(lambda lit, _e: seen.append(set(lit)))
    model.hovered("front")
    assert "face:front" in seen[-1]
    model.hovered(None)
    tab.ctx.litKeys.emit({"face:side"}, set())
    model.canvas.resize(400, 300)
    _show(tab)
    model.view_buttons["Front"].click()
    model.canvas.grab()
    assert any(it.get("lit") and it["key"] == "side" for it in model.canvas.items), "the side, edge on in the front view, lit through"
    tab.ctx.litKeys.emit(set(), set())
    tab.window().hide()


def test_pinned_its_window_takes_the_window_s_size_and_the_buttons_wrap():
    tab = base._tab()
    model = _model()
    pane = base._modules().pane
    base._form().blocks["model"].pin.click()
    module = pane.modules["b:model"]
    assert module.spec.fills_window
    window = pane.open_window("b:model")
    window.resize(900, 700)
    window.layout().activate()
    assert window.body.width() > 800
    window.close()
    pane.remove("b:model")
    model.controls.resize(900, 60)
    model.row.arrange()
    wide = model.row.rows()
    model.controls.resize(200, 60)
    model.row.arrange()
    assert model.row.rows() > wide, "the buttons wrap where the widget narrows (UI-018)"
