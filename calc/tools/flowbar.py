"""A row of controls that wraps onto the next line, and the widget that carries one -- the window's tool bars are built on it (docs/ui/window.md §10quater, docs/conventions/testing.md §11ter). Beside it, the rest of what the centre column of the static models' and the schemas' tabs is furnished with: the measures of their tool bars, the symbols they share, the tooltip that names a tool and says how to use it, and the lists under the drawing whose columns the engineer drags.

Written for the static models' bar (v0.66) and moved here when the position plan's bar needed the same thing (v0.67): a bar whose width is its own business rather than the minimum width of the whole tab. A bar laid out in a grid demands the width of its widest row, and a tab whose centre pane demands 880 px is a tab whose splitter cannot be dragged.

⚠️ An item whose widget is hidden is skipped rather than given a place (v0.67). Qt's own flow-layout example lays every item out, hidden or not, which leaves a hole where the plan's subtype combo sits while the tool chosen has no variants.
"""

import html
import textwrap
import time

from PySide6.QtCore import QByteArray, QEvent, QObject, QPoint, QRect, QRectF, QSize, Qt, QTimer
from PySide6.QtGui import QCursor, QGuiApplication, QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (QApplication, QComboBox, QFrame, QHBoxLayout, QHeaderView, QLayout, QScrollArea, QSizePolicy,
                               QSplitter, QStyle, QStyleOptionComboBox, QStylePainter, QToolButton, QToolTip, QWidget)

# The measures of the static models' and the schemas' tool bars, one place for both (v0.94). The engineer: «Ces volets prennent trop de place et sont trop peu ergonomiques. Inspire-toi du module "Plan de positions". Les icônes sont suffisamment compréhensibles pour qu'il ne faille pas de nom.» So every tool is its symbol alone in a square button, the groups are parted by a thin line and no longer boxed under a title («Séparateurs fins, sans titres»), and a button is exactly as tall as a tool of the position plan's bar -- where from v0.87 a button was a 20 px symbol over its name, 42 px tall, and the groups stood in titled boxes, so at the window's own size the static models' bar took three rows and 242 px over the drawing.
#
# The height is measured, not written down: `tool_height` lays out a button as plan_tab.tool_button makes one -- its name beside a PLAN_ICON symbol -- and takes the height Qt gives it under the window's font and style sheet, which is what the plan's tools are.
PLAN_ICON = QSize(26, 18)
# a symbol alone is drawn this much smaller than its button, top and bottom: the button's frame and padding (theme.STYLE's QToolButton, 1 px and 2 px) and a pixel to spare
SYMBOL_INSET = 7
# the size a symbol is rendered at where no button gives it one -- what `symbol_px` comes to at the window's default font
TOOL_ICON_PX = 20
# the padding a button that carries a word keeps round it -- a control with no symbol, which the bars no longer have but a caller may still make
TOOL_PAD = 6
# the space between two controls of a group, and between two groups either side of the line that parts them: the line is the middle of a frame SEPARATOR_GAP + 1 + SEPARATOR_GAP wide, so a group reads as its own run of buttons
GROUP_SPACING = 2
BAR_SPACING = 2
SEPARATOR_GAP = 5
# The dynamic property a group carries the width of its leading line under: a group that opens a row is moved left by that much, so the line falls outside the bar and no row starts with one (FlowLayout._lay).
LEAD = "flowLead"
# How long the pointer rests on a tool before its tooltip names it and says how to use it -- half a second, the engineer's figure, where Qt's own wait is about 0.7 s. Only the bars' tools: the application's own delay is left alone for every other widget.
TIP_DELAY_MS = 500
# A tooltip hidden by the pointer leaving its tool leaves the next one awake this long, so running the pointer along the bar names each tool at once, as Qt's own tooltips do.
TIP_AWAKE_S = 0.4
# how many characters a line of a tooltip's use runs to: about 360 px of the window's font
TIP_LINE = 56

