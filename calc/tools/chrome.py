"""The window's frame, after the website's (docs/ui/window.md §10quater, v0.91): the module icons, the segmented language switch, the grouped side navigation that replaces the row of tabs -- with, at its top, the drop-down of the three documents a project is written as (30.09.2026) -- and the start page's cards.

What is here draws the frame and nothing else: which module a row opens is an index of the window's own QTabWidget, which stays -- its tab bar hidden -- so that every tab, every test and every `tab_widget.setCurrentWidget` works as it did. Every colour is the scheme's (theme.py), read when a row is painted, so a switch of scheme repaints the frame without building it again.
"""

import functools

from PySide6.QtCore import QEvent, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QActionGroup, QColor, QFont, QIcon, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QAbstractItemView, QButtonGroup, QComboBox, QFrame, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMenu,
    QSizePolicy, QStyle, QStyledItemDelegate, QToolButton, QVBoxLayout, QWidget,
)

import theme
from svg_icons import pixel_ratio, svg_pixmap

# --- the icons -------------------------------------------------------------------------------------------------
# Line icons on a 24-unit square, drawn in one ink: the site's own feature icons are of this kind. Each says what its module draws or computes -- a floor plan, the sheet of positions, loads onto a beam, a sum, a beam on two supports, a joint, a bolt, a turn about a centre, a pair of brackets -- and none is a picture of a product. SVG Tiny: no arc command, circles and polylines only (docs/domain/connections.md §3.3quinquies).
ICONS = {
    # A document's outline: a heading, and under it its two sections, hung on one line -- what «Structure du document» lists. Drawn as an indented list and not as a tree of boxes, which `tab_schema`'s pieces already are.
    "tab_project": '<path d="M3 21h18"/><path d="M5 21V9l7-5 7 5v12"/><path d="M10 21v-6h4v6"/>',
    "tab_structure": '<path d="M4 5h16"/><path d="M8 5v12h3M8 11h3"/><path d="M13 11h7M13 17h7"/>',
    "tab_plan": '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 10h8v11M11 3v4M15 10h6"/>',
    "tab_fire": '<path d="M12 3c1 3 5 5.5 5 10c0 2.8-2.2 5-5 5s-5-2.2-5-5c0-1.7.7-3 1.8-4 .2 1.3.9 2 1.7 2.2C10.2 8.4 10.7 5.6 12 3z"/>',
    "tab_positions": '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 9h18M3 14.5h18M9 4v16"/>',
    "tab_metre": '<rect x="2" y="8" width="20" height="8" rx="1.5"/><path d="M6 8v3M10 8v4M14 8v3M18 8v4"/>',
    # A revised page: the sheet with its folded corner, its lines, and the triangle a drawing marks a revision with. Kept away from the positions sheet's grid, which it would otherwise be read as.
    "tab_journal": '<path d="M6 3h8l4 4v14H6z"/><path d="M14 3v4h4"/><path d="M9 11l1.6-2.7L12.2 11z"/><path d="M9 14.5h6M9 18h6"/>',
    # The six tabs of «Actions» (action_tabs.py, v0.117), each drawn as what it is: a block on its support under its own weight; layers over it; a load put on a floor; a snowflake; wind round a line; the ground shaking.
    "tab_ac_selfweight": '<rect x="6" y="9" width="12" height="7"/><path d="M12 2.5v4M9.7 4.3L12 6.6l2.3-2.3"/><path d="M3 20h18M6 16v4M18 16v4"/>',
    "tab_ac_imposed": '<rect x="9" y="8" width="6" height="6" rx="1"/><path d="M12 3v3"/><path d="M3 20h18M9 14v6M15 14v6"/>',
    "tab_ac_snow": '<path d="M12 3v18M4.2 7.5l15.6 9M4.2 16.5l15.6-9"/><path d="M10 4.5l2 1.5 2-1.5M10 19.5l2-1.5 2 1.5"/>',
    "tab_ac_wind": '<path d="M3 9h11a3 3 0 1 0-3-3"/><path d="M3 14h16a3 3 0 1 1-3 3"/>',
    "tab_ac_seismic": '<path d="M2 14l3-3 3 6 3-9 3 12 3-6 3 3 2-3"/>',
    "tab_combinations": '<path d="M18 5H6l6 7-6 7h12"/>',
    # a paper clip: what is attached to the report from outside (v0.115)
    "tab_annexes": '<path d="M16.5 7.5l-7 7a2 2 0 0 0 2.8 2.8l7.4-7.4a4 4 0 0 0-5.6-5.6l-7.4 7.4a6 6 0 0 0 8.5 8.5l6.3-6.3"/>',
    # a formula's two lines: what it is in letters, and the same with its numbers -- the «Formule» tab's blocks (v0.117)
    "tab_formula": '<path d="M4 7h4M6 5v4"/><path d="M11 7h9"/><path d="M4 17h4"/><path d="M11 15h9M11 19h9"/>',
    "tab_python": '<path d="M9 8l-4 4 4 4"/><path d="M15 8l4 4-4 4"/>',
    "tab_statics": '<path d="M2 9h20"/><path d="M5 9l-2.5 5h5z"/><path d="M19 9l-2.5 5h5z"/><path d="M2 17h6M16 17h6"/>',
    "tab_schema": '<rect x="3" y="4" width="18" height="6" rx="1"/><rect x="9" y="10" width="6" height="11" rx="1"/>',
    "tab_connections": '<path d="M8 3h8v4H8z"/><path d="M12 7v14"/><path d="M9.5 10l5 1.5M9.5 13.5l5 1.5M9.5 17l5 1.5"/>',
    "tab_polar": '<circle cx="12" cy="12" r="1.6"/><circle cx="12" cy="12" r="7.5" stroke-dasharray="36 11"/><path d="M19.2 4.4l.3 4.4-4.3-.6"/>',
    # Names at the left and their values at the right, which is what the tab lists: two columns, and no chevron, which `tab_python` and `tab_commands` both already are.
    "tab_variables": '<path d="M4 7h3M11 7h9"/><path d="M4 12h3M11 12h6"/><path d="M4 17h3M11 17h8"/>',
    "tab_commands": '<path d="M9 7l-5 5 5 5M15 7l5 5-5 5"/>',
    # Three objects, one reading the two others: what the «Dépendances» tab lists (issue #71).
    "tab_dependencies": '<circle cx="5" cy="12" r="2.2"/><circle cx="19" cy="6" r="2.2"/><circle cx="19" cy="18" r="2.2"/><path d="M7 11l9.8-4M7 13l9.8 4"/>',
    # The member checks of SIA 265 chapter 4 (member_check_tab.py), each drawn as the action it checks: a bar pulled at both ends, pressed at both ends, bent under a load, sheared, twisted, a column bowed and a beam tipping over, then -- serviceability -- a beam sagging under its original line and a wave.
    "tab_mc_tension": '<rect x="8" y="10" width="8" height="4"/><path d="M8 12H3M5.5 9.5L3 12l2.5 2.5"/><path d="M16 12h5M18.5 9.5L21 12l-2.5 2.5"/>',
    "tab_mc_compression": '<rect x="8" y="10" width="8" height="4"/><path d="M2 12h6M5 9.5L8 12l-3 2.5"/><path d="M22 12h-6M19 9.5L16 12l3 2.5"/>',
    "tab_mc_bending": '<path d="M3 9q9 9 18 0"/><path d="M12 2v7M9.5 6.5L12 9l2.5-2.5"/>',
    "tab_mc_shear": '<rect x="7" y="8" width="10" height="8"/><path d="M5 18V6M3 8.5L5 6l2 2.5"/><path d="M19 6v12M17 15.5L19 18l2-2.5"/>',
    "tab_mc_torsion": '<path d="M4 12h16"/><path d="M8 6c3 2 3 10 0 12"/><path d="M16 6c-3 2-3 10 0 12"/>',
    "tab_mc_buckling": '<path d="M12 3c-4 6 4 12 0 18"/><path d="M8 3h8M8 21h8"/>',
    "tab_mc_ltb": '<path d="M4 6h10M9 6v12M4 18h10"/><path d="M17 8l4 4-4 4"/>',
    # issue #46: a beam's section under a flame -- the section and, over it, the flame the residual section is computed for
    "tab_mc_fire": '<rect x="7" y="13" width="10" height="8"/><path d="M12 2c2 3 4 4 4 7a4 4 0 0 1-8 0c0-2 1-3 2-4 0 2 1 3 2 3 0-2-1-4 0-6z"/>',
    "tab_sls_deformation": '<path d="M3 8h18" stroke-dasharray="3 3"/><path d="M3 8q9 10 18 0"/>',
    # «Acier» (issues #50-#52): an I in section, its plates marked; a bar pulled, pressed, bent, sheared -- the timber checks' figures on a steel I
    "tab_st_profiles": '<path d="M6 4h12M6 20h12M12 4v16"/><path d="M4 4h4M16 4h4M4 20h4M16 20h4"/>',
    "tab_st_class": '<path d="M6 4h12M6 20h12M12 4v16"/><path d="M15 9l3 3-3 3"/>',
    "tab_st_tension": '<path d="M2 12h20"/><path d="M5 9l-3 3 3 3M19 9l3 3-3 3"/><path d="M10 9h4v6h-4z"/>',
    "tab_st_compression": '<path d="M2 12h20"/><path d="M6 9l3 3-3 3M18 9l-3 3 3 3"/><path d="M10 9h4v6h-4z"/>',
    "tab_st_bending": '<path d="M3 9q9 8 18 0"/><path d="M3 13q9 8 18 0"/><path d="M12 3v4"/>',
    "tab_st_shear": '<path d="M4 7h16v10H4z"/><path d="M9 3v6M15 21v-6"/>',
    "tab_sls_vibration": '<path d="M3 12h3l2-6 3 12 3-12 2 6h5"/>',
    # A chain of two links: the mark of a section file shared with another document, in the structure tree (structure_tree.py). Rounded rectangles and no arc, which SVG Tiny reads alike everywhere.
    "badge_link": '<rect x="2.5" y="8.5" width="11" height="7" rx="3.5"/><rect x="10.5" y="8.5" width="11" height="7" rx="3.5"/>',
    # What a row of the structure tree is (structure_tree.py): a chapter, a section and the objects a section holds -- each drawn as what it prints, in the one ink, small enough for a row.
    "kind_group": '<path d="M3 6h6l2 2h10v11H3z"/>',
    "kind_file": '<path d="M6 3h8l4 4v14H6z"/><path d="M14 3v4h4"/>',
    "kind_heading": '<path d="M6 5v14M18 5v14M6 12h12"/>',
    "kind_text": '<path d="M4 7h16M4 12h16M4 17h10"/>',
    "kind_table": '<rect x="3" y="5" width="18" height="14" rx="1"/><path d="M3 10h18M9 5v14"/>',
    "kind_norms": '<path d="M5 4h14v16H8l-3-3z"/><path d="M9 8h6M9 12h6"/>',
    "home_new": '<path d="M3 5h6l2 2h10v12H3z"/><path d="M12 10v6M9 13h6"/>',
    "home_open": '<path d="M3 5h6l2 2h8v3"/><path d="M3 5v14h15l3-8H7l-4 8"/>',
    "nav_collapse": '<path d="M15 6l-6 6 6 6"/>',
    "nav_expand": '<path d="M9 6l6 6-6 6"/>',
}


