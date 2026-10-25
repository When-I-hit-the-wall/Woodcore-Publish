"""The list of the «Variables» tab (calc/tools/variables_list.py; spec 2026-10-24-onglet-variables-groupes, UI-006 to UI-009, ARCH-007).

⚠️ **The widths never follow the list** (UI-007): two searches, the same widths; dragged, kept; a double click on
the edge of a heading gives the width of the start back.

⚠️ **A title line is no variable** (UI-009, ARCH-007): a click on it does nothing, a range never takes it, and the
list -- a table, not a tree -- cannot be folded.
"""

TIER = "fast"  # tests/run_tests.py --fast

import sys

from conftest import ROOT, Skip

sys.path.insert(0, str(ROOT / "calc" / "tools")) if str(ROOT / "calc" / "tools") not in sys.path else None

import variable_sources as sources
import variables as model


def _app():
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:
        raise Skip(f"PySide6 is not installed ({exc})")
    return QApplication.instance() or QApplication([])


def _var(key, value, unit, domain):
    return model.Variable(key=key, domain=domain, value=value, unit=unit, symbol=key, label=f"label of {key} " * 6)


def _groups(words=None):
    sl = sources.Domain(name="snow-load · SL", origin="export", address=("snow-load", "SL"), results=("q_k1",),
                        variables=[_var("s_k", 1.394, "kN/m²", "snow-load · SL"), _var("q_k1", 1.115, "kN/m²", "snow-load · SL")])
    a1 = sources.Domain(name="live-load · A1", origin="export", address=("live-load", "A1"), results=("q_k",),
                        variables=[_var("q_k", 2.0, "kN/m²", "live-load · A1"), _var("Q_k", 2.0, "kN", "live-load · A1"), _var("psi_0", 0.7, "", "live-load · A1")])
    groups = [(sl, list(sl.variables)), (a1, list(a1.variables))]
    if words:
        groups = [(d, [v for v in vs if words in v.key]) for d, vs in groups]
        groups = [(d, vs) for d, vs in groups if vs]
    return groups


def _describe(domain, count):
    return {"case": domain.address[1], "badge": "export", "kind": "export", "rest": "Neige", "count": count, "tip": ""}


def _list():
    _app()
    from variables_list import VariablesList
    view = VariablesList(lambda key, **v: key)
    view.resize(900, 400)
    view.set_groups(_groups(), _describe)
    return view


def test_the_widths_start_at_their_default_and_never_follow_a_search():
    import theme
    from variables_list import DEFAULT_WIDTHS, SYMBOL, UNIT, VALUE
    view = _list()
    assert view.widths() == {"symbol": theme.scaled(DEFAULT_WIDTHS[SYMBOL]), "value": theme.scaled(DEFAULT_WIDTHS[VALUE]), "unit": theme.scaled(DEFAULT_WIDTHS[UNIT])}
    first = view.widths()
    view.set_groups(_groups("q"), _describe)
    view.set_groups(_groups("psi"), _describe)
    assert view.widths() == first