# The symbols the two bars share, where the figure has none to lend: the navigation, the history, the snapping, and the schemas' two actions that draw nothing. SVG text on a 24 px square, `{c}` the ink -- the scheme's, so a symbol reads on the dark ground as on the light one (theme.py, v0.90). The undo and redo arrows were written into both tabs until v0.94.
ICONS = {
    "select": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">'
              '<path d="M6.5 3.5 V19 L10.4 15.3 L13.1 21 L15.6 19.9 L12.9 14.3 L18.2 14.1 Z" fill="none" stroke="{c}" '
              'stroke-width="1.7" stroke-linejoin="round"/></svg>',
    "pan": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">'
           '<path d="M12 5 V19 M5 12 H19" fill="none" stroke="{c}" stroke-width="1.7"/>'
           '<polygon points="12,2 8.8,6 15.2,6" fill="{c}"/><polygon points="12,22 8.8,18 15.2,18" fill="{c}"/>'
           '<polygon points="2,12 6,8.8 6,15.2" fill="{c}"/><polygon points="22,12 18,8.8 18,15.2" fill="{c}"/></svg>',
    "fit": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">'
           '<path d="M3 8 V3 H8 M16 3 H21 V8 M21 16 V21 H16 M8 21 H3 V16" fill="none" stroke="{c}" stroke-width="1.8"/>'
           '<rect x="8" y="8" width="8" height="8" fill="none" stroke="{c}" stroke-width="1.4"/></svg>',
    "crop": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">'
            '<path d="M6.5 2 V17.5 H22 M2 6.5 H17.5 V22" fill="none" stroke="{c}" stroke-width="1.8"/></svg>',
    "snap": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">'
            '<path d="M6 8.5 V12 a6 6 0 0 0 12 0 V8.5" fill="none" stroke="{c}" stroke-width="3.2"/>'
            '<path d="M6 3 V6.4 M18 3 V6.4" fill="none" stroke="{c}" stroke-width="3.2"/></svg>',
    "marker-grid": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">'
                   + "".join(f'<circle cx="{x}" cy="{y}" r="2.1" fill="{{c}}"/>' for y in (5, 12, 19) for x in (5, 12, 19))
                   + '</svg>',
    "clear-lines": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">'
                   '<path d="M2.5 16 L21.5 4" fill="none" stroke="{c}" stroke-width="1.6" stroke-dasharray="3.2,2.4"/>'
                   '<path d="M14 14 L20.5 20.5 M20.5 14 L14 20.5" fill="none" stroke="{c}" stroke-width="2"/></svg>',
    "undo": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">'
            '<path d="M7 9 H14 a5 5 0 0 1 0 10 H9" fill="none" stroke="{c}" stroke-width="2.1" '
            'stroke-linecap="round"/><polygon points="4,9 10,5.5 10,12.5" fill="{c}"/></svg>',
    "redo": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">'
            '<path d="M17 9 H10 a5 5 0 0 0 0 10 H15" fill="none" stroke="{c}" stroke-width="2.1" '
            'stroke-linecap="round"/><polygon points="20,9 14,5.5 14,12.5" fill="{c}"/></svg>',
}

_heights = {}


def tool_height(font=None):
    """The one height every control of the two bars is set to: a tool of the position plan's bar, measured (v0.94). A probe button is laid out as plan_tab.tool_button lays one out -- a name beside a PLAN_ICON symbol, raised on hover -- under the application's style sheet and `font`, and its height is Qt's own answer; kept per font and style sheet, the style sheet being the same geometry in both schemes."""
    app = QApplication.instance()
    probe_font = font if font is not None else (app.font() if app is not None else None)
    key = (probe_font.toString() if probe_font is not None else "", hash(app.styleSheet()) if app is not None else 0)
    if key not in _heights:
        probe = QToolButton()
        if probe_font is not None:
            probe.setFont(probe_font)
        probe.setAutoRaise(True)
        pixmap = QPixmap(PLAN_ICON)
        pixmap.fill(Qt.GlobalColor.transparent)
        probe.setIcon(QIcon(pixmap))           # a null icon would lay the probe out as text alone, which is shorter
        probe.setIconSize(PLAN_ICON)
        probe.setText("Ag")
        probe.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        probe.ensurePolished()
        _heights[key] = probe.sizeHint().height()
        probe.deleteLater()
    return _heights[key]