@functools.lru_cache(maxsize=256)
def _pixmap(key, colour, size, ratio):
    """A symbol of ICONS in `colour`, `size` logical pixels square -- cached by the screen's `ratio` too, so a window moved to another screen renders it anew."""
    body = ICONS[key]
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{colour}" '
           f'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{body}</svg>')
    return svg_pixmap(svg, size)


def icon(key, colour=None, size=18):
    """One of ICONS in `colour` -- the scheme's ink where none is given -- `size` logical pixels square, drawn at the screen's pixel ratio."""
    return QIcon(_pixmap(key, colour or theme.colour("ink-soft"), size, pixel_ratio()))


# --- the segmented switches: the language and the view ----------------------------------------------------------

class SegmentedSwitch(QWidget):
    """A row of buttons of which one is down, the site's segmented control: `items` is [(key, text, tip), ...]. Emits `changed(key)` when the engineer presses another -- never when the program sets one (`set_current`). `set_items` replaces the buttons, keeping the one down where its key is still there: the view switch of the top bar (v0.117) shows the views of the tab in front and is given another tab's views as the engineer moves between tabs. Styled by the `segment` property (theme.py), as the language switch always was."""

    changed = Signal(str)

    def __init__(self, items=(), current=None, parent=None, soft=False):
        super().__init__(parent)
        self.soft = soft    # the button down only lightly set apart (the `soft` property, theme.py): a value among others, as the level -1 rows of «Affichage» are (issue #41), where the bar's switches mark theirs in ink
        self.row = QHBoxLayout(self)
        self.row.setContentsMargins(0, 0, 0, 0)
        self.row.setSpacing(0)
        self.group = QButtonGroup(self)
        self.group.setExclusive(True)
        self.group.idClicked.connect(self._clicked)
        self.keys = []
        self.set_items(items, current)

    def set_items(self, items, current=None):
        items = list(items)
        keep = current if current is not None else self.current_key()
        for button in self.group.buttons():
            self.group.removeButton(button)
            self.row.removeWidget(button)
            button.deleteLater()
        self.keys = [key for key, _text, _tip in items]
        for i, (key, text, tip) in enumerate(items):
            button = QToolButton()
            button.setText(text)
            button.setToolTip(tip or "")
            button.setCheckable(True)
            button.setProperty("segment", "first" if i == 0 else "last" if i == len(items) - 1 else "middle")
            if self.soft:
                button.setProperty("soft", True)
            button.setAutoRaise(False)
            button.setObjectName(f"segment_{key}")
            self.group.addButton(button, i)
            self.row.addWidget(button)
        if self.keys:
            self.group.button(self.keys.index(keep) if keep in self.keys else 0).setChecked(True)

    def _clicked(self, index):
        self.changed.emit(self.keys[index])

    def current_key(self):
        index = self.group.checkedId()
        return self.keys[index] if 0 <= index < len(self.keys) else None

    def set_current(self, key):
        """Presses `key`'s button without saying so: the program follows the tab, the engineer is not answered."""
        if key in self.keys and key != self.current_key():
            self.group.button(self.keys.index(key)).setChecked(True)

    def button(self, key):
        return self.group.button(self.keys.index(key)) if key in self.keys else None


