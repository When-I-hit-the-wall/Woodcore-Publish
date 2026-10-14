"""*Ajuster* in the static models tab: the view it opens on (docs/ui/window.md §10quater).

The engineer clicked it on a 0.55 kN bench frame, 0.5 m across, and got a view twelve metres wide with the model forty-two pixels of it -- a twenty-fifth of the drawing area. He put it down to the dimension he had just added, which is worth recording because it was not that at all: measured with and without the dimension, the fit came out identical to the centimetre, and it is identical for every model smaller than four metres.

What did it was the floor. `fit()` held every model to a view of at least four metres and did it by growing the rect to a **square** of that side; `fitInView` keeps the aspect ratio, so a four-metre square letterboxed into a drawing area 1070 x 400 px is fitted to its height and the width blows out to 12.4 m. The floor was written for a model with nothing in it -- "so a first point lands on a grid one can read rather than on a millimetre" -- and a model that has been drawn does not need it: MAX_ZOOM is absolute and holds the top end on its own. So it applies where its own comment says, to a model whose points span nothing, and nowhere else (v0.64.1).

Nothing in this folder touched the canvas before this file, so neither the defect nor its repair would have been named by a test run.

⚠️ Skipped where PySide6 is not installed: a machine that only builds the report is a legitimate machine. Every canvas here is built off-screen -- a test run must never open a window.
"""

import os
import sys

import conftest
from conftest import ROOT, Skip

WIDE = (1070, 400)      # the drawing area as the tab lays it out with the lists under it
TALL = (1070, 700)      # and with them folded away


def _qt():
    """Qt, off-screen, with calc/tools on the path -- or a Skip."""
    path = str(ROOT / "calc" / "tools")
    if path not in sys.path:
        sys.path.insert(0, path)
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:
        raise Skip(f"PySide6 is not installed ({exc})")
    QApplication.instance() or QApplication([])
    import statics_canvas
    return statics_canvas


def _fitted(source, size=WIDE):
    """One canvas of `size`, holding `source`, with *Ajuster* pressed: (the view in metres, the figure's own box, the zoom)."""
    sc = _qt()
    from PySide6.QtWidgets import QApplication
    canvas = sc.StaticsCanvas()
    canvas.resize(*size)
    canvas.show()
    canvas.set_source(source, {})
    canvas.fit()
    QApplication.instance().processEvents()
    view = canvas.mapToScene(canvas.viewport().rect()).boundingRect()
    figure = canvas.overlay.boundingRect()
    zoom = canvas.scale_px()
    canvas.close()
    return view, figure, zoom


def _model():
    from domains import statics as model
    return model


def _bench(span=0.5):
    """The shape the engineer met: one bar, one support, one load, half a metre long and flat."""
    model = _model()
    s = model.new_source("Bank")
    s["points"] = [{"id": "P1", "x": 0.0, "z": 0.0}, {"id": "P2", "x": span, "z": 0.0}]
    s["members"] = [{"id": "B1", "kind": "bar", "p1": "P1", "p2": "P2"}]
    s["supports"] = [{"id": "A1", "point": "P2", "type": "fixed", "angle": -90}]
    s["point_loads"] = [{"id": "F1", "point": "P1", "reference": "B1", "along": "0",
                         "direction": "vertical", "show": "value",
                         "magnitude": {"value": 0.55, "unit": "kN"}}]
    return s


def _frame(span):
    model = _model()
    s = model.new_source("R")
    s["points"] = [{"id": "P1", "x": 0.0, "z": 0.0}, {"id": "P2", "x": 0.0, "z": -0.6 * span},
                   {"id": "P3", "x": span, "z": -0.6 * span}, {"id": "P4", "x": span, "z": 0.0}]
    s["members"] = [{"id": "B1", "kind": "bar", "p1": "P1", "p2": "P2"},
                    {"id": "B2", "kind": "bar", "p1": "P2", "p2": "P3"},
                    {"id": "B3", "kind": "bar", "p1": "P3", "p2": "P4"}]
    return s


def _fill(view, figure):
    """How much of the view the figure takes along whichever direction it was fitted to."""
    return max(figure.width() / view.width(), figure.height() / view.height())


