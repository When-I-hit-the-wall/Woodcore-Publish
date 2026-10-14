"""The tool bars of the static models' and the schemas' tabs when their pane is made shorter (docs/ui/window.md §10quater).

The centre column is a vertical splitter since v0.66 -- the bar, the drawing, the lists -- so the engineer can give the drawing the height the other two are using. The bar is the half that needed work: dragged shorter it must not *clip*, it must lay its groups into the rows that still fit, grow to the right, and scroll left and right.

⚠️ This reverses what v0.51 settled and what section 10quater said in so many words -- "the bar **wraps** rather than scrolling". Wrapping is still what a tall pane does; what is new is that a short one is not the same thing as a small one. The engineer asked for it after using the tab on a 0.5 m model, where the bar took four rows of a drawing area 400 px tall.

👉 The defect this caught, kept here because it is the one a reader should ask about: `wrap_width(1)` returned exactly the sum of the groups' widths, and `_lay` breaks on `x + w > right` where `right` is the **last pixel** rather than the width. One row therefore needs `total + 1`, the bar came out one pixel short, and a pane holding one row was drawn with two -- the second clipped, with four tools in it and nothing to say so. A stop past `total` fixes it, and `test_one_row_is_one_row` is what keeps saying so.

👉 **Since v0.75 every check runs on both tabs.** The schemas' bar was a bare QScrollArea with its vertical bar hidden: hidden is not absent, so a row taller than the pane was clipped and still scrolled up and down under the wheel -- what the engineer met, and asked in those words to be rid of ("pas de scroller vertical, seulement horizontal"). `ToolBarArea` moved to flowbar.py and serves both, and the checks below are what hold the *outcome* rather than the policy: at every height the vertical range is zero.

⚠️ Skipped where PySide6 is not installed: a machine that only builds the report is a legitimate machine. The window is built once, off-screen -- a test run must never open one.
"""

import os
import sys

import conftest
from conftest import ROOT, Skip

WIDE = 640          # the centre column at the width the side panels leave it

# The two tabs, the export file each reads to fill its lists, and the panes their centre column is built of.
TABS = {
    "StaticsTab": ("statics.json", ["ToolBarArea", "StaticsCanvas", "QTabWidget"]),
    "SchemaTab": ("schemas.json", ["ToolBarArea", "SchemaCanvas", "QTabWidget"]),
}

_window = None
_bars = {}       # tab name -> (tab, the bar's pane detached, the centre column as it was assembled)


def _bar(name):
    """The tool bar's pane of tab `name`, off-screen and **out of its splitter**.

    Detached on purpose: a widget a layout manages ignores `resize()`, so inside the splitter every height measures the same and the test would pass while proving nothing -- which is what the first run of it did.
    """
    global _window
    if name not in _bars:
        conftest.exported(TABS[name][0])     # the tab reads the export to fill its lists
        path = str(ROOT / "calc" / "tools")
        if path not in sys.path:
            sys.path.insert(0, path)
        try:
            from PySide6.QtWidgets import QApplication
        except ImportError as exc:
            raise Skip(f"PySide6 is not installed ({exc})")
        import woodcore_gui
        QApplication.instance() or QApplication([])
        if _window is None:
            _window = woodcore_gui.MainWindow()
            _window.show()
        tab = next(t for t in _window.tabs if type(t).__name__ == name)
        tab.window_ref = _window          # the window outlives this call, or the tab goes with it
        split = tab.center_split
        built = {
            "vertical": split.orientation(),
            "panes": [type(split.widget(i)).__name__ for i in range(split.count())],
            "collapsible": split.childrenCollapsible(),
        }
        area = tab.bar_area
        area.setParent(None)
        area.show()
        _bars[name] = (tab, area, built)
    return _bars[name][1]


def _groups(widget):
    """The groups of a bar -- flowbar.tool_group's, a run of controls behind a thin line (v0.94; titled QGroupBoxes until then)."""
    from PySide6.QtWidgets import QWidget
    return [g for g in widget.findChildren(QWidget) if g.objectName() == "toolGroup" and g.parent() is widget]