class LanguageSwitch(SegmentedSwitch):
    """FR · DE · EN, the site's segmented control, where the window had a combo box. It answers the part of QComboBox's interface the window and its tests use -- `currentIndex`, `setCurrentIndex`, `itemData`, `count`, `currentIndexChanged` -- so it took the combo's place with nothing around it changed. A `SegmentedSwitch` since v0.117, the view switch beside it being another."""

    currentIndexChanged = Signal(int)

    def __init__(self, languages, current, parent=None):
        self.codes = list(languages)
        self.names = dict(languages)
        super().__init__([(code, code.upper(), self.names[code]) for code in self.codes], current if current in self.codes else None, parent)
        self.changed.connect(lambda code: self.currentIndexChanged.emit(self.codes.index(code)))

    def count(self):
        return len(self.codes)

    def currentIndex(self):
        return self.group.checkedId()

    def setCurrentIndex(self, index):
        if index != self.currentIndex() and 0 <= index < len(self.codes):
            self.group.button(index).setChecked(True)
            self.currentIndexChanged.emit(index)

    def itemData(self, index):
        return self.codes[index]

    def itemText(self, index):
        return self.names[self.codes[index]]


# --- the fold button -----------------------------------------------------------------------------------------------

class FoldButton(QToolButton):
    """The chevron at the foot of a pane that folds it away and back: the side navigation's since v0.91, the plan tabs' left pane's since v0.117 (the engineer: «similaire que pour le volet entièrement à gauche»). `tips` is (the tip while open, the tip while folded); `set_folded` turns the chevron, `clicked` is the caller's to answer."""

    def __init__(self, tips=("", ""), parent=None):
        super().__init__(parent)
        self.setObjectName("fold")
        self.setAutoRaise(True)
        self.tips = tuple(tips)
        self.folded = False
        self.set_folded(False)

    def set_folded(self, folded):
        self.folded = bool(folded)
        self.setIcon(icon("nav_expand" if self.folded else "nav_collapse", theme.colour("muted"), 16))
        self.setToolTip(self.tips[1] if self.folded else self.tips[0])