def test_a_model_smaller_than_the_floor_fills_the_view():
    """The defect itself: the bench took 5.6% of the width and 42 px. It is the model that is fitted now, not a four-metre square."""
    for size in (WIDE, TALL):
        view, figure, zoom = _fitted(_bench(), size)
        assert _fill(view, figure) > 0.8, f"{size}: the figure takes {_fill(view, figure):.0%} of the view"
        assert view.width() < 4.0, f"{size}: the view is {view.width():.2f} m wide for a 0.5 m model"
        assert 0.5 * zoom > 200, f"{size}: half a metre is {0.5 * zoom:.0f} px"


def test_a_model_with_nothing_in_it_opens_on_the_four_metre_grid():
    """What the floor was written for, and where it still applies: no point at all, or one, which alone has no extent to fit."""
    model = _model()
    one = model.new_source("Un")
    one["points"] = [{"id": "P1", "x": 0.0, "z": 0.0}]
    for name, source in (("empty", model.new_source("Vide")), ("one point", one)):
        view, _figure, _zoom = _fitted(source)
        assert min(view.width(), view.height()) >= 4.0, f"{name}: {view.width():.2f} x {view.height():.2f} m"


def test_a_lone_point_away_from_the_origin_is_still_in_view():
    """The floor is centred on the figure and not on the origin, or a first point put down at 5 m would open off-screen."""
    model = _model()
    s = model.new_source("Un")
    s["points"] = [{"id": "P1", "x": 5.0, "z": 3.0}]
    view, figure, _zoom = _fitted(s)
    assert view.contains(figure), f"the point at (5, 3) is outside {view}"


def test_a_model_the_floor_never_reached_is_fitted_as_it_was():
    """Everything four metres and over is untouched by the repair: the two frames below fitted to the same pixel before and after."""
    for span in (6.0, 30.0):
        for size in (WIDE, TALL):
            view, figure, _zoom = _fitted(_frame(span), size)
            assert _fill(view, figure) > 0.8, f"{span} m in {size}: {_fill(view, figure):.0%}"


def test_the_whole_figure_is_always_visible():
    """*Ajuster* means everything is on screen -- the load's arrow and the dimension's value included, which reach well past the last node."""
    model = _model()
    dimensioned = _bench()
    dimensioned["dimensions"] = [{"id": "D1", "kind": "horizontal", "from": {"point": "P1"},
                                  "to": {"point": "P2"}, "offset": 0.23}]
    sources = [model.new_source("Vide"), _bench(), dimensioned, _frame(6.0), _frame(30.0)]
    for source in sources:
        view, figure, _zoom = _fitted(source)
        assert view.contains(figure) or figure.isEmpty(), f"{source['id']}: {figure} is not inside {view}"


def test_a_dimension_is_part_of_what_is_fitted():
    """A dimension reaches below the bar it measures, so it makes the figure taller and the fit does stand back a little to hold it -- which is *Ajuster* doing its job, not the defect the engineer suspected.

    Under the floor it looked like the opposite: both figures were under four metres, both got the same square, and the fit was identical to the centimetre whether the dimension was there or not. That is what made it worth testing from this side.
    """
    bare = _bench()
    dimensioned = _bench()
    dimensioned["dimensions"] = [{"id": "D1", "kind": "horizontal", "from": {"point": "P1"},
                                  "to": {"point": "P2"}, "offset": 0.23}]
    _bare_view, bare_figure, _bare_zoom = _fitted(bare)
    view, figure, _zoom = _fitted(dimensioned)
    assert figure.height() > bare_figure.height(), "the dimension did not widen the figure at all"
    assert view.contains(figure), f"the dimension is cut off: {figure} is not inside {view}"
    assert _fill(view, figure) > 0.8, f"the fit stood back further than the dimension asked: {_fill(view, figure):.0%}"


def test_the_zoom_stays_inside_its_limits():
    """MAX_ZOOM is what holds the top end now that the floor does not, so a fit must never walk past it."""
    sc = _qt()
    model = _model()
    tiny = model.new_source("Klein")
    tiny["points"] = [{"id": "P1", "x": 0.0, "z": 0.0}, {"id": "P2", "x": 0.05, "z": 0.0}]
    for source in (model.new_source("Vide"), tiny, _bench(), _frame(30.0)):
        _view, _figure, zoom = _fitted(source)
        assert sc.MIN_ZOOM <= zoom <= sc.MAX_ZOOM, f"{source['id']}: {zoom:.1f} px/m"