def _at(name, height, width=WIDE):
    """The bar of tab `name` in a pane `height` tall: (rows actually drawn, the widget, its horizontal scroll bar)."""
    from PySide6.QtWidgets import QApplication
    area = _bar(name)
    area.resize(width, height)
    QApplication.instance().processEvents()
    widget = area.widget()
    # counted off the drawn geometry, never off the layout's own arithmetic -- that arithmetic is the thing under test
    rows = len({g.y() for g in _groups(widget)})
    return rows, widget, area.horizontalScrollBar()


def _row_height(name):
    return _bar(name).widget().layout().row_height()


def _each_tab(check):
    for name in TABS:
        check(name)


def test_the_centre_column_is_three_panes_the_engineer_can_drag():
    """The drawing is what the height is wanted for, so the bar and the lists each sit in a pane of their own.

    Read as the column was **assembled**, not as it stands: `_bar()` takes the bar out of the splitter so that `resize()` works on it, which would leave this test counting two panes and failing for a reason the tab does not have.
    """
    from PySide6.QtCore import Qt

    def check(name):
        _bar(name)
        built = _bars[name][2]
        assert built["vertical"] == Qt.Orientation.Vertical, name
        assert built["panes"] == TABS[name][1], (name, built["panes"])
        assert not built["collapsible"], f"{name}: a pane dragged to nothing is one the engineer must know to drag back"
    _each_tab(check)


def test_a_tall_pane_wraps_and_does_not_scroll():
    """What v0.51 built, unchanged: given room, the bar wraps and shows every group at once."""
    def check(name):
        # a pane with a row to spare for every group: room enough to wrap at any width the widest group allows
        rows, widget, hbar = _at(name, (_bar(name).widget().layout().count() + 1) * (_row_height(name) + 6) + 24)
        # the widest single group is the floor: a group is never cut in two, so a pane narrower than it scrolls whatever its height
        layout = widget.layout()
        room = max([WIDE] + [item.sizeHint().width() for item in layout.items()])
        assert rows >= 2, f"{name}: the bar stopped wrapping: {rows} row(s) in a pane six rows tall"
        assert widget.width() <= room, f"{name}: the bar grew to {widget.width()} px with the height to wrap in"
        assert hbar.maximum() == 0 or room > WIDE, f"{name}: a bar with room to wrap is scrolling"
    _each_tab(check)


def test_a_shorter_pane_gives_fewer_rows_and_scrolls_sideways():
    """A pane a row shorter than the bar takes with room gives it one row fewer, and the bar grows to the right. Measured against the rows the bar actually takes: since the bar was made compact the static models' needs two rows at this width, where it needed three, so a fixed two-row pane was no longer shorter than it."""
    def check(name):
        row = _row_height(name)
        tall, _w, _h = _at(name, 6 * row + 40)
        assert tall >= 2, f"{name}: the bar fits one row at {WIDE} px, so no pane can be shorter than it"
        spacing = _bar(name).widget().layout().spacing()
        rows, widget, hbar = _at(name, (tall - 1) * (row + spacing) + 24)
        assert rows < tall, f"{name}: {rows} rows in a {tall - 1}-row pane against {tall} in a six-row one"
        assert widget.width() > WIDE, f"{name}: the bar did not grow to the right, so there is nothing to scroll to"
        assert hbar.maximum() > 0, f"{name}: the groups do not fit and no scroll bar reaches them"
    _each_tab(check)


def test_one_row_is_one_row():
    """The planted defect (v0.66): the bar came out one pixel short of a single row and was drawn in two, the second clipped with four tools in it."""
    def check(name):
        row = _row_height(name)
        rows, widget, hbar = _at(name, row + 24)
        assert rows == 1, f"{name}: a pane one row tall drew {rows} rows"
        assert widget.height() <= _bar(name).viewport().height(), (
            f"{name}: the bar is {widget.height()} px in a {_bar(name).viewport().height()} px pane -- a row is cut off"
        )
        assert hbar.maximum() > 0, f"{name}: one row of every group fits no viewport this narrow; it must scroll"
    _each_tab(check)