class FoldablePane(QWidget):
    """A tab's own left pane -- its list or its tree, the second pane from the left -- with the arrow at its foot that folds it away and back (issue #10: «fermer ce volet dans tous les onglets»), and a floor every tab shares (cards.PANE_FLOOR, «pouvoir le réduire bien plus»). Built once here and put round every tab's pane by the window (woodcore_gui.bind_layout); the plan tabs' pane of v0.117 is the same object (drawing_tab.build_list).

    Folded, the pane is its arrow's width and no more, the splitter's sizes from before kept to be given back (`sizes`); the content is hidden, not taken out, so a tab's references to it stand. `foldedChanged` says the arrow was clicked, for the window to remember it (the setting `left_folded`).

    ⚠️ Folded by a fixed width and never by the splitter's own collapse (`setCollapsible`): a pane collapsed by a drag has no arrow to come back by, and its layout (layout_store) would remember a fraction of nothing -- a pane gone at the next start with nothing to show it was ever there.
    """

    foldedChanged = Signal(bool)

    def __init__(self, content, tips=("", ""), parent=None):
        super().__init__(parent)
        import cards
        self.setObjectName("foldablePane")
        self.content = content
        self.folded = False
        self.sizes = None
        cards.loosen(content)
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)
        v.addWidget(content, 1)
        foot = QHBoxLayout()
        foot.setContentsMargins(2, 2, 2, 2)
        self.fold = FoldButton(tips)
        self.fold.clicked.connect(self.toggle)
        foot.addWidget(self.fold)
        foot.addStretch(1)
        v.addLayout(foot)

    def minimumSizeHint(self):
        """Never below the floor while open, never wider than what the content still holds after `cards.loosen` -- a content that cannot give way keeps the pane at its own width, which is a wider pane and never a cut one."""
        import cards
        hint = super().minimumSizeHint()
        if self.folded:
            return hint
        return QSize(max(cards.PANE_FLOOR, hint.width()), hint.height())

    def splitter(self):
        from PySide6.QtWidgets import QSplitter
        parent = self.parentWidget()
        return parent if isinstance(parent, QSplitter) else None

    def toggle(self):
        self.set_folded(not self.folded)
        self.foldedChanged.emit(self.folded)

    def set_folded(self, folded):
        """Folded to the arrow, or open again at the width it had (the navigation's fold, for this pane).

        The width it frees goes to its neighbour -- the centre pane -- at once, and is taken back from it on unfolding (issue #91: the centre came up to the arrow only once the window was resized, a fixed width alone never asking the splitter to share out again). The unfold takes back only this pane's own width and not the whole list kept at folding, which a window resized meanwhile has made stale."""
        folded = bool(folded)
        if folded == self.folded:
            return
        splitter = self.splitter()
        self.folded = folded
        self.fold.set_folded(folded)
        self.content.setVisible(not folded)
        if folded:
            self.sizes = splitter.sizes() if splitter is not None else None
            arrow = self.fold.sizeHint().width() + 4
            self.setFixedWidth(arrow)
            if self.sizes:
                self._share(splitter, arrow)
        else:
            self.setMinimumWidth(0)
            self.setMaximumWidth(16777215)
            if self.sizes and splitter is not None:
                self._share(splitter, self.sizes[splitter.indexOf(self)])
        self.updateGeometry()

    def _share(self, splitter, width):
        """This pane set to `width` in `splitter`, the difference given to or taken from its neighbour -- the next pane, or the one before where it is the last -- and the others left as they are."""
        sizes = splitter.sizes()
        index = splitter.indexOf(self)
        if index < 0 or len(sizes) < 2:
            return
        neighbour = index + 1 if index + 1 < len(sizes) else index - 1
        moved = sizes[index] - width
        sizes[neighbour] = max(0, sizes[neighbour] + moved)
        sizes[index] = width
        splitter.setSizes(sizes)

# --- the side navigation -----------------------------------------------------------------------------------------

KIND = Qt.ItemDataRole.UserRole + 1     # "group", "section" (a sub-title inside a group, v0.117) or "entry"
INDEX = Qt.ItemDataRole.UserRole        # an entry's tab index
DIRTY = Qt.ItemDataRole.UserRole + 2    # an entry's unsaved changes
ICON_KEY = Qt.ItemDataRole.UserRole + 3
TITLE = Qt.ItemDataRole.UserRole + 4   # a group's own title (v0.117)
FOLDED = Qt.ItemDataRole.UserRole + 5  # whether a group is folded, its rows hidden (v0.117)
OFF = Qt.ItemDataRole.UserRole + 6     # an entry the document shown cannot open yet -- its document not made (issue #90): greyed, not chosen, not counted by Ctrl+1 … Ctrl+9

EXPANDED_WIDTH = 214
COLLAPSED_WIDTH = 52
# How wide the navigation may be dragged, unfolded (v0.117, the engineer: «la largeur du volet tout à gauche doit pouvoir être modifiée»); its grip, at its right edge, this many pixels wide.
MIN_EXPANDED_WIDTH = 150
MAX_EXPANDED_WIDTH = 420
GRIP_PX = 5
ENTRY_HEIGHT = 32
GROUP_HEIGHT = 30
SECTION_HEIGHT = 26   # a sub-title inside a group; an empty one is only a thin line, SECTION_LINE high
SECTION_LINE = 10