def test_a_width_dragged_is_kept_and_a_double_click_on_its_edge_gives_the_default_back():
    import theme
    from PySide6.QtCore import QEvent, QPointF, Qt
    from PySide6.QtGui import QMouseEvent
    from PySide6.QtWidgets import QApplication
    from variables_list import DEFAULT_WIDTHS, SYMBOL
    view = _list()
    view.header.resizeSection(SYMBOL, 200)
    kept = view.widths()
    assert kept["symbol"] == 200
    other = _list()
    other.set_widths(kept)
    assert other.widths() == kept
    other.set_widths({})            # a state of before: no widths, the defaults
    assert other.widths()["symbol"] == theme.scaled(DEFAULT_WIDTHS[SYMBOL])
    view.show()
    edge = view.header.sectionViewportPosition(SYMBOL) + view.header.sectionSize(SYMBOL)
    event = QMouseEvent(QEvent.Type.MouseButtonDblClick, QPointF(edge, 5), QPointF(edge, 5), Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
    QApplication.sendEvent(view.header.viewport(), event)
    assert view.widths()["symbol"] == theme.scaled(DEFAULT_WIDTHS[SYMBOL])
    view.hide()


def test_a_result_is_framed_in_the_theme_s_accent_and_no_other_value():
    import theme
    from variables_list import VALUE
    view = _list()
    model_ = view.list_model
    rows = {model_.key(r)[2]: r for r in range(model_.rowCount()) if model_.key(r) is not None}
    saved = theme._state["scheme"]
    try:
        for scheme in ("light", "dark"):
            theme._state["scheme"] = scheme
            framed = view.delegate.frame_colour(model_.index(rows["q_k1"], VALUE))
            assert framed is not None and framed.name() == theme.tokens(scheme)["accent"], scheme
            assert view.delegate.frame_colour(model_.index(rows["s_k"], VALUE)) is None
    finally:
        theme._state["scheme"] = saved
    assert all("★" not in (model_.data(model_.index(r, c)) or "") for r in range(model_.rowCount()) for c in range(5))


def test_the_boxes_follow_every_gesture_and_a_title_is_never_chosen():
    from PySide6.QtCore import Qt
    from variables_list import BOX, SYMBOL, TITLE
    view = _list()
    model_ = view.list_model
    titles = [r for r in range(model_.rowCount()) if model_.kind(r) == TITLE]
    rows = [r for r in range(model_.rowCount()) if model_.key(r) is not None]
    assert titles == [0, 3] and view.columnSpan(0, 0) == 5, "a title line spans the whole width"

    def boxes():
        return [r for r in rows if model_.data(model_.index(r, BOX), Qt.ItemDataRole.CheckStateRole) == Qt.CheckState.Checked]
    assert not view.gesture(titles[0], SYMBOL), "a click on a title does nothing"
    view.gesture(rows[0], SYMBOL)
    assert boxes() == [rows[0]]
    view.gesture(rows[3], SYMBOL, shift=True)
    assert boxes() == rows[:4], "a range across the two domains, the title skipped"
    assert view.selection.focus == model_.key(rows[3])
    view.gesture(rows[1], BOX)
    assert boxes() == [rows[0], rows[2], rows[3]], "the box takes one away"
    assert model_.data(model_.index(rows[0], SYMBOL), Qt.ItemDataRole.BackgroundRole) is not None, "a row chosen has its ground"
    view.toggle_all(True)
    assert boxes() == rows
    view.toggle_all(False)
    assert boxes() == []
    from PySide6.QtWidgets import QAbstractItemView, QTableView
    assert isinstance(view, QTableView) and view.selectionMode() == QAbstractItemView.SelectionMode.NoSelection, "no tree to fold, no selection of Qt's own"


def test_the_keyboard_follows_the_mouse():
    from PySide6.QtCore import QEvent, Qt
    from PySide6.QtGui import QKeyEvent
    from PySide6.QtWidgets import QApplication
    view = _list()
    model_ = view.list_model
    rows = [r for r in range(model_.rowCount()) if model_.key(r) is not None]

    def key(k, mods=Qt.KeyboardModifier.NoModifier):
        QApplication.sendEvent(view, QKeyEvent(QEvent.Type.KeyPress, k, mods))
    key(Qt.Key.Key_Down)
    key(Qt.Key.Key_Down)
    assert view.selection.keys(view.shown()) == [model_.key(rows[1])]
    key(Qt.Key.Key_Down, Qt.KeyboardModifier.ShiftModifier)
    assert view.selection.keys(view.shown()) == [model_.key(rows[1]), model_.key(rows[2])], "Shift+arrow across the domains"
    key(Qt.Key.Key_Space)
    assert view.selection.keys(view.shown()) == [model_.key(rows[1])]
    key(Qt.Key.Key_A, Qt.KeyboardModifier.ControlModifier)
    assert view.selection.keys(view.shown()) == view.shown()


def test_while_a_field_is_linked_there_is_no_box():
    from PySide6.QtCore import Qt
    from variables_list import BOX
    view = _list()
    view.selection.begin_single()
    model_ = view.list_model
    row = next(r for r in range(model_.rowCount()) if model_.key(r) is not None)
    assert model_.data(model_.index(row, BOX), Qt.ItemDataRole.CheckStateRole) is None
    view.toggle_all(True)
    assert len(view.selection) == 0