def test_no_height_ever_scrolls_up_and_down():
    """The engineer's own words for the schemas' bar (v0.75): no vertical scroller, only a horizontal one. Held as the OUTCOME -- the vertical range is zero and the bar fits the pane -- at every height from six rows down to the pane's own minimum, and below it, where the splitter would stop the drag anyway."""
    def check(name):
        area = _bar(name)
        row = _row_height(name)
        heights = [6 * row + 40, 5 * row + 30, 4 * row + 24, 3 * row + 20, 2 * row + 12, row + 24,
                   area.minimumHeight(), area.minimumHeight() + 1]
        for height in heights:
            rows, widget, _hbar = _at(name, max(height, area.minimumHeight()))
            assert area.verticalScrollBar().maximum() == 0, (
                f"{name}: at {height} px ({rows} rows) the bar can be scrolled up and down by "
                f"{area.verticalScrollBar().maximum()} px"
            )
            assert widget.height() <= area.viewport().height(), (
                f"{name}: at {height} px the bar is {widget.height()} px tall in a {area.viewport().height()} px pane"
            )
    _each_tab(check)


def test_no_tool_is_ever_left_outside_the_bar():
    """The point of the whole thing: a shorter bar loses height, never a tool -- nor a whole group. Since v0.94 a group that opens a row is laid a little left of the bar, its leading line outside it: what must stay inside is every control, the left edge included."""
    from PySide6.QtWidgets import QToolButton

    def check(name):
        row = _row_height(name)
        for height in (6 * row + 40, 3 * row + 24, 2 * row + 24, row + 24):
            for width in (WIDE, 200, 3000):
                rows, widget, _hbar = _at(name, height, width)
                buttons = widget.findChildren(QToolButton)
                assert len(buttons) >= 20, f"{name}: only {len(buttons)} tools found -- has the bar been rebuilt?"
                for button in buttons:
                    top_left = button.mapTo(widget, button.rect().topLeft())
                    box = button.mapTo(widget, button.rect().bottomRight())
                    assert top_left.x() >= 0 and box.x() <= widget.width() and box.y() <= widget.height(), (
                        f"{name}: at {width}x{height} px ({rows} rows) the tool {button.accessibleName()!r} lies outside the bar"
                    )
                for group in _groups(widget):
                    geo = group.geometry()
                    assert geo.right() <= widget.width() and geo.bottom() <= widget.height(), (
                        f"{name}: at {width}x{height} px the group {group.accessibleName()!r} is cut off"
                    )
    _each_tab(check)


def test_a_very_wide_pane_needs_no_scrolling_at_all():
    def check(name):
        rows, widget, hbar = _at(name, 3 * _row_height(name) + 24, 3000)
        assert hbar.maximum() == 0, f"{name}: 3000 px is room for every group and the bar still scrolls"
        assert _bar(name).verticalScrollBar().maximum() == 0, name
    _each_tab(check)


def test_the_wheel_scrolls_sideways_and_never_up_and_down():
    """A vertical wheel over the bar moves it sideways -- the only way it can scroll -- and never up and down."""
    from PySide6.QtCore import QPoint, QPointF, Qt
    from PySide6.QtGui import QWheelEvent
    from PySide6.QtWidgets import QApplication

    def check(name):
        rows, widget, hbar = _at(name, _row_height(name) + 24)
        area = _bar(name)
        hbar.setValue(0)
        event = QWheelEvent(QPointF(20, 20), QPointF(20, 20), QPoint(0, 0), QPoint(0, -120),
                            Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier, Qt.ScrollPhase.NoScrollPhase, False)
        QApplication.sendEvent(area.viewport(), event)
        QApplication.instance().processEvents()
        assert area.verticalScrollBar().value() == 0, f"{name}: the wheel scrolled the bar up and down"
        assert hbar.value() > 0, f"{name}: the wheel did not move a one-row bar sideways"
    _each_tab(check)


def test_the_bar_never_scrolls_up_and_down():
    """A tool bar that scrolls vertically is one where a tool is hidden with nothing to say so; the horizontal bar, by contrast, says exactly that."""
    from PySide6.QtCore import Qt

    def check(name):
        area = _bar(name)
        assert area.verticalScrollBarPolicy() == Qt.ScrollBarPolicy.ScrollBarAlwaysOff, name
        assert area.minimumHeight() >= _row_height(name), f"{name}: the pane can be dragged below one whole row"
    _each_tab(check)