def symbol_px(font=None):
    """How big a tool's symbol is drawn: its square button's height less its frame and padding (SYMBOL_INSET). 20 px at the default font, the size the symbols were drawn at from v0.87."""
    return tool_height(font) - SYMBOL_INSET


def pixel_ratio():
    """The screen's device pixel ratio, what a symbol is rendered at so it stays sharp on a scaled display rather than being drawn at 20 px and blown up."""
    app = QGuiApplication.instance()
    return app.devicePixelRatio() if app is not None else 1.0


def icon(name, size, ink):
    """One of the shared symbols (ICONS), `size` logical pixels square in `ink`, rendered at the screen's pixel ratio."""
    return svg_text_icon(ICONS[name].format(c=ink), size)


def svg_text_icon(svg, size):
    """An icon from SVG text, `size` logical pixels square, rendered at the screen's pixel ratio."""
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    ratio = pixel_ratio()
    pixmap = QPixmap(round(size * ratio), round(size * ratio))
    pixmap.setDevicePixelRatio(ratio)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    renderer.render(painter, QRectF(0, 0, size, size))
    painter.end()
    return QIcon(pixmap)


def size_tool(button, named=False):
    """A QToolButton at the bar's measures: `tool_height` tall, and square with its symbol alone at `symbol_px` -- every tool since v0.94, its name and its use being its tooltip (`set_tip`). `named`, or a button with no symbol, carries its word instead and is exactly as wide as that word needs: a control nothing draws a symbol for is kept compact rather than dropped."""
    height = tool_height(button.font())
    button.setFixedHeight(height)
    if named or button.icon().isNull():
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        button.setFixedWidth(button.fontMetrics().horizontalAdvance(button.text()) + 2 * TOOL_PAD + 2)
    else:
        px = height - SYMBOL_INSET
        button.setIconSize(QSize(px, px))
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        button.setFixedWidth(height)
    return button


def tip_text(name, usage=""):
    """A tool's tooltip: its name in bold, and under it how it is used, broken into lines of TIP_LINE characters here -- left to itself Qt narrows a rich tooltip to about 220 px, which set a tool's sentence on five lines (measured), and it sets the lines it is given as they come."""
    lines = [f"<b>{html.escape(name, quote=False)}</b>"]
    lines += [html.escape(line, quote=False) for line in textwrap.wrap(usage, TIP_LINE)]
    return '<p style="white-space:nowrap">' + "<br>".join(lines) + "</p>"


class DelayedTips(QObject):
    """The bars' tooltips, after TIP_DELAY_MS rather than Qt's own wait (v0.94). An event filter on each tool: the pointer entering starts a timer, and when it runs out the tool's own tooltip is shown where the pointer is; leaving, pressing or scrolling stops it. Qt's own ToolTip event is eaten on the tools it watches, so a tip never shows twice, and the application's delay is left alone for every other widget. One filter serves every bar: only one tool is under the pointer at a time."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(TIP_DELAY_MS)
        self.timer.timeout.connect(self.show_tip)
        self.over = None
        self.left = None
        self.awake_until = 0.0

    def eventFilter(self, watched, event):
        kind = event.type()
        if kind == QEvent.Type.ToolTip:
            # a disabled tool has no Enter to start the timer with, so it keeps Qt's own tooltip
            return watched.isEnabled()
        if kind == QEvent.Type.Enter:
            self.over = watched
            # awake: the pointer came from another tool whose tip was up -- not back onto the one it left, which Qt also re-enters when a tip closes over it
            if time.monotonic() < self.awake_until and watched is not self.left:
                self.show_tip()
            else:
                self.timer.start()
        elif kind in (QEvent.Type.Leave, QEvent.Type.MouseButtonPress, QEvent.Type.Wheel, QEvent.Type.Hide):
            if watched is self.over:
                if QToolTip.isVisible() and kind == QEvent.Type.Leave:
                    self.awake_until = time.monotonic() + TIP_AWAKE_S
                    self.left = watched
                self.timer.stop()
                self.over = None
                QToolTip.hideText()
        return False

    def show_tip(self):
        widget = self.over
        try:
            if widget is None or not widget.isVisible() or not widget.toolTip():
                return
            QToolTip.showText(QCursor.pos(), widget.toolTip(), widget)
        except RuntimeError:        # the tool was deleted under the pointer -- a window built again
            self.over = None


_tips = []


def delayed_tips():
    """The one DelayedTips of the application, made the first time a tool asks for it."""
    if not _tips:
        _tips.append(DelayedTips(QApplication.instance()))
    return _tips[0]


def set_tip(widget, name, usage=""):
    """Names `widget` and says how to use it: the tooltip `tip_text`, shown after TIP_DELAY_MS; its accessible name the plain name, so a screen reader -- and a test -- finds a tool by it, and its accessible description the use."""
    widget.setToolTip(tip_text(name, usage))
    widget.setAccessibleName(name)
    widget.setAccessibleDescription(usage)
    widget.installEventFilter(delayed_tips())
    return widget


def separator():
    """The thin line between two groups of a bar: a frame drawn by the style sheet (`QFrame#toolSeparator`, theme.STYLE), its left border in the middle of its width, in the scheme's own line colour."""
    line = QFrame()
    line.setObjectName("toolSeparator")
    line.setFrameShape(QFrame.Shape.VLine)
    line.setFixedWidth(2 * SEPARATOR_GAP + 1)
    return line


