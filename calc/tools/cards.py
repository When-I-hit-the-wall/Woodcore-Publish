"""Forms in cards, after the website (v0.93, docs/ui/window.md §10quater): the second half of stage C, one tab at a time.

A card is a `QGroupBox` dressed by the window's style sheet as the site dresses a card -- its title inside it, in the ink and not in grey, on a ground of its own with a thin line round it and the site's radius -- laid one under the other on the soft ground of a column that scrolls (`column`). It stays a `QGroupBox` on purpose: a tab's own code, and every test that finds a box by its `title()`, go on working unchanged, and a box made a card is one call (`card`) where it was `QGroupBox(title)`.

What the style sheet reads here (theme.py): the property `card` on a box, the object name `cardGround` on the column's body and its viewport, `cardNote` on a card's explanation, `cardBadge` on a row's number (a member of a polar moment). Cards read side by side -- a connector's two pieces -- sit in a `Reflow`, which puts them one under the other where the column is narrower than the two. The colours are theme.json's: the column on `bg-soft`, the card on `card` -- white in the light scheme, a shade lighter than the column in the dark one, a raised surface being lighter there.
"""

import shiboken6
from PySide6.QtCore import QEvent, QObject, QSize, Qt, QTimer, Signal
from PySide6.QtWidgets import QAbstractSpinBox, QBoxLayout, QComboBox, QFormLayout, QGroupBox, QLabel, QLayout, QPushButton, QScrollArea, QSizePolicy, QStackedWidget, QVBoxLayout, QWidget


def card(title=""):
    """A box dressed as a card: `QGroupBox(title)` with the property the style sheet dresses (`QGroupBox[card="true"]`)."""
    box = QGroupBox(title)
    box.setProperty("card", True)
    return box


def form(parent=None):
    """A card's rows of «label field»: a `QFormLayout` whose label goes above its field where the two do not fit side by side (`WrapLongRows`), so that a long label -- «Visibilité de l'arrière-plan» -- sets the card's minimum width as the longer of the two and not as their sum."""
    layout = QFormLayout(parent) if parent is not None else QFormLayout()
    layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
    return layout


# What stands between a value and where it comes from, in the field that shows it: «C24 — T001» (the engineer, 07.10.2026: «lorsqu'une valeur est reprise d'une position, il est écrit "Repris de xxx". À la place, il doit simplement y avoir --- (long tiret) xxx»). The same in every language, so it is no word of a glossary.
FOLLOWED_DASH = " — "


def followed(value, source):
    """A value that follows its source, said in its own field: «C24 — T001», «120/240 mm — T001»; the source alone where there is no value to show («— T001»)."""
    value = str(value or "").strip()
    return f"{value}{FOLLOWED_DASH}{source}" if value else f"— {source}"


def note(text=""):
    """A card's explanation under its title: muted, wrapping -- in the title it would set the column's minimum width -- and never read as HTML."""
    label = QLabel(text)
    label.setObjectName("cardNote")
    label.setTextFormat(Qt.TextFormat.PlainText)
    label.setWordWrap(True)
    return label


class Reflow(QWidget):
    """Cards side by side where they have the room, one under the other where they do not -- as the site's grid sets its cards on a narrow screen. «Pièce 1» and «Pièce 2» of a connector are read side by side, which is how the classeur sets them; a pane narrower than the two (a window of 1440 px, the navigation shown) had them cut at its right edge.

    Its minimum is ONE card's width, so the column holding it (`Column`) asks for no more than that; its layout turns when its width crosses the two cards' side by side. It turns only on a resize, and the layout it invalidates asks its parent to be laid out again.
    """

    def __init__(self, spacing=10):
        super().__init__()
        self.row = QBoxLayout(QBoxLayout.Direction.LeftToRight, self)
        self.row.setContentsMargins(0, 0, 0, 0)
        self.row.setSpacing(spacing)
        self.row.setSizeConstraint(QLayout.SizeConstraint.SetNoConstraint)   # its own layout does not hold it to the two cards' width side by side, as it would a window

    def addWidget(self, widget):
        self.row.addWidget(widget, 1)

    def cards(self):
        return [self.row.itemAt(i).widget() for i in range(self.row.count()) if self.row.itemAt(i).widget() is not None]

    def side_by_side(self):
        """The width the cards take side by side: their minima and the spaces between them."""
        cards = self.cards()
        return sum(card.minimumSizeHint().width() for card in cards) + self.row.spacing() * max(len(cards) - 1, 0)

    def minimumSizeHint(self):
        hint = super().minimumSizeHint()
        cards = self.cards()
        if not cards:
            return hint
        return QSize(max(card.minimumSizeHint().width() for card in cards), hint.height())

    def resizeEvent(self, event):
        wanted = QBoxLayout.Direction.LeftToRight if event.size().width() >= self.side_by_side() else QBoxLayout.Direction.TopToBottom
        if self.row.direction() != wanted:
            self.row.setDirection(wanted)
        super().resizeEvent(event)