def test_the_lists_can_be_dragged_shorter_than_they_ask_for():
    """A QTableWidget asks for its header and several rows, which would have stopped the splitter long before the drawing gained anything."""
    def check(name):
        _bar(name)
        tables = _bars[name][0].tables
        assert tables.minimumHeight() < tables.sizeHint().height(), (
            f"{name}: the lists will not go below {tables.minimumHeight()} px against a hint of {tables.sizeHint().height()}"
        )
        assert tables.minimumHeight() > 0, f"{name}: the lists can be dragged away entirely"
    _each_tab(check)


# --- after the position plan's bar, snug, and lists whose columns the engineer drags --------------------------
# v0.87: «Volet milieu haut, diminue la plage que prennent les outils afin que ce soit plus ergonomique.» -- a 20 px symbol over a name, 42 px a button, titled boxes. v0.94: «Ces volets prennent trop de place et sont trop peu ergonomiques. Inspire-toi du module "Plan de positions". Les icônes sont suffisamment compréhensibles pour qu'il ne faille pas de nom. Au survol, après un court moment (0.5 s), une info-bulle apparaît qui donne le nom de la commande et comment l'utiliser. Les boutons pour les outils doivent être de même hauteur que ceux des outils du module "Plan de position".» and «Séparateurs fins, sans titres». Measured at the window's default size, 1400 × 780 in French, with the side navigation: the static models' bar went from 242 px in three rows over a drawing 232 px tall to 56 px in two over 418; the schemas' from a pane of 324 px scrolling 220 px sideways over a drawing 172 px tall to 85 px in three rows, nothing to scroll, over 411.


def _plan_height():
    """How tall a tool of the position plan's bar is -- one that carries its symbol beside its name, as the plan's tools of type and axis do -- read off the built window."""
    from PySide6.QtWidgets import QToolButton
    _bar("StaticsTab")
    plan = next(t for t in _window.tabs if type(t).__name__ == "PlanTab")
    heights = {b.sizeHint().height() for row in plan.tool_rows for b in row.findChildren(QToolButton) if not b.icon().isNull()}
    assert len(heights) == 1, f"the plan's tools are not one height: {heights}"
    return heights.pop()


def test_every_tool_is_its_symbol_alone_and_as_tall_as_the_plan_s():
    """flowbar.size_tool (v0.94): every button of the two bars its symbol alone in a square as tall as a tool of the position plan's bar -- measured off the plan's own buttons, not written down -- the symbol at flowbar.symbol_px, and no word on any of them; every combo as tall. Until v0.94 a tool was a 20 px symbol over its name, 42 px tall, beside the plan's 27."""
    from PySide6.QtWidgets import QComboBox, QToolButton
    import flowbar

    plan = _plan_height()
    assert flowbar.tool_height() == plan, (flowbar.tool_height(), plan)

    def check(name):
        widget = _bar(name).widget()
        buttons = widget.findChildren(QToolButton)
        assert len(buttons) >= 20, name
        for button in buttons:
            label = button.accessibleName()
            assert label, f"{name}: a control with no name"
            assert button.height() == plan and button.width() == plan, (name, label, button.size(), plan)
            assert button.toolButtonStyle() == button.toolButtonStyle().ToolButtonIconOnly and not button.icon().isNull(), (name, label)
            assert button.iconSize().width() == flowbar.symbol_px(button.font()), (name, label)
            assert not button.text(), f"{name}: {label!r} carries a word"
        for combo in widget.findChildren(QComboBox):
            assert combo.height() == plan, (name, combo.accessibleName(), combo.height())
    _each_tab(check)


