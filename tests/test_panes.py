"""The position plan tab's three panes, and the tool bar that used to set their widths (docs/ui/window.md §10quater).

The tab is a horizontal splitter -- the plans and the elements, the drawing, the properties -- and until v0.67 its handles could not be dragged: the bar was one grid, so it demanded the width of its widest row (880 px with the default font, 1098 with the engineer's), that width was the centre pane's minimum, and beside the two side panes' own minima it left about a hundred pixels of play in a 1500 px window. A drag then either did nothing or took the width from the pane on the **far** side, which is what the engineer saw as the display jumping.

👉 The defect this keeps: the panes' minima were 258 + 892 + 202 in a 1468 px splitter. `test_the_panes_have_room_to_be_dragged` is the one that would have failed, and it is written on the slack rather than on any one pane, since it is the sum that decides.

⚠️ Skipped where PySide6 is not installed: a machine that only builds the report is a legitimate machine. The window is built once, off-screen -- a test run must never open one.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import conftest
from conftest import ROOT, Skip

WIDTH = 1500        # the window this is measured in, about the size Woodcore opens at
_tab = None


def _plan_tab():
    global _tab
    if _tab is None:
        conftest.exported("plans.json")      # the tab reads the export for its plans and positions
        path = str(ROOT / "calc" / "tools")
        if path not in sys.path:
            sys.path.insert(0, path)
        try:
            from PySide6.QtWidgets import QApplication
        except ImportError as exc:
            raise Skip(f"PySide6 is not installed ({exc})")
        import usersettings
        import woodcore_gui
        # Measured in English, the language conftest seeds the run's settings in: the minima are language-dependent (French labels are wider, and leave less play), and a test earlier in the run that switched the window's language wrote it into the shared settings file -- which made these tests pass alone and fail in the full suite (v0.114).
        settings = usersettings.read()
        settings["lang"] = "en"
        usersettings.write(settings)
        QApplication.instance() or QApplication([])
        window = woodcore_gui.MainWindow()
        window.resize(WIDTH, 850)
        window.show()
        _tab = next(t for t in window.tabs if type(t).__name__ == "PlanTab")
        _tab.window_ref = window             # the window outlives this call, or the tab goes with it
        window.tab_widget.setCurrentWidget(_tab)
        QApplication.instance().processEvents()
    return _tab


def _minimums(splitter):
    """The width each pane will not go below -- an explicit minimum where one is set, and what the pane's own contents ask for otherwise, which is Qt's own rule (qSmartMinSize)."""
    out = []
    for i in range(splitter.count()):
        pane = splitter.widget(i)
        out.append(pane.minimumWidth() or pane.minimumSizeHint().width())
    return out


def _drag(splitter, index, dx):
    """Drag handle `index` by dx pixels, as the mouse does, and return the sizes it leaves."""
    from PySide6.QtCore import QEvent, QPointF, Qt
    from PySide6.QtGui import QMouseEvent
    from PySide6.QtWidgets import QApplication
    handle = splitter.handle(index)
    start = QPointF(handle.width() / 2, handle.height() / 2)
    steps = ((QEvent.Type.MouseButtonPress, start, Qt.MouseButton.LeftButton),
             (QEvent.Type.MouseMove, QPointF(start.x() + dx / 2, start.y()), Qt.MouseButton.LeftButton),
             (QEvent.Type.MouseMove, QPointF(start.x() + dx, start.y()), Qt.MouseButton.LeftButton),
             (QEvent.Type.MouseButtonRelease, QPointF(start.x() + dx, start.y()), Qt.MouseButton.NoButton))
    for kind, pos, buttons in steps:
        event = QMouseEvent(kind, pos, handle.mapToGlobal(pos.toPoint()).toPointF(),
                            Qt.MouseButton.LeftButton, buttons, Qt.KeyboardModifier.NoModifier)
        QApplication.sendEvent(handle, event)
        QApplication.instance().processEvents()
    return splitter.sizes()


def test_the_tab_is_three_panes_the_engineer_can_drag():
    from PySide6.QtCore import Qt
    tab = _plan_tab()
    assert tab.splitter.orientation() == Qt.Orientation.Horizontal
    assert tab.splitter.count() == 3, [type(tab.splitter.widget(i)).__name__ for i in range(tab.splitter.count())]
    assert not tab.splitter.childrenCollapsible(), "a pane dragged to nothing is one the engineer must know to drag back"


# The splitter measured in a process of its own, in the window's own fonts (below).
MINIMA_PROBE = r"""
import json, os, sys
sys.path.insert(0, sys.argv[1])
from PySide6.QtWidgets import QApplication
import woodcore_gui
app = QApplication([])
window = woodcore_gui.MainWindow()
window.resize(int(sys.argv[2]), 850)
window.show()
tab = next(t for t in window.tabs if type(t).__name__ == "PlanTab")
window.tab_widget.setCurrentWidget(tab)
app.processEvents()
s = tab.splitter
minimums = [s.widget(i).minimumWidth() or s.widget(i).minimumSizeHint().width() for i in range(s.count())]
print(json.dumps({"width": s.width(), "minimums": minimums, "handles": s.handleWidth() * (s.count() - 1)}))
"""


def _minima_in_the_window_s_fonts():
    """The splitter's width and its panes' minima as the engineer's window has them: in Windows' own fonts, which the off-screen platform finds only when it is told where they are (`QT_QPA_FONTDIR`), and which a process can be told only before its application exists -- hence a process of its own. Elsewhere, the in-process measurement."""
    fonts = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"
    if sys.platform != "win32" or not fonts.is_dir():
        splitter = _plan_tab().splitter
        return splitter.width(), _minimums(splitter), splitter.handleWidth() * (splitter.count() - 1)
    import project
    conftest.exported("plans.json")
    env = dict(os.environ, QT_QPA_PLATFORM="offscreen", QT_QPA_FONTDIR=str(fonts), WOODCORE_PROJECT=str(project.current().file), PYTHONIOENCODING="utf-8")
    done = subprocess.run([sys.executable, "-c", MINIMA_PROBE, str(ROOT / "calc" / "tools"), str(WIDTH)], capture_output=True, text=True, encoding="utf-8", env=env, timeout=180)
    assert done.returncode == 0, done.stderr[-2000:]
    found = json.loads(done.stdout.strip().splitlines()[-1])
    return found["width"], found["minimums"], found["handles"]


def test_the_panes_have_room_to_be_dragged():
    """The defect (v0.67): the three minima all but filled the splitter, so a handle had nowhere to go.

    ⚠️ Measured in the window's own fonts (`_minima_in_the_window_s_fonts`), since the forms went into cards: a column of cards is never narrower than its cards (cards.py), so the properties pane is as wide as its widest words -- and the off-screen platform with no font directory sets words about twice as wide as Segoe UI does, which made that pane 403 px here where the engineer's window gives it 269. The centre pane, the one this test was written for, is its bar's widest button and measures the same in either.
    """
    width, minimums, handles = _minima_in_the_window_s_fonts()
    slack = width - sum(minimums) - handles
    assert slack > 400, f"{slack} px of play between the panes' minima {minimums} in {width} px"


def test_the_tool_bar_does_not_set_the_width_of_the_tab():
    """The bar wants what it wants; the pane around it must not pass that on to the splitter."""
    tab = _plan_tab()
    bar = max(row.layout().wrap_width(1) for row in tab.tool_rows)   # the width the row wants on one line
    centre = tab.splitter.widget(1).minimumSizeHint().width()
    assert bar > 400, f"the bar hints {bar} px -- this test has lost its subject"
    assert centre < bar / 2, f"the centre pane demands {centre} px of the {bar} px the bar wants"


def test_a_drag_moves_its_own_two_panes_and_not_the_third():
    """The jump: with the centre at its minimum the width came out of the pane on the far side."""
    tab = _plan_tab()
    splitter = tab.splitter
    splitter.setSizes([260, 840, 360])
    before = splitter.sizes()
    after = _drag(splitter, 1, 140)
    assert after[0] > before[0] + 100, f"the left pane did not follow the handle: {before} -> {after}"
    assert after[2] == before[2], f"the pane on the far side moved: {before} -> {after}"
    back = _drag(splitter, 1, -140)
    assert abs(back[0] - before[0]) <= 2, f"the left pane does not come back: {before} -> {after} -> {back}"
    wider = _drag(splitter, 2, -160)
    assert wider[2] > before[2] + 100, f"the right pane did not follow its handle: {before} -> {wider}"
    assert wider[0] == before[0], f"the pane on the far side moved: {before} -> {wider}"


def test_the_bar_wraps_and_loses_no_tool():
    """Narrowed, the bar takes another line rather than cutting a tool off -- the v0.66 rule, in the direction this bar can grow."""
    from PySide6.QtWidgets import QApplication, QToolButton
    tab = _plan_tab()
    tab.splitter.setSizes([260, 840, 360])
    QApplication.instance().processEvents()
    wide_rows = [len({b.y() for b in row.findChildren(QToolButton)}) for row in tab.tool_rows]
    tab.splitter.setSizes([520, 500, 440])
    QApplication.instance().processEvents()
    narrow_rows = [len({b.y() for b in row.findChildren(QToolButton)}) for row in tab.tool_rows]
    assert narrow_rows > wide_rows, f"the bar did not wrap: {wide_rows} lines wide, {narrow_rows} narrow"
    for row, lines in zip(tab.tool_rows, narrow_rows):
        for button in row.findChildren(QToolButton):
            if button.isHidden():
                continue  # a tool the plan's type does not carry (v0.116: the load-path plan's load tools), laid out by no one
            assert button.geometry().right() <= row.width(), (
                f"{button.text() or button.toolTip()} ends at {button.geometry().right()} px of a {row.width()} px row"
            )
            assert button.geometry().bottom() <= row.height(), (
                f"{button.text() or button.toolTip()} is cut off below a row {row.height()} px tall ({lines} lines)"
            )
    tab.splitter.setSizes([260, 840, 360])


def test_a_drawing_tool_s_options_do_not_widen_the_right_pane():
    """Issue #9 (D-014): a drawing tool chosen shows its element's options in the right pane, the *Section* among them -- whose list of types names SZS C5's families in full, some 750 px for the longest. That list must not set the pane's width: it made the pane 815 px wide the moment a tool was chosen, the drawing squeezed to its minimum and the bar unable to wrap (`test_the_bar_wraps_and_loses_no_tool`, run after `test_a_hidden_variant_combo_leaves_no_hole` left the beam tool chosen)."""
    from PySide6.QtWidgets import QApplication
    tab = _plan_tab()
    tab.choose_tool("select")
    QApplication.instance().processEvents()
    plan_pane = tab.splitter.widget(2).minimumSizeHint().width()
    try:
        for tool in ("T", "S", "D"):
            tab.choose_tool(tool)
            QApplication.instance().processEvents()
            width = tab.splitter.widget(2).minimumSizeHint().width()
            assert width <= plan_pane, f"the {tool} tool's options ask {width} px of the right pane, the plan's own {plan_pane}"
    finally:
        tab.choose_tool("select")