class Column(QScrollArea):
    """A scroll area that asks, as its minimum width, for the width of the cards it holds -- so a splitter never squeezes it below them and a card is never cut at its right edge, in whatever language and font."""

    def __init__(self, hold=True):
        super().__init__()
        self.hold = hold

    def eventFilter(self, watched, event):
        """A card grown or shrunk -- a member added, a selection shown -- asks its body to be laid out again: the column tells its own parent that its minimum has moved with it, where a splitter would go on holding the old one."""
        if event.type() == QEvent.Type.LayoutRequest and watched is self.widget() and self.hold:
            self.updateGeometry()
        return False

    def minimumSizeHint(self):
        hint = super().minimumSizeHint()
        body = self.widget()
        if not self.hold or body is None:
            return hint
        width = body.minimumSizeHint().width() + self.verticalScrollBar().sizeHint().width() + 2 * self.frameWidth()
        return QSize(max(hint.width(), width), hint.height())


def column(margins=(10, 10, 10, 10), spacing=10, hold=True):
    """A column of cards that scrolls up and down and never sideways: returns `(scroll, layout)`, the cards added to `layout` one under the other on the soft ground, a stretch left for the caller to add under the last.

    ⚠️ Never sideways, and never narrower than its cards (`hold`, `Column.minimumSizeHint`): the forms before cards were wider than their pane, a horizontal scroll bar under them and their buttons cut at their right edge. The column is not given a minimum width of its own, which would win over the hint; a column of what is read rather than typed -- a preview's results -- may pass `hold=False` and let the pane be narrower than it.
    """
    scroll = Column(hold)
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QScrollArea.Shape.NoFrame)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    body = QWidget()
    body.setObjectName("cardGround")
    body.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)  # a plain QWidget paints a style sheet's background only when told to
    layout = QVBoxLayout(body)
    layout.setContentsMargins(*margins)
    layout.setSpacing(spacing)
    scroll.setWidget(body)
    body.installEventFilter(scroll)   # its layout requests reach the column (Column.eventFilter)
    scroll.viewport().setObjectName("cardGround")  # under a body shorter than the pane, the viewport shows: the same ground
    scroll.viewport().setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    return scroll, layout


class SizedBox(QWidget):
    """A box of a pane's column whose height is its own (v0.117, the engineer: «les text-box du volet de gauche doivent pouvoir être manuellement élargis ou réduit vers le bas sans modifier la hauteur des autres»): the grip along its bottom edge drags its height, and its alone -- the boxes under it move down, the column scrolls where they no longer fit (`Column`). A box never dragged shares the height the column has with the others, as a splitter's panes did; once dragged it keeps its height (`height_set`), never below what its content needs (`minimumSizeHint`). `resized` says a drag ended, for the tab to remember it.

    ⚠️ It replaced the plan tabs' vertical splitter (v0.116), which was the defect itself: a splitter fills the height it is given, so the column under it never scrolled, and a handle dragged took its height from the box beside it.
    """

    resized = Signal()

    def __init__(self, content, parent=None):
        super().__init__(parent)
        self.content = content
        self.height_set = None
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)
        v.addWidget(content, 1)
        self.grip = _Grip(self)
        v.addWidget(self.grip)

    def set_height(self, height):
        """`height` the box's own, or None for a share of the column's; held at what its content needs."""
        if height is None:
            self.height_set = None
            self.setMinimumHeight(0)
            self.setMaximumHeight(16777215)
            self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        else:
            self.height_set = max(int(height), self.least_height())
            self.setFixedHeight(self.height_set)
            self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        parent = self.parentWidget()
        if parent is not None and parent.layout() is not None:
            parent.layout().invalidate()

    def least_height(self):
        return self.content.minimumSizeHint().height() + self.grip.sizeHint().height()


class _Grip(QWidget):
    """The bottom edge of a SizedBox: dragged, the box's height follows the pointer."""

    def __init__(self, box):
        super().__init__(box)
        self.box = box
        self.setFixedHeight(7)
        self.setCursor(Qt.CursorShape.SizeVerCursor)
        self.setObjectName("sizeGrip")
        self.start = None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.start = (event.globalPosition().y(), self.box.height())
            event.accept()

    def mouseMoveEvent(self, event):
        if self.start is not None:
            y0, h0 = self.start
            self.box.set_height(h0 + event.globalPosition().y() - y0)
            event.accept()

    def mouseReleaseEvent(self, event):
        if self.start is not None:
            self.start = None
            self.box.resized.emit()
            event.accept()