def test_the_groups_are_parted_by_a_thin_line_and_carry_no_title():
    """«Séparateurs fins, sans titres» (v0.94): no QGroupBox in either bar; every group a run of controls behind one thin line -- a frame the style sheet draws (QFrame#toolSeparator) -- and a group that opens a row lays its line outside the bar, so a line only ever stands between two groups. A group's name stays its accessible name."""
    from PySide6.QtWidgets import QFrame, QGroupBox
    import flowbar
    import theme

    assert 'QFrame#toolSeparator' in theme.STYLE and f"margin: {flowbar.SEPARATOR_GAP}px" in theme.STYLE

    def check(name):
        row = _row_height(name)
        for height, width in ((6 * row + 40, WIDE), (3 * row + 24, 400), (row + 24, WIDE)):
            _rows, widget, _hbar = _at(name, height, width)
            assert not widget.findChildren(QGroupBox), f"{name}: a titled box is left in the bar"
            groups = _groups(widget)
            assert len(groups) >= 6, name
            by_row = {}
            for group in groups:
                assert group.accessibleName(), f"{name}: a group with no name"
                first = group.layout().itemAt(0).widget()
                assert isinstance(first, QFrame) and first.objectName() == "toolSeparator", (name, group.accessibleName())
                assert first.width() == 2 * flowbar.SEPARATOR_GAP + 1
                assert len(group.findChildren(QFrame, "toolSeparator")) == 1, (name, group.accessibleName())
                by_row.setdefault(group.y(), []).append(group)
            lead = 2 * flowbar.SEPARATOR_GAP + 1 + flowbar.GROUP_SPACING
            for y, run in by_row.items():
                run.sort(key=lambda g: g.x())
                assert run[0].x() == -lead, f"{name}: the group opening the row at y={y} shows its line ({run[0].x()})"
                for group in run[1:]:
                    assert group.x() >= 0, (name, group.accessibleName(), group.x())
    _each_tab(check)


def test_a_tool_s_tooltip_names_it_and_says_how_to_use_it_in_every_language():
    """The engineer: «une info-bulle apparaît qui donne le nom de la commande et comment l'utiliser». Every control of the two bars carries its name in bold and a line of use under it, the two read from the tab's own keys (`bar_tips`), and both keys are written in French, German and English -- not the English again."""
    import woodcore_gui
    import flowbar

    def check(name):
        _bar(name)
        tab = _bars[name][0]
        widget = tab.bar_area.widget()
        tipped = {id(w) for w, _n, _u in tab.bar_tips}
        from PySide6.QtWidgets import QComboBox, QToolButton
        for control in widget.findChildren(QToolButton) + widget.findChildren(QComboBox):
            assert id(control) in tipped, f"{name}: {control.accessibleName()!r} says nothing of how it is used"
        for control, name_key, use_key in tab.bar_tips:
            assert control.toolTip() == flowbar.tip_text(tab.t(name_key), tab.t(use_key)), (name, name_key)
            assert control.toolTip().startswith('<p style="white-space:nowrap"><b>') and "<br>" in control.toolTip(), (name, name_key)
            for key in (name_key, use_key):
                words = {lang: woodcore_gui.STRINGS[lang][key] for lang in ("fr", "de", "en")}
                assert all(words.values()), (name, key, words)
            use = {lang: woodcore_gui.STRINGS[lang][use_key] for lang in ("fr", "de", "en")}
            assert len(set(use.values())) == 3, f"{name}: {use_key} is not translated: {use}"
    _each_tab(check)


def test_the_tooltip_comes_after_half_a_second_and_goes_with_the_pointer():
    """flowbar.DelayedTips (v0.94): nothing before TIP_DELAY_MS, the tool's own tooltip after it, and gone once the pointer leaves -- where Qt's own tooltips wait about 0.7 s. Only the tools it watches: the application's delay is left alone."""
    import time
    from PySide6.QtCore import QEvent, QPointF
    from PySide6.QtGui import QCursor, QEnterEvent
    from PySide6.QtWidgets import QApplication, QToolTip
    import flowbar

    app = QApplication.instance()

    def run(seconds):
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            app.processEvents()
            time.sleep(0.01)

    assert flowbar.TIP_DELAY_MS == 500

    def check(name):
        _at(name, 3 * _row_height(name) + 24, 3000)
        tab = _bars[name][0]
        button = next(b for b in tab.tool_buttons.values() if b.isVisible())
        # the pointer off every tool and no timer left running: a window shown under the pointer enters a tool, and that tool's timer showed its tip during the wait below, before the Enter this test sends
        QCursor.setPos(app.primaryScreen().geometry().bottomRight())
        flowbar.delayed_tips().timer.stop()
        QToolTip.hideText()
        run(0.5)                       # a tip left from before, and Qt's own 300 ms of hiding it
        flowbar.delayed_tips().awake_until = 0.0
        QApplication.sendEvent(button, QEnterEvent(QPointF(4, 4), QPointF(4, 4), QPointF(4, 4)))
        run(0.35)
        assert not QToolTip.isVisible(), f"{name}: the tooltip came before half a second"
        run(0.35)
        assert QToolTip.isVisible() and QToolTip.text() == button.toolTip(), f"{name}: no tooltip after 0.7 s"
        # the pointer leaves as a pointer does, off the tool: left over it, the off-screen platform enters the tool again when the tip closes
        QCursor.setPos(app.primaryScreen().geometry().bottomRight())
        QApplication.sendEvent(button, QEvent(QEvent.Type.Leave))
        run(0.5)
        assert not QToolTip.isVisible(), f"{name}: the tooltip stayed after the pointer left"
    _each_tab(check)