def tool_group(widgets, name=""):
    """One group of the bar, its controls side by side and close, a thin line before them and no title (v0.94; a box with its name on it until then). The group's name is its accessible name. A group that opens a row of the bar lays its line outside the bar (LEAD), so a line only ever stands between two groups."""
    group = QWidget()
    group.setObjectName("toolGroup")
    group.setAccessibleName(name)
    row = QHBoxLayout(group)
    row.setContentsMargins(0, 0, 0, 0)
    row.setSpacing(GROUP_SPACING)
    row.addWidget(separator())
    for widget in widgets:
        row.addWidget(widget)
    group.setProperty(LEAD, 2 * SEPARATOR_GAP + 1 + GROUP_SPACING)
    return group


def combo_chrome(combo):
    """How much of a combo's width is not its edit field -- border, padding and drop-down -- asked of the style at the bar's height. Qt's own size hint leaves the drop-down out under the window's style sheet, which is what cut the static models' «auto» to «aut»."""
    option = QStyleOptionComboBox()
    combo.initStyleOption(option)
    option.rect = QRect(0, 0, 200, tool_height(combo.font()))
    edit = combo.style().subControlRect(QStyle.ComplexControl.CC_ComboBox, option, QStyle.SubControl.SC_ComboBoxEditField, combo)
    return 200 - edit.width()


def size_combo(combo):
    """A combo of the bar -- the grid's step -- as tall as a tool and exactly as wide as its longest choice needs, with no room kept beside its arrow (QComboBox[compact="true"], theme.STYLE)."""
    combo.setProperty("compact", True)
    combo.ensurePolished()
    words = max((combo.fontMetrics().horizontalAdvance(combo.itemText(i)) for i in range(combo.count())), default=0)
    combo.setFixedSize(words + combo_chrome(combo) + 4, tool_height(combo.font()))
    return combo


class SymbolCombo(QComboBox):
    """A choice of the bar shown by its symbol alone, as every tool is, its words in the list it opens (v0.94) -- the schemas' «Surfacique» mode, whose words («Arête + largeur tapée») made its group the widest of the bar. As tall as a tool; as wide as its symbol and its arrow."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("compact", True)     # QComboBox[compact="true"], theme.STYLE: no room kept beside the arrow
        self.ensurePolished()

    def sizeHint(self):
        """Its symbol and whatever the style keeps round an edit field (combo_chrome) -- Qt's own hint leaving out the drop-down's width under the window's style sheet, and so the symbol."""
        return QSize(self.iconSize().width() + combo_chrome(self) + 1, tool_height(self.font()))

    def minimumSizeHint(self):
        return self.sizeHint()

    def paintEvent(self, _event):
        painter = QStylePainter(self)
        option = QStyleOptionComboBox()
        self.initStyleOption(option)
        option.currentText = ""
        painter.drawComplexControl(QStyle.ComplexControl.CC_ComboBox, option)
        painter.drawControl(QStyle.ControlElement.CE_ComboBoxLabel, option)

    def showPopup(self):
        # the list shows the words the box leaves out, so it is as wide as they are
        view = self.view()
        view.setMinimumWidth(view.sizeHintForColumn(0) + 2 * view.frameWidth() + 8)
        super().showPopup()