class CurrentStack(QStackedWidget):
    """A stack whose size is its current page's. A QStackedWidget asks for the largest of its pages, so the command builder's options or the document view's bar would set the plan's panes' minimum widths, and the splitter would lose the play it was given in v0.67 (tests/test_panes.py). Here since v0.117, the «Affichage» views stacking every tab's panes the same way (display_view.ViewPanes); drawing_tab.py's until then."""

    def sizeHint(self):
        page = self.currentWidget()
        return page.sizeHint() if page is not None else super().sizeHint()

    def minimumSizeHint(self):
        page = self.currentWidget()
        return page.minimumSizeHint() if page is not None else super().minimumSizeHint()

    def show_page(self, index):
        self.setCurrentIndex(index)
        self.updateGeometry()


# --- a tab's left pane, narrowed at will (issue #10) -----------------------------------------------------------------

PANE_FLOOR = 120   # px: the narrowest a tab's own left pane may be dragged, every tab alike (issue #10, «pouvoir le réduire bien plus»); its contents give way under it (`loosen`) rather than holding it wider
ELIDE_LEAST = 36   # px: the narrowest a button of such a pane is squeezed to -- an ellipsis and a letter or two, its whole text in its tooltip
SPIN_LEAST = 44   # px: the narrowest a number box of such a pane is squeezed to -- two or three digits and its arrows


class _Elider(QObject):
    """Keeps a push button's text to the width it is given: cut with an ellipsis where it is narrower than its words, whole again where it widens, the whole text in its tooltip while it is cut. The text a tab sets later (a language switched, a label changed) is taken as the new whole -- anything but what this filter itself last wrote."""

    pending = set()   # the buttons whose fit is asked for and not yet done

    def eventFilter(self, button, event):
        if event.type() in (QEvent.Type.Resize, QEvent.Type.Show) and isinstance(button, QPushButton) and id(button) not in self.pending:
            # fitted on the next turn of the loop and never inside the resize: a text set lays its row out again, which resizes the button beside it, whose fit would set its text inside this one -- a chain as deep as the pane has buttons
            self.pending.add(id(button))
            QTimer.singleShot(0, lambda button=button: self.later(button))
        return False

    def later(self, button):
        self.pending.discard(id(button))
        if shiboken6.isValid(button):
            self.fit(button)

    @staticmethod
    def fit(button):

        shown = button.property("elidedShown")
        if shown is None or button.text() != shown:
            button.setProperty("elidedWhole", button.text())
        whole = button.property("elidedWhole") or ""
        metrics = button.fontMetrics()
        padding = button.sizeHint().width() - metrics.horizontalAdvance(button.text())
        text = metrics.elidedText(whole, Qt.TextElideMode.ElideRight, max(0, button.width() - padding))
        if text != button.text():
            button.setProperty("elidedShown", text)
            button.setText(text)
        else:
            button.setProperty("elidedShown", text)
        tip = button.property("elidedTip")
        if text != whole and (not button.toolTip() or tip):
            button.setToolTip(whole)
            button.setProperty("elidedTip", True)
        elif text == whole and tip:
            button.setToolTip("")
            button.setProperty("elidedTip", False)


_ELIDER = None


def loosen(widget):
    """What holds a left pane wider than `PANE_FLOOR`, let go (issue #10): every push button may be squeezed to `ELIDE_LEAST`, its text cut with an ellipsis (`_Elider`), every label of plain words wraps, every drop-down asks for a few letters rather than its longest entry, every number box for a few digits (`SPIN_LEAST`). Lists and trees scroll already. Called once on a pane's content (chrome.FoldablePane); a widget added later is the tab's to loosen, or holds the pane at its own width -- which is the old behaviour and never a cut.

    ⚠️ The buttons are squeezed by their minimum width, which Qt's layouts take over their hint (qSmartMinSize), and never by their size policy: an `Ignored` button beside a stretch would be laid out at nothing."""
    global _ELIDER
    if _ELIDER is None:
        _ELIDER = _Elider()
    for button in widget.findChildren(QPushButton):
        button.setMinimumWidth(min(ELIDE_LEAST, button.sizeHint().width()))
        button.installEventFilter(_ELIDER)
    for label in widget.findChildren(QLabel):
        if label.pixmap() is None or label.pixmap().isNull():
            if label.text() and not label.wordWrap() and label.minimumSizeHint().width() > PANE_FLOOR // 2:
                label.setWordWrap(True)
    for combo in widget.findChildren(QComboBox):
        combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        combo.setMinimumContentsLength(min(combo.minimumContentsLength() or 6, 6))
    for spin in widget.findChildren(QAbstractSpinBox):
        spin.setMinimumWidth(min(SPIN_LEAST, spin.minimumSizeHint().width()))   # a number box asks for its widest number and its arrows: a few digits are enough, as many as the box shows