class NavDelegate(QStyledItemDelegate):
    """Paints a row of the navigation the way the site's sidebar sets one: a group's name in small capitals, muted; an entry with its icon and its name, the chosen one on the accent's soft ground; a dot at its right while its module holds unsaved changes -- the tab's mark of section 10quater, which the hidden tab bar still carries too."""

    def __init__(self, nav):
        super().__init__(nav)
        self.nav = nav

    def sizeHint(self, option, index):
        if index.data(KIND) == "group":
            return QSize(10, theme.scaled(12 if self.nav.collapsed else GROUP_HEIGHT))
        if index.data(KIND) == "section":
            return QSize(10, theme.scaled(SECTION_LINE if self.nav.collapsed or not index.data(Qt.ItemDataRole.DisplayRole) else SECTION_HEIGHT))
        return QSize(10, theme.scaled(ENTRY_HEIGHT))

    def paint(self, painter, option, index):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = option.rect
        if index.data(KIND) == "section":
            title = index.data(Qt.ItemDataRole.DisplayRole)
            if self.nav.collapsed or not title:
                # folded to the icons, or a section with no name: a thin line, which only parts what is above from what is below
                painter.setPen(QPen(QColor(theme.colour("line")), 1))
                y = rect.center().y()
                painter.drawLine(rect.left() + 16, y, rect.right() - 16, y)
            else:
                font = QFont(option.font)
                font.setBold(True)
                font.setPointSizeF(max(6.5, option.font.pointSizeF() * 0.9))
                painter.setFont(font)
                painter.setPen(QColor(theme.colour("ink-soft")))
                painter.drawText(rect.adjusted(16, 6, -8, 0), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, title)
            painter.restore()
            return
        if index.data(KIND) == "group":
            if self.nav.collapsed:
                painter.setPen(QPen(QColor(theme.colour("line")), 1))
                y = rect.center().y()
                painter.drawLine(rect.left() + 12, y, rect.right() - 12, y)
            else:
                font = QFont(option.font)
                font.setBold(True)
                font.setPointSizeF(max(6.5, option.font.pointSizeF() * 0.82))
                font.setLetterSpacing(QFont.SpacingType.PercentageSpacing, 108)
                painter.setFont(font)
                painter.setPen(QColor(theme.colour("muted")))
                painter.drawText(rect.adjusted(14, 8, -8, 0), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, index.data(Qt.ItemDataRole.DisplayRole).upper())
                # its arrow at its right: folded ▸, unfolded ▾ -- a click on the title folds it (v0.117)
                painter.drawText(rect.adjusted(14, 8, -12, 0), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, "▸" if index.data(FOLDED) else "▾")
            painter.restore()
            return
        off = bool(index.data(OFF))
        selected = bool(option.state & QStyle.StateFlag.State_Selected) and not off
        hovered = bool(option.state & QStyle.StateFlag.State_MouseOver) and not off
        box = QRectF(rect.adjusted(6, 1, -6, -1))
        if selected or hovered:
            path = QPainterPath()
            path.addRoundedRect(box, 7, 7)
            painter.fillPath(path, QColor(theme.colour("accent-soft" if selected else "bg-soft")))
        ink = theme.colour("muted" if off else "accent-strong" if selected else "ink-soft")
        size = 18
        if self.nav.collapsed:
            x = rect.center().x() - size / 2
        else:
            x = rect.left() + 16
        y = rect.center().y() - size / 2
        painter.drawPixmap(round(x), round(y), _pixmap(index.data(ICON_KEY), ink, size, pixel_ratio()))
        if not self.nav.collapsed:
            font = QFont(option.font)
            font.setWeight(QFont.Weight.DemiBold if selected else QFont.Weight.Normal)
            painter.setFont(font)
            painter.setPen(QColor(ink if selected or off else theme.colour("ink")))
            text_rect = rect.adjusted(16 + size + 10, 0, -24, 0)
            text = painter.fontMetrics().elidedText(index.data(Qt.ItemDataRole.DisplayRole), Qt.TextElideMode.ElideRight, text_rect.width())
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, text)
        if index.data(DIRTY):
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(theme.colour("ink")))
            if self.nav.collapsed:
                painter.drawEllipse(QRectF(x + size - 1, y - 2, 6, 6))
            else:
                painter.drawEllipse(QRectF(rect.right() - 20, rect.center().y() - 3, 6, 6))
        painter.restore()