def test_a_hidden_variant_combo_leaves_no_hole():
    """A tool without variants hides the combo, and Qt's own flow layout would keep its place empty (flowbar.py)."""
    from PySide6.QtWidgets import QApplication, QToolButton
    tab = _plan_tab()
    tab.splitter.setSizes([260, 840, 360])
    tools = tab.tool_rows[1]

    def gap_after_the_letters():
        QApplication.instance().processEvents()
        buttons = sorted(tools.findChildren(QToolButton), key=lambda b: (b.y(), b.x()))
        letters = [b for b in buttons if len(b.text()) == 1]
        after = [b for b in buttons if len(b.text()) > 1 and b.y() == letters[-1].y()]
        return (after[0].x() - letters[-1].geometry().right()) if after else None

    tab.choose_tool("D")                      # a slab has variants: the combo is shown
    assert tab.subtype_combo.isVisible()
    with_combo = gap_after_the_letters()
    tab.choose_tool("T")                      # a beam has none: it is hidden
    assert not tab.subtype_combo.isVisible()
    without = gap_after_the_letters()
    if with_combo is None or without is None:
        return                                # the row wrapped between the letters and the buttons; nothing to compare
    assert without < with_combo / 2, f"the hidden combo left {without} px of hole against {with_combo} px shown"