class ResizableColumns:
    """The columns of one list under the drawing, which the engineer widens or narrows by dragging the dividers of its header (the static models' and the schemas' tabs).

    Each column starts at the width of what it holds, as it did while the header sized them itself (ResizeToContents in the one tab, Stretch in the other -- neither of which a divider can be dragged in). A column the engineer has dragged keeps his width from then on: a list is filled again after every edit, and a width that snapped back to the content at the next keystroke would be a width nobody can set. `state()` and `restore()` carry the widths through the tab's `view_state`, a language switch and a reload.
    """

    def __init__(self, table):
        self.table = table
        self.by_hand = {}      # column -> the width the engineer dragged it to
        self._fitting = False
        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(False)
        header.sectionResized.connect(self._resized)

    def _resized(self, column, _old, new):
        # a width set here, while the list is fitted, is not the engineer's
        if not self._fitting:
            self.by_hand[column] = new

    def fit(self):
        """After the list is filled: every column the engineer has not dragged to the width of its content and its header, every one he has at his own width."""
        self._fitting = True
        try:
            for column in range(self.table.columnCount()):
                if column in self.by_hand:
                    self.table.setColumnWidth(column, self.by_hand[column])
                else:
                    self.table.resizeColumnToContents(column)
        finally:
            self._fitting = False

    def state(self):
        return {str(column): width for column, width in self.by_hand.items()}

    def restore(self, state):
        self.by_hand = {int(column): int(width) for column, width in (state or {}).items()}
        self.fit()


