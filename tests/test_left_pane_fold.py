"""Every tab's own left pane -- its list or its tree, the second pane from the left -- folds away and back by the arrow at its foot, is remembered folded, and narrows far below what its buttons once held it at (issue #10, docs/ui/window.md §10quater, chrome.FoldablePane, cards.loosen).

👉 The defect this keeps: the pane stopped at 240 to 435 px depending on the tab, the width of its row of buttons side by side, or a minimum written in (Structure's 180 px); only the plan tabs could fold theirs (v0.117).

⚠️ Skipped where PySide6 is not installed. The window is built once, off-screen.
"""

import os
import sys

import conftest
from conftest import ROOT, Skip

_STATE = {}
PANE_MAX_FLOOR = 200   # px: the widest any tab's left pane may still insist on -- the floor (cards.PANE_FLOOR) plus a row of squeezed buttons


def _window():
    if "window" not in _STATE:
        conftest.exported("plans.json")
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        path = str(ROOT / "calc" / "tools")
        if path not in sys.path:
            sys.path.insert(0, path)
        try:
            from PySide6.QtWidgets import QApplication
        except ImportError as exc:
            raise Skip(f"PySide6 is not installed ({exc})")
        import woodcore_gui
        app = QApplication.instance() or QApplication([])
        window = woodcore_gui.MainWindow()
        window.resize(1500, 850)
        window.show()
        app.processEvents()
        _STATE.update(window=window, app=app)
    return _STATE["window"], _STATE["app"]


def _panes():
    """(key, tab, pane) for every tab with a left pane of its own."""
    import chrome
    import woodcore_gui
    from PySide6.QtWidgets import QSplitter
    window, _app = _window()
    out = []
    for (key, _factory), tab in zip(woodcore_gui.TABS, window.tabs):
        splitter = getattr(tab, "splitter", None)
        if isinstance(splitter, QSplitter) and splitter.count() >= 2:
            out.append((key, tab, splitter.widget(0)))
    assert len(out) >= 15, [k for k, _t, _p in out]
    assert all(isinstance(pane, chrome.FoldablePane) for _k, _t, pane in out), [(k, type(p).__name__) for k, _t, p in out if not isinstance(p, chrome.FoldablePane)]
    return out


def _settle(app, rounds=4):
    for _ in range(rounds):   # a squeezed button's text is fitted on the next turn of the loop (cards._Elider)
        app.processEvents()


def test_every_tab_s_left_pane_has_the_arrow_and_a_low_floor():
    import cards
    window, app = _window()
    for key, tab, pane in _panes():
        # measured shown, as the engineer meets it: a tab never shown keeps the widths its buttons had before cards.loosen squeezed them (Qt lays out a hidden widget again only when it is shown)
        window.tab_widget.setCurrentWidget(tab)
        _settle(app)
        floor = pane.minimumSizeHint().width()
        assert cards.PANE_FLOOR <= floor <= PANE_MAX_FLOOR, f"{key}: its left pane will not go below {floor} px"
        assert pane.fold.isVisibleTo(pane), key
        assert not pane.splitter().childrenCollapsible(), f"{key}: a pane dragged to nothing has no arrow to come back by"


def test_at_its_floor_no_button_of_the_pane_is_cut():
    from PySide6.QtCore import QPoint
    from PySide6.QtWidgets import QPushButton
    window, app = _window()
    for key, tab, pane in _panes():
        window.tab_widget.setCurrentWidget(tab)
        _settle(app)
        splitter = pane.splitter()
        sizes = splitter.sizes()
        splitter.setSizes([0, sizes[1] + sizes[0]] + sizes[2:])   # as far left as it goes: Qt stops it at its minimum
        _settle(app)
        assert pane.width() <= PANE_MAX_FLOOR, f"{key}: dragged to the left it stays {pane.width()} px wide"
        for button in pane.findChildren(QPushButton):
            if not button.isVisibleTo(pane) or button.width() <= 0:
                continue
            right = button.mapTo(pane, QPoint(button.width(), 0)).x()
            assert right <= pane.width() + 1, f"{key}: «{button.text()}» ends at {right} px of a {pane.width()} px pane"
        splitter.setSizes(sizes)
        _settle(app)


def test_the_arrow_folds_every_pane_and_gives_its_width_back():
    window, app = _window()
    for key, tab, pane in _panes():
        window.tab_widget.setCurrentWidget(tab)
        _settle(app)
        width = pane.width()
        pane.fold.click()
        _settle(app)
        assert pane.folded and pane.width() <= 40 and pane.content.isHidden(), (key, pane.width())
        assert key in window.folded_left_panes(), f"{key}: the fold is not remembered"
        pane.fold.click()
        _settle(app)
        assert not pane.folded and abs(pane.width() - width) <= 2, (key, pane.width(), width)
        assert key not in window.folded_left_panes(), key


def test_a_pane_left_folded_is_folded_at_the_next_start():
    """The setting `left_folded` read when the tab's layout is bound -- after its sizes are put back, so the width it unfolds to is the one dragged."""
    window, app = _window()
    key, tab, pane = next(item for item in _panes() if item[0] != "tab_plan")
    window.tab_widget.setCurrentWidget(tab)
    _settle(app)
    try:
        window.remember_left_fold(key, True)
        window.refresh_tab(key)
        _settle(app)
        new = dict((k, p) for k, _t, p in _panes())[key]
        assert new.folded, f"{key}: left folded, built again open"
    finally:
        window.remember_left_fold(key, False)
        window.refresh_tab(key)
        _settle(app)