class SideNav(QWidget):
    """The window's modules, grouped as the site's sidebar groups its pages -- `groups` is [(group title, [(tab index, name, icon key), ...]), ...] -- with, at its foot, the button that folds it to its icons and back. Emits `chosen(index)` with the tab index of the entry clicked or reached with the keyboard.

    **The document a project is written as** (the engineer's request of 30.09.2026): `modes` is [(code, name), ...] -- calc/documents.py's `mode_choices`, the convention d'utilisation, the base de projet and the report -- and `mode` the one shown. Where it is given, a drop-down (object name `modeSelect`) stands at the top of the navigation, above the first group, and `modeChanged(code)` says the engineer chose another; folded to its icons, the drop-down gives way to a button showing the document's number, 1, 2 or 3, whose menu offers the three. A project laid out as a report alone has one document and is given no `modes`: it shows no drop-down at all. Which rows a document shows is the window's to say (`set_visible`); a row hidden is left out of `order`, which is what Ctrl+1 … Ctrl+9 count by, and a group whose every row is hidden hides its title too.
    """

    chosen = Signal(int)
    collapsedChanged = Signal(bool)
    modeChanged = Signal(str)
    widthChanged = Signal(int)          # the width it was dragged to, unfolded (v0.117)
    foldedChanged = Signal(object)      # the titles of the groups folded (v0.117)

    def __init__(self, groups, collapsed=False, collapse_tip=("", ""), modes=None, mode=None, mode_tip="", parent=None, width=None, folded=()):
        super().__init__(parent)
        self.collapsed = bool(collapsed)
        self.collapse_tip = collapse_tip
        self.rows = {}
        self.groups = []   # [(the group's title row, [its entry rows])], for a title to be hidden with its last row
        self.sections = []   # [(a sub-title row, [the entry rows it holds], its group's title row)] (v0.117): hidden with its last row, and with its group when that is folded
        # v0.117: a group folded by a click on its title, its rows hidden -- kept apart from what the document shows (`set_visible`), so that a folded group neither shows a row the document hides nor takes one out of `order`, which Ctrl+1 … Ctrl+9 count by; and the width dragged at the grip
        self.folded = set(folded or ())
        self.shown = None   # the tab indices the document shows; None: all
        self.off = set()    # the tab indices it shows and cannot open yet (issue #90)
        self.expanded_width = max(MIN_EXPANDED_WIDTH, min(MAX_EXPANDED_WIDTH, int(width))) if width else EXPANDED_WIDTH
        self.modes = list(modes or ())
        self._mode = None
        column = QVBoxLayout(self)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(0)
        self.mode_select = self.mode_button = None
        if self.modes:
            self._build_modes(column, mode, mode_tip)
        self.list = QListWidget()
        self.list.setObjectName("nav")
        self.list.setMouseTracking(True)
        self.list.setUniformItemSizes(False)
        self.list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.list.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.delegate = NavDelegate(self)
        self.list.setItemDelegate(self.delegate)
        for title, entries in groups:
            head = QListWidgetItem(title)
            head.setData(KIND, "group")
            head.setFlags(Qt.ItemFlag.NoItemFlags)
            self.list.addItem(head)
            members = []
            section = None
            for index, name, key in entries:
                if index is None:
                    # a sub-title inside the group (v0.117: «Actions permanentes», «Actions variables»): `name` is its words, empty for a thin line only; it holds the entries that follow it, up to the next one
                    row = QListWidgetItem(name)
                    row.setData(KIND, "section")
                    row.setFlags(Qt.ItemFlag.NoItemFlags)
                    self.list.addItem(row)
                    section = (row, [], head)
                    self.sections.append(section)
                    continue
                item = QListWidgetItem(name)
                item.setData(KIND, "entry")
                item.setData(INDEX, index)
                item.setData(ICON_KEY, key)
                item.setData(DIRTY, False)
                item.setToolTip(name)
                self.list.addItem(item)
                self.rows[index] = item
                members.append(item)
                if section is not None:
                    section[1].append(item)
            self.groups.append((head, members))
            head.setData(TITLE, title)
        self.list.currentItemChanged.connect(self._current)
        self.list.viewport().installEventFilter(self)
        column.addWidget(self.list, 1)
        foot = QHBoxLayout()
        foot.setContentsMargins(6, 4, 6, 6)
        self.fold = FoldButton(collapse_tip)
        self.fold.clicked.connect(lambda: self.set_collapsed(not self.collapsed))
        foot.addWidget(self.fold)
        foot.addStretch(1)
        column.addLayout(foot)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self.grip = _WidthGrip(self)
        self._refresh_rows()
        self._apply_width()

    def _build_modes(self, column, mode, tip):
        """The drop-down of the documents, at the top of the navigation, and the button that stands for it while the navigation is folded to its icons: the document's number, its menu the three documents. Both are set from `mode`; neither says anything until the engineer chooses (`_chosen_mode`)."""
        box = QHBoxLayout()
        box.setContentsMargins(8, 2, 8, 6)
        box.setSpacing(0)
        self.mode_select = QComboBox()
        self.mode_select.setObjectName("modeSelect")
        self.mode_select.setToolTip(tip)
        # the navigation's fixed width is what the drop-down has; a long name is cut rather than widening it
        self.mode_select.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.mode_select.setMinimumContentsLength(8)
        self.mode_select.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        for code, name in self.modes:
            self.mode_select.addItem(name, code)
        box.addWidget(self.mode_select)
        self.mode_button = QToolButton()
        self.mode_button.setObjectName("modeButton")
        self.mode_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.mode_button.setAutoRaise(False)
        self.mode_button.setFixedSize(theme.scaled(34), theme.scaled(28))
        # the number alone: in a button 34 px wide the menu's arrow would stand on top of it
        self.mode_button.setStyleSheet("QToolButton::menu-indicator { image: none; width: 0px; }")
        menu = QMenu(self.mode_button)
        self.mode_actions = QActionGroup(menu)
        self.mode_actions.setExclusive(True)
        for number, (code, name) in enumerate(self.modes, 1):
            action = menu.addAction(f"{number}  {name}")
            action.setCheckable(True)
            action.setData(code)
            self.mode_actions.addAction(action)
        self.mode_button.setMenu(menu)
        box.addWidget(self.mode_button, 0, Qt.AlignmentFlag.AlignHCenter)
        column.addLayout(box)
        self._mode = mode if mode in dict(self.modes) else self.modes[0][0]
        self._show_mode(self._mode)
        self.mode_select.currentIndexChanged.connect(lambda index: self._chosen_mode(self.mode_select.itemData(index)))
        self.mode_actions.triggered.connect(lambda action: self._chosen_mode(action.data()))

    def _show_mode(self, code):
        """`code` shown in the drop-down, the folded button and its menu, and nothing said."""
        codes = [c for c, _name in self.modes]
        index = codes.index(code)
        self.mode_select.blockSignals(True)
        self.mode_select.setCurrentIndex(index)
        self.mode_select.blockSignals(False)
        self.mode_button.setText(str(index + 1))
        self.mode_button.setToolTip(self.modes[index][1])
        for action in self.mode_actions.actions():
            action.setChecked(action.data() == code)

    def _chosen_mode(self, code):
        """The engineer chose document `code`: shown everywhere, and said once. The window may take it back (`set_mode`) where something unsaved keeps it on the document it was on."""
        if code is None or code == self._mode:
            self._show_mode(self._mode)
            return
        self._mode = code
        self._show_mode(code)
        self.modeChanged.emit(code)

    def mode(self):
        """The document shown, or None where the project has only one."""
        return self._mode

    def set_mode(self, code):
        """Shows document `code` without saying so -- what the window does when it keeps the engineer on the document he was on, or brings the navigation in step with a document chosen elsewhere."""
        if not self.modes or code not in dict(self.modes):
            return
        self._mode = code
        self._show_mode(code)

    def set_visible(self, indices):
        """Only the rows of `indices` shown, the others hidden -- and a group's title hidden where every one of its rows is. What a document shows (the window's MODE_TABS); `order` then lists the rows shown and nothing else."""
        self.shown = set(indices)
        self._refresh_rows()

    def _shows(self, item):
        return self.shown is None or item.data(INDEX) in self.shown

    def set_unavailable(self, indices, tip=""):
        """The rows of `indices` shown greyed, `tip` saying why, and neither chosen nor counted by Ctrl+1 … Ctrl+9 (`order`) -- a document not made yet, whose modules have nothing to work on (issue #90); every other row as it was."""
        self.off = set(indices)
        for index, item in self.rows.items():
            off = index in self.off
            item.setData(OFF, off)
            item.setFlags(Qt.ItemFlag.NoItemFlags if off else Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            item.setToolTip(tip if off and tip else item.text())
        self.list.viewport().update()

    def _refresh_rows(self):
        """Each row shown where the document shows it and its group is not folded; a group's title hidden where the document shows none of its rows, its arrow saying whether it is folded."""
        for head, members in self.groups:
            folded = head.data(TITLE) in self.folded
            for item in members:
                item.setHidden(not self._shows(item) or folded)
            head.setHidden(not any(self._shows(item) for item in members))
            head.setData(FOLDED, folded)
        for row, held, head in self.sections:
            row.setHidden(head.data(TITLE) in self.folded or not any(self._shows(item) for item in held))
        self.list.doItemsLayout()
        self.list.viewport().update()

    def toggle_group(self, title):
        """A group folded or unfolded -- its title clicked."""
        if title in self.folded:
            self.folded.discard(title)
        else:
            self.folded.add(title)
        self._refresh_rows()
        self.foldedChanged.emit(sorted(self.folded))

    def eventFilter(self, obj, event):
        if obj is self.list.viewport() and event.type() == QEvent.Type.MouseButtonRelease:
            item = self.list.itemAt(event.position().toPoint())
            if item is not None and item.data(KIND) == "group" and not self.collapsed:
                self.toggle_group(item.data(TITLE))
                return True
        return super().eventFilter(obj, event)

    def visible(self, index):
        item = self.rows.get(index)
        return item is not None and self._shows(item)

    def order(self):
        """The tab indices in the order the navigation lists them, the rows the document shows and no other -- what Ctrl+1 … Ctrl+9 count by; a folded group's rows count still."""
        return [self.list.item(i).data(INDEX) for i in range(self.list.count())
                if self.list.item(i).data(KIND) == "entry" and self._shows(self.list.item(i)) and self.list.item(i).data(INDEX) not in self.off]

    def set_expanded_width(self, width, emit=True):
        width = max(MIN_EXPANDED_WIDTH, min(MAX_EXPANDED_WIDTH, int(width)))
        if width == self.expanded_width:
            return
        self.expanded_width = width
        self._apply_width()
        if emit:
            self.widthChanged.emit(width)

    def _current(self, item, _previous):
        if item is not None and item.data(KIND) == "entry":
            self.chosen.emit(item.data(INDEX))

    def set_current(self, index):
        item = self.rows.get(index)
        if item is not None and self.list.currentItem() is not item:
            self.list.blockSignals(True)
            self.list.setCurrentItem(item)
            self.list.blockSignals(False)
            self.list.viewport().update()

    def current(self):
        item = self.list.currentItem()
        return item.data(INDEX) if item is not None else None

    def set_dirty(self, index, dirty):
        item = self.rows.get(index)
        if item is not None and bool(item.data(DIRTY)) != bool(dirty):
            item.setData(DIRTY, bool(dirty))

    def dirty(self, index):
        item = self.rows.get(index)
        return bool(item.data(DIRTY)) if item is not None else False

    def set_collapsed(self, collapsed):
        collapsed = bool(collapsed)
        if collapsed == self.collapsed:
            return
        self.collapsed = collapsed
        self._apply_width()
        self.collapsedChanged.emit(collapsed)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.grip.place()

    def _apply_width(self):
        # the widths are kept at 100 % -- the one dragged too, in layout_store -- and drawn at the zoom in force (issue #85)
        self.setFixedWidth(theme.scaled(COLLAPSED_WIDTH if self.collapsed else self.expanded_width))
        self.grip.setVisible(not self.collapsed)
        self.grip.place()
        if self.mode_select is not None:   # folded, the document is its number
            self.mode_select.setVisible(not self.collapsed)
            self.mode_button.setVisible(self.collapsed)
        self.fold.set_folded(self.collapsed)
        # group rows change height when folded: the list lays itself out again
        self.list.doItemsLayout()
        self.list.viewport().update()


class _WidthGrip(QWidget):
    """The navigation's right edge, dragged to make it wider or narrower (v0.117): a strip GRIP_PX wide over its edge, the cursor the splitters' own."""

    def __init__(self, nav):
        super().__init__(nav)
        self.nav = nav
        self.setCursor(Qt.CursorShape.SizeHorCursor)
        self.start = None

    def place(self):
        grip = theme.scaled(GRIP_PX)
        self.setGeometry(self.nav.width() - grip, 0, grip, self.nav.height())
        self.raise_()

    def mousePressEvent(self, event):
        self.start = (event.globalPosition().x(), self.nav.expanded_width)

    def mouseMoveEvent(self, event):
        if self.start is not None:
            x, width = self.start
            self.nav.set_expanded_width(width + (event.globalPosition().x() - x) * 100 / theme.zoom(), emit=False)   # dragged in pixels on screen, kept at 100 %

    def mouseReleaseEvent(self, _event):
        if self.start is not None:
            self.start = None
            self.nav.widthChanged.emit(self.nav.expanded_width)


# --- the interface's zoom: its three actions, the same in the window's «Affichage» menu and on the start page (issue #85) ---

# The keys of each, stated once. Ctrl+= beside Ctrl++, which a Swiss keyboard reaches by Shift; the numeric keypad's + and − match these, Qt leaving its modifier out of a shortcut.
ZOOM_KEYS = (("zoom_in", ("Ctrl++", "Ctrl+=")), ("zoom_out", ("Ctrl+-",)), ("zoom_reset", ("Ctrl+0",)))


def zoom_actions(parent, t):
    """The three actions of the zoom -- *Zoom avant*, *Zoom arrière*, *Taille réelle* -- with their keys, parented to `parent`, each calling theme's own; `t` gives their words. A window puts them in its menu, the start page on itself."""
    from PySide6.QtGui import QAction, QKeySequence
    actions = []
    for key, keys in ZOOM_KEYS:
        action = QAction(t(key), parent)
        action.setShortcuts([QKeySequence(k) for k in keys])
        action.triggered.connect(getattr(theme, key))
        actions.append(action)
    return actions


# --- the start page's cards --------------------------------------------------------------------------------------

class ActionCard(QFrame):
    """One thing the start page offers -- a new project, a project opened, an old folder converted -- as the site sets a feature: an icon on a soft ground, a title and a line saying what it does. Clicked, or Enter/Space while it has the focus, it emits `clicked`."""

    clicked = Signal()

    def __init__(self, key, title, text, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        row = QHBoxLayout(self)
        row.setContentsMargins(12, 10, 12, 10)
        row.setSpacing(12)
        badge = QLabel()
        badge.setObjectName("cardIcon")
        badge.setFixedSize(36, 36)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setPixmap(_pixmap(key, theme.colour("accent-strong"), 20, pixel_ratio()))
        row.addWidget(badge, 0, Qt.AlignmentFlag.AlignTop)
        words = QVBoxLayout()
        words.setSpacing(2)
        self.title = QLabel(title)
        self.title.setObjectName("cardTitle")
        self.text = QLabel(text)
        self.text.setObjectName("cardText")
        self.text.setWordWrap(True)
        words.addWidget(self.title)
        words.addWidget(self.text)
        row.addLayout(words, 1)
        self.setToolTip(text)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.rect().contains(event.position().toPoint()):
            self.clicked.emit()
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
            self.clicked.emit()
            return
        super().keyPressEvent(event)


class RecentCardDelegate(QStyledItemDelegate):
    """A recent project as a card, where it was a row of five columns: its name and number, its folder under them, and at the right when it was last exported and by which engine -- the engine in wood where it is not this program's, which is what the first export will ask about. It reads the item's five columns, so the list keeps its data as it was (tests/test_home.py reads them); the other four columns are hidden and this one is painted across the row."""

    HEIGHT = 58

    def __init__(self, view, words):
        super().__init__(view)
        self.view = view
        self.words = words   # {"number": "N°", "exported": "Dernier export", "engine": "moteur {version}", "current": program version}

    def sizeHint(self, option, index):
        return QSize(10, self.HEIGHT)

    def paint(self, painter, option, index):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(option.rect.adjusted(2, 3, -2, -3))
        selected = bool(option.state & QStyle.StateFlag.State_Selected)
        hovered = bool(option.state & QStyle.StateFlag.State_MouseOver)
        path = QPainterPath()
        path.addRoundedRect(rect, 9, 9)
        painter.fillPath(path, QColor(theme.colour("accent-soft" if selected else "bg-soft" if hovered else "bg")))
        painter.setPen(QPen(QColor(theme.colour("accent" if selected else "line")), 1))
        painter.drawPath(path)
        cell = lambda column: index.siblingAtColumn(column).data(Qt.ItemDataRole.DisplayRole) or ""  # noqa: E731
        muted = QColor(theme.colour("muted"))
        gone = bool(index.siblingAtColumn(1).data(Qt.ItemDataRole.UserRole))   # a project no longer where it was, or one that cannot be read (HomeWindow.fill)
        ink = muted if gone else QColor(theme.colour("ink"))
        base = QFont(option.font)
        title = QFont(base)
        title.setBold(True)
        title.setPointSizeF(base.pointSizeF() * 1.08 if base.pointSizeF() > 0 else base.pointSizeF())
        left = rect.adjusted(14, 8, -14, -8)
        # right column: last export, and the engine
        right_width = 190
        right = QRectF(left.right() - right_width, left.top(), right_width, left.height())
        painter.setFont(base)
        painter.setPen(muted)
        exported = cell(3)
        painter.drawText(right.adjusted(0, 0, 0, -right.height() / 2), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                         f"{self.words['exported']} {exported}".strip())
        engine = cell(4)
        if engine:
            text = self.words["engine"].format(version=engine)
            width = painter.fontMetrics().horizontalAdvance(text) + 14
            pill = QRectF(right.right() - width, right.center().y() + 2, width, right.height() / 2 - 2)
            older = engine != self.words["current"]
            pill_path = QPainterPath()
            pill_path.addRoundedRect(pill, pill.height() / 2, pill.height() / 2)
            painter.fillPath(pill_path, QColor(theme.colour("wood-soft" if older else "bg-sunk")))
            painter.setPen(QColor(theme.colour("ink" if older else "muted")))
            painter.drawText(pill, Qt.AlignmentFlag.AlignCenter, text)
        # left: name and number, the folder under them
        text_left = QRectF(left.left(), left.top(), left.width() - right_width - 12, left.height())
        painter.setFont(title)
        painter.setPen(ink)
        name = cell(0)
        top_line = QRectF(text_left.left(), text_left.top(), text_left.width(), text_left.height() / 2)
        name_width = painter.fontMetrics().horizontalAdvance(name)
        painter.drawText(top_line, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, painter.fontMetrics().elidedText(name, Qt.TextElideMode.ElideRight, int(top_line.width())))
        number = cell(1)
        if number and name_width + 12 < top_line.width():
            painter.setFont(base)
            painter.setPen(muted)
            painter.drawText(top_line.adjusted(name_width + 10, 0, 0, 0), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, f"{self.words['number']} {number}")
        painter.setFont(base)
        painter.setPen(muted)
        folder = cell(2)
        bottom_line = QRectF(text_left.left(), text_left.center().y(), text_left.width(), text_left.height() / 2)
        painter.drawText(bottom_line, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, painter.fontMetrics().elidedText(folder, Qt.TextElideMode.ElideMiddle, int(bottom_line.width())))
        painter.restore()