class FlowLayout(QLayout):
    """A row of widgets that wraps onto the next line when it runs out of width -- Qt's own example layout, in the shape this tab needs it. It is what lets the tool bar keep its groups whole and take two rows in a narrow window, rather than scrolling or forcing the drawing to stay wide."""

    def __init__(self, parent=None, margin=0, spacing=6):
        super().__init__(parent)
        self._items = []
        self.setContentsMargins(margin, margin, margin, margin)
        self.setSpacing(spacing)

    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        return self._items[index] if 0 <= index < len(self._items) else None

    def takeAt(self, index):
        return self._items.pop(index) if 0 <= index < len(self._items) else None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._lay(QRect(0, 0, width, 0), test=True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._lay(rect, test=False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self.items():
            # an item alone on its row opens it, and its lead is laid outside
            size = size.expandedTo(item.minimumSize() - QSize(self.lead(item), 0))
        margins = self.contentsMargins()
        return size + QSize(margins.left() + margins.right(), margins.top() + margins.bottom())

    def items(self):
        """The items that take a place: a hidden widget is passed over, where Qt's example would leave its gap."""
        return [item for item in self._items if not item.isEmpty()]

    @staticmethod
    def lead(item):
        """How much of `item` is laid outside the bar where it opens a row: its leading line (tool_group, LEAD, v0.94), which parts it from the group before it and has no group before it there. 0 for any other item -- the position plan's buttons."""
        widget = item.widget()
        value = widget.property(LEAD) if widget is not None else None
        return int(value) if value else 0

    def row_height(self):
        """The tallest item, which is one row of the bar."""
        return max((item.sizeHint().height() for item in self.items()), default=0)

    def wrap_width(self, rows):
        """The width the items need in order to come out in `rows` rows or fewer (v0.66).

        This is what lets a bar that is given less height grow to the right instead of losing a tool: the caller sets it as the widget's minimum width, and a viewport narrower than that scrolls. An even share of the total is the first guess and not the answer -- the items are whole groups of unequal width, so the guess is widened until the greedy fill below actually comes out at `rows`.
        """
        items = self.items()
        widths = [item.sizeHint().width() for item in items]
        if not widths:
            return 0
        rows = max(1, rows)
        margins = self.contentsMargins()
        total = sum(widths) + self.spacing() * (len(widths) - 1) - self.lead(items[0])
        target = max(max(w - self.lead(item) for w, item in zip(widths, items)), total // rows)
        # ⚠️ The stop is past `total` and not at it. `_lay` breaks on `x + w > right`, and `right` is the last pixel rather than the width, so one row needs `total + 1` -- and for rows = 1 the guess starts exactly at `total`, where a stop at `total` would leave the bar one pixel short and lay it out in two rows inside a pane that holds one.
        limit = total + self.spacing() + 32
        while self._rows_at(target) > rows and target < limit:
            target += 24
        return target + margins.left() + margins.right()

    def _rows_at(self, width):
        """How many rows the greedy fill of `_lay` produces in `width`. Written to break exactly where `_lay` breaks, since a disagreement here would size the bar for one layout and draw it in another."""
        rows, x, placed = 1, 0, False
        for item in self.items():
            hint = item.sizeHint().width()
            if x + hint > width - 1 and placed:
                rows, x, placed = rows + 1, 0, False
            left = x if placed else x - self.lead(item)
            x = left + hint + self.spacing()
            placed = True
        return rows

    def _lay(self, rect, test):
        """The greedy fill: each item where the last one ended, or at the start of the next row where it would run past the right edge. An item opening a row is moved left by its lead (v0.94), so a group's leading line falls outside the bar -- the bar's widget clips it -- and its first control stands at the row's start."""
        margins = self.contentsMargins()
        area = rect.adjusted(margins.left(), margins.top(), -margins.right(), -margins.bottom())
        x, y, line, placed = area.x(), area.y(), 0, False
        for item in self.items():
            hint = item.sizeHint()
            if placed and x + hint.width() > area.right():
                x, y, line, placed = area.x(), y + line + self.spacing(), 0, False
            if not placed and hint.width() - self.lead(item) > area.width():
                # alone on its row and still wider than it: narrowed to the row, never below its own minimum -- a button squeezed in a narrow pane is cut with an ellipsis (cards.loosen, issue #10) rather than past the pane's right edge
                hint = QSize(max(item.minimumSize().width(), area.width() + self.lead(item)), hint.height())
            left = x if placed else x - self.lead(item)
            if not test:
                if left < x:
                    # QWidgetItem.setGeometry keeps a widget inside the layout, which would take the lead back; the widget itself is set where it goes
                    item.widget().setGeometry(QRect(QPoint(left, y), hint))
                else:
                    item.setGeometry(QRect(QPoint(left, y), hint))
            x = left + hint.width() + self.spacing()
            line = max(line, hint.height())
            placed = True
        return y + line - rect.y() + margins.bottom()


class FlowWidget(QWidget):
    """A widget whose height follows the wrapping of its FlowLayout; a plain QWidget would keep the height of one row."""

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self.layout().heightForWidth(width)

    def sizeHint(self):
        return QSize(self.layout().minimumSize().width(), self.heightForWidth(self.width() or 800))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.setFixedHeight(self.heightForWidth(self.width()))


class ToolBarArea(QScrollArea):
    """The tool bar, in a pane whose height the engineer sets by dragging (v0.66; shared by the static models' and the schemas' tabs since v0.75).

    Given room it wraps exactly as it did before and shows every group at once. Dragged shorter it does not clip: it lays the groups into the rows that still fit, grows to the right, and **scrolls left and right**. That is what makes the height givable back to the drawing without a tool going missing, which is the whole of what was asked for.

    ⚠️ The vertical scroll bar is off on purpose, and that is the rule this is built on: a tool bar that scrolls up and down is one where a tool is hidden with nothing to say so. Off, the only way the bar can fail to show a group is by being too narrow, and then the horizontal bar is there saying exactly that. Off is not enough on its own -- a QScrollArea with its bar hidden still scrolls under the wheel and still clips what is taller than it -- which is why `fit_rows` sizes the bar so that it is never taller than the pane, and `wheelEvent` turns a vertical wheel into a horizontal scroll (v0.75: the schemas' bar was a bare QScrollArea, and did both).

    Moved here from statics_tab.py in v0.75, when the «Schémas» tab needed the same bar: one mechanism, one file, as FlowLayout was in v0.67.
    """

    def __init__(self, bar):
        super().__init__()
        self.setWidget(bar)
        self.setWidgetResizable(True)
        self.setFrameShape(QScrollArea.Shape.NoFrame)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        layout = bar.layout()
        margins = layout.contentsMargins()
        # one row, its margins and the scroll bar under it: the shortest the bar may be dragged, since below that a group is cut in half rather than moved
        self.setMinimumHeight(layout.row_height() + margins.top() + margins.bottom()
                              + self.horizontalScrollBar().sizeHint().height())

    # Whether the pane is made snug round the bar the first time it is shown (`snug`). A tab restoring the heights the engineer set -- through a language switch or a reload -- sets it false.
    snug_on_show = True

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fit_rows()

    def showEvent(self, event):
        super().showEvent(event)
        if self.snug_on_show:
            self.snug_on_show = False
            QTimer.singleShot(0, self, self.snug)

    def snug_height(self):
        """The height that shows the bar at the pane's present width, every group and no row to spare."""
        bar = self.widget()
        width = max(self.viewport().width(), bar.layout().minimumSize().width())
        return bar.heightForWidth(width) + 2 * self.frameWidth()

    def snug(self):
        """Gives the drawing under it whatever height the bar does not use, once, when the tab is first shown. The splitter hands the pane the bar's height at Qt's first guess at its width -- 640 or 800 px, before anything is laid out -- which at the pane's real width may be a row more than the bar needs: an empty strip over the drawing, which is exactly the room the engineer asked the tools to give back.

        ⚠️ And a row fewer (v0.94): a guess wider than the pane is a bar too short to show every group, which then scrolls sideways at the window's own size -- the schemas' bar hid 700 px of its tools so. The pane then takes the row it lacks from the drawing, as long as the drawing keeps the most of its height.
        """
        split = self.parentWidget()
        if not isinstance(split, QSplitter):
            return
        index = split.indexOf(self)
        sizes = split.sizes()
        if index < 0 or index + 1 >= len(sizes):
            return
        spare = sizes[index] - max(self.snug_height(), self.minimumHeight())
        if spare > 0 or (spare < 0 and sizes[index + 1] + spare >= sizes[index + 1] // 2):
            sizes[index] -= spare
            sizes[index + 1] += spare
            split.setSizes(sizes)

    def fit_rows(self):
        """As many rows as the height now allows, and the width that needs.

        The rows are counted in the pane's whole height first, as if no scroll bar stood under the bar: where that many rows fit its width, none is needed and none takes a row's room. Counted in the viewport alone, a pane that had once shown the scroll bar kept it -- the bar laid out one row short in the room the scroll bar took, so the scroll bar stayed, although the pane held every group without it.
        """
        bar = self.widget().layout()
        row = bar.row_height()
        if row <= 0:
            return
        margins = bar.contentsMargins()

        def rows_in(height):
            room = height - margins.top() - margins.bottom()
            return max(1, (room + bar.spacing()) // (row + bar.spacing()))

        whole = self.height() - 2 * self.frameWidth()
        rows = rows_in(whole)
        want = bar.wrap_width(rows)
        if want > self.width() - 2 * self.frameWidth():
            rows = rows_in(whole - self.horizontalScrollBar().sizeHint().height())
            want = bar.wrap_width(rows)
        # only on a change: setMinimumWidth resizes the widget, which comes back here
        if want != self.widget().minimumWidth():
            self.widget().setMinimumWidth(want)

    def wheelEvent(self, event):
        """A vertical wheel scrolls the bar sideways, the only way it can scroll -- never up and down, which would hide a row with nothing to say so."""
        bar = self.horizontalScrollBar()
        delta = event.angleDelta()
        steps = delta.x() if abs(delta.x()) > abs(delta.y()) else delta.y()
        if steps and bar.maximum() > 0:
            bar.setValue(bar.value() - round(steps / 120.0 * bar.singleStep() * 3))
        event.accept()