def test_the_pane_is_made_snug_round_the_bar_when_first_shown():
    """The splitter hands the bar's pane its height at Qt's first guess at its width -- 640 px -- which at the pane's real width may be a row more than the bar needs; the first time it is shown the pane gives that strip to the drawing, and never again, so a height the engineer drags stays his."""
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication, QSplitter, QWidget
    import flowbar

    def check(name):
        area = _bar(name)
        split = QSplitter(Qt.Orientation.Vertical)
        split.addWidget(area)
        split.addWidget(QWidget())
        split.resize(3000, 900)
        split.show()
        split.setSizes([450, 450])
        QApplication.instance().processEvents()
        total = sum(split.sizes())            # the splitter's handle takes its own few pixels
        area.snug()
        QApplication.instance().processEvents()
        sizes = split.sizes()
        assert sizes[0] == max(area.snug_height(), area.minimumHeight()) and sum(sizes) == total, (name, sizes)
        assert sizes[1] > 450, f"{name}: the strip the bar did not use went to nothing"
        assert area.verticalScrollBar().maximum() == 0 and area.horizontalScrollBar().maximum() == 0, name
        # and a pane handed less than the bar needs at its real width takes the row it lacks from the drawing (v0.94): at the window's own size the schemas' bar was otherwise laid out in one row scrolling 700 px sideways
        split.resize(400, 900)
        split.setSizes([area.minimumHeight(), 900 - area.minimumHeight()])
        QApplication.instance().processEvents()
        area.snug()
        QApplication.instance().processEvents()
        assert split.sizes()[0] == area.snug_height() > area.minimumHeight(), (name, split.sizes(), area.snug_height())
        assert area.horizontalScrollBar().maximum() == 0, f"{name}: the snug pane still scrolls sideways"
        # and the flag a restored layout sets is what keeps it from doing so again
        assert flowbar.ToolBarArea.snug_on_show is True
        area.setParent(None)
        area.show()
        split.deleteLater()
    _each_tab(check)


def test_the_lists_columns_are_dragged_by_the_engineer_and_kept():
    """Each column starts at the width of what it holds; one the engineer has dragged keeps his width while the list is filled again after every edit, and through `view_state` -- a language switch, a reload."""
    from PySide6.QtWidgets import QHeaderView
    import flowbar

    def check(name):
        _bar(name)
        tab = _bars[name][0]
        fill = tab.set_tables if name == "StaticsTab" else tab.fill_tables
        for which, table in tab.table_widgets.items():
            header = table.horizontalHeader()
            assert header.sectionResizeMode(0) == QHeaderView.ResizeMode.Interactive, (name, which)
            assert not header.stretchLastSection(), (name, which)
        which, table = next(iter(tab.table_widgets.items()))
        header = table.horizontalHeader()
        header.resizeSection(1, 173)          # what a drag of the divider does
        fill()
        assert header.sectionSize(1) == 173, (name, which, header.sectionSize(1))
        state = tab.view_state()["columns"]
        assert state[which] == {"1": 173}, (name, state[which])
        # another list fitted by its content again, as it always was
        columns = flowbar.ResizableColumns(table)
        columns.restore(state[which])
        assert header.sectionSize(1) == 173
        tab.table_columns[which].restore({})
        fill()
        assert header.sectionSize(1) != 173 or table.sizeHintForColumn(1) == 173, (name, which)
    _each_tab(check)
