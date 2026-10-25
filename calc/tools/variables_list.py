"""The list of the «Variables» tab: always grouped by domain, one line per variable, the choice «comme dans Windows» (spec docs/requirements/completed/2026-10-24-onglet-variables-groupes.md, UI-006 to UI-009, ARCH-007; docs/ui/tab-variables.md).

**A `QTableView` on a flat `QAbstractTableModel`** (ARCH-007, D-16): a title line per domain spanning the whole
width (`setSpan`), its variables under it; never a tree, which the keyboard would fold, and never Qt's own
selection (`NoSelection`), whose range takes the title lines and which knows no «last one clicked». The choice
is `variable_select.Selection`'s: the view hands it the clicks, their modifiers and the keys, and paints what it
holds -- the ground of a row chosen, its box, the bar at the left of the last one clicked.

The columns (UI-007): the box, **the symbol** as the report prints it (`richtext.MathDelegate`, the name to write
in its tooltip), the value at the right in tabular figures, the unit, the label. Their widths start at
120 / 120 / 76 px and never follow a search (no `ResizeToContents`); dragged at the right edge of a heading they
are kept (`widths` / `set_widths`, the tab's state), and a double click on that edge gives the width back.

A result is framed in the theme's accent (UI-008, D-6), its value in the accent and in bold: the star of before is gone.
"""

from PySide6.QtCore import QAbstractTableModel, QModelIndex, QRect, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QAbstractTextDocumentLayout, QColor, QFont, QFontMetrics, QPalette, QPen, QTextDocument
from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QStyle, QStyleOptionButton, QStyleOptionViewItem, QTableView

import richtext
import theme
import variables as model
from variable_select import Selection

BOX, SYMBOL, VALUE, UNIT, LABEL = range(5)
COLUMNS = ("", "vr_col_symbol", "vr_col_value", "vr_col_unit", "vr_col_label")
# The widths a column starts at, in px at 100 % (UI-007), and the box's.
DEFAULT_WIDTHS = {SYMBOL: 120, VALUE: 120, UNIT: 76}
WIDTH_NAMES = {SYMBOL: "symbol", VALUE: "value", UNIT: "unit"}
BOX_WIDTH = 28
EDGE = 4          # how near the edge of a heading a double click gives its width back

TITLE, VARIABLE = "title", "variable"
KEY_ROLE = Qt.ItemDataRole.UserRole
KIND_ROLE = Qt.ItemDataRole.UserRole + 1


def default_width(column):
    return theme.scaled(DEFAULT_WIDTHS[column])


class VariablesModel(QAbstractTableModel):
    """The rows: a title per domain, then its variables -- one flat list, in the order of `variable_query.Catalogue.groups`. `describe(domain, count)` gives a title's parts: {case, badge, kind (export/file/document), rest, count, tip}."""

    def __init__(self, selection, words, parent=None):
        super().__init__(parent)
        self.selection = selection
        self.words = words
        self.rows = []          # [(TITLE, domain, parts) | (VARIABLE, domain, var)]
        self.keys = []          # the variables' keys, in the list's order
        self.accept = None      # while a field is linked: what it takes (REQ-008)

    def set_groups(self, groups, describe):
        self.beginResetModel()
        self.rows, self.keys = [], []
        for domain, kept in groups:
            self.rows.append((TITLE, domain, describe(domain, len(kept))))
            for var in kept:
                self.rows.append((VARIABLE, domain, var))
                self.keys.append((domain.origin, domain.name, var.key))
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.rows)

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(COLUMNS)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole and COLUMNS[section]:
            return self.words(COLUMNS[section])
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.TextAlignmentRole and section == VALUE:
            return int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        return None

    def kind(self, row):
        return self.rows[row][0] if 0 <= row < len(self.rows) else None

    def key(self, row):
        """The key (origin, domain, name) of a variable's row, None for a title."""
        if self.kind(row) != VARIABLE:
            return None
        _kind, domain, var = self.rows[row]
        return (domain.origin, domain.name, var.key)

    def row_of(self, key):
        key = tuple(key) if key is not None else None
        for row in range(len(self.rows)):
            if self.key(row) == key:
                return row
        return -1

    def is_result(self, row):
        if self.kind(row) != VARIABLE:
            return False
        _kind, domain, var = self.rows[row]
        return var.key in domain.results

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        kind, domain, item = self.rows[index.row()]
        column = index.column()
        if role == KIND_ROLE:
            return kind
        if role == KEY_ROLE:
            return self.key(index.row())
        if kind == TITLE:
            if role == Qt.ItemDataRole.DisplayRole and column == BOX:
                return f"{item['case']} [{item['badge']}] {item['rest']}"
            if role == Qt.ItemDataRole.ToolTipRole:
                return item.get("tip") or None
            return None
        var = item
        key = (domain.origin, domain.name, var.key)
        if role == Qt.ItemDataRole.DisplayRole:
            return {SYMBOL: var.symbol, VALUE: model.fmt_value(var.value), UNIT: var.unit, LABEL: var.label}.get(column)
        if role == Qt.ItemDataRole.ToolTipRole:
            return {SYMBOL: var.key, VALUE: model.fmt_value(var.value), UNIT: var.unit or None, LABEL: (var.description or var.label) or None}.get(column)
        if role == Qt.ItemDataRole.TextAlignmentRole and column == VALUE and var.is_number:
            return int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        if role == Qt.ItemDataRole.CheckStateRole and column == BOX and not self.selection.single:
            return Qt.CheckState.Checked if key in self.selection else Qt.CheckState.Unchecked
        if role == Qt.ItemDataRole.BackgroundRole and key in self.selection:
            return QColor(theme.colour("accent-soft"))
        if role == Qt.ItemDataRole.ForegroundRole and self.accept is not None and not self.accept(var, domain):
            return QColor(theme.colour("muted"))
        return None

    def selection_changed(self):
        if self.rows:
            self.dataChanged.emit(self.index(0, 0), self.index(len(self.rows) - 1, len(COLUMNS) - 1))


class ListDelegate(richtext.MathDelegate):
    """The symbol as mathematics (MathDelegate), a title line drawn as the prototype draws it, a result framed in the accent, the box, and the bar of the last one clicked."""

    def __init__(self, view):
        super().__init__(view, [SYMBOL])
        self.view = view

    def frame_colour(self, index):
        """The accent the value of a result is framed in -- read from the theme in force when it is painted, light or dark (UI-008) --, None for any other cell."""
        if index.column() == VALUE and self.view.model().is_result(index.row()):
            return QColor(theme.colour("accent"))
        return None

    def paint(self, painter, option, index):
        model_ = self.view.model()
        row = index.row()
        if model_.kind(row) == TITLE:
            return self._paint_title(painter, option, index)
        if index.column() == BOX:
            return self._paint_box(painter, option, index)
        frame = self.frame_colour(index)
        if frame is not None:
            return self._paint_result(painter, option, index, frame)
        super().paint(painter, option, index)

    def _background(self, painter, option, index):
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        opt.text = ""
        opt.features &= ~QStyleOptionViewItem.ViewItemFeature.HasCheckIndicator
        widget = opt.widget
        widget.style().drawControl(QStyle.ControlElement.CE_ItemViewItem, opt, painter, widget)
        return opt

    def _paint_box(self, painter, option, index):
        model_ = self.view.model()
        self._background(painter, option, index)
        key = model_.key(index.row())
        if key is not None and key == model_.selection.focus:
            painter.fillRect(QRect(option.rect.left(), option.rect.top(), 3, option.rect.height()), QColor(theme.colour("accent")))
        if model_.selection.single:
            return
        box = QStyleOptionButton()
        size = self.view.style().pixelMetric(QStyle.PixelMetric.PM_IndicatorWidth)
        box.rect = QRect(option.rect.left() + (option.rect.width() - size) // 2, option.rect.top() + (option.rect.height() - size) // 2, size, size)
        box.state = QStyle.StateFlag.State_Enabled | (QStyle.StateFlag.State_On if key in model_.selection else QStyle.StateFlag.State_Off)
        self.view.style().drawPrimitive(QStyle.PrimitiveElement.PE_IndicatorCheckBox, box, painter, self.view)

    def _paint_result(self, painter, option, index, frame):
        opt = self._background(painter, option, index)
        text = index.data(Qt.ItemDataRole.DisplayRole) or ""
        font = QFont(opt.font)
        font.setBold(True)
        metrics = QFontMetrics(font)
        width = metrics.horizontalAdvance(text) + 10
        height = metrics.height() + 2
        rect = opt.rect.adjusted(2, 0, -4, 0)
        box = QRect(rect.right() - width, rect.top() + (rect.height() - height) // 2, width, height)
        painter.save()
        painter.setRenderHint(painter.RenderHint.Antialiasing)
        painter.setPen(QPen(frame, 1.5))
        painter.drawRoundedRect(QRectF(box), 4, 4)
        painter.setFont(font)
        painter.setPen(QColor(theme.colour("accent-strong")))
        painter.drawText(box, int(Qt.AlignmentFlag.AlignCenter), text)
        painter.restore()

    def _paint_title(self, painter, option, index):
        if index.column() != BOX:
            return
        _kind, _domain, parts = self.view.model().rows[index.row()]
        rect = QRect(option.rect)
        painter.save()
        painter.fillRect(rect, QColor(theme.colour("bg-sunk")))
        badge = {"export": "wood", "file": "accent-strong", "document": "ok"}.get(parts.get("kind"), "muted")
        html = (f'<b>{_esc(parts["case"])}</b>&nbsp;&nbsp;<span style="color:{theme.colour(badge)}">{_esc(parts["badge"])}</span>'
                f'&nbsp;&nbsp;<span style="color:{theme.colour("muted")}">{_esc(parts["rest"])}</span>')
        doc = QTextDocument()
        doc.setDefaultFont(option.font)
        doc.setDocumentMargin(0)
        doc.setHtml(html)
        count = str(parts.get("count", ""))
        count_width = option.fontMetrics.horizontalAdvance(count) + 12
        painter.translate(rect.left() + 8, rect.top() + max(0.0, (rect.height() - doc.size().height()) / 2))
        painter.setClipRect(QRectF(0, -rect.height(), rect.width() - count_width - 16, rect.height() * 3))
        context = QAbstractTextDocumentLayout.PaintContext()
        context.palette.setColor(QPalette.ColorRole.Text, QColor(theme.colour("ink")))
        doc.documentLayout().draw(painter, context)
        painter.restore()
        painter.save()
        painter.setPen(QColor(theme.colour("muted")))
        painter.drawText(rect.adjusted(0, 0, -10, 0), int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter), count)
        painter.restore()

    def sizeHint(self, option, index):
        size = super().sizeHint(option, index)
        return QSize(size.width(), max(size.height(), option.fontMetrics.height() + 8))


def _esc(text):
    import html
    return html.escape(str(text or ""), quote=False)


class Header(QHeaderView):
    """The headings: the box of the first ticks or lets go every variable shown (UI-009), a double click on the right edge of a heading gives its width back (UI-007)."""

    toggled = Signal(bool)

    def __init__(self, view):
        super().__init__(Qt.Orientation.Horizontal, view)
        self.view = view
        self.setSectionsClickable(True)
        self.setHighlightSections(False)

    def paintSection(self, painter, rect, logical):
        super().paintSection(painter, rect, logical)
        model_ = self.view.model()
        if logical != BOX or model_ is None or model_.selection.single:
            return
        box = QStyleOptionButton()
        size = self.style().pixelMetric(QStyle.PixelMetric.PM_IndicatorWidth)
        box.rect = QRect(rect.left() + (rect.width() - size) // 2, rect.top() + (rect.height() - size) // 2, size, size)
        box.state = QStyle.StateFlag.State_Enabled | (QStyle.StateFlag.State_On if model_.selection.all_shown(model_.keys) else QStyle.StateFlag.State_Off)
        self.style().drawPrimitive(QStyle.PrimitiveElement.PE_IndicatorCheckBox, box, painter, self)

    def edge_at(self, x):
        """The column whose right edge `x` is on, None where it is on none -- the box's and the last's are not dragged."""
        for logical in (SYMBOL, VALUE, UNIT):
            edge = self.sectionViewportPosition(logical) + self.sectionSize(logical)
            if abs(x - edge) <= EDGE:
                return logical
        return None

    def mouseDoubleClickEvent(self, event):
        column = self.edge_at(int(event.position().x()))
        if column is not None:
            self.resizeSection(column, default_width(column))
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    def mousePressEvent(self, event):
        x = int(event.position().x())
        if self.logicalIndexAt(x) == BOX and self.edge_at(x) is None and not self.view.model().selection.single:
            model_ = self.view.model()
            self.toggled.emit(not model_.selection.all_shown(model_.keys))
            event.accept()
            return
        super().mousePressEvent(event)


class VariablesList(QTableView):
    """The view. `changed` after every gesture that changed the choice or the last one clicked: the tab then shows the card and the bar of the choice."""

    changed = Signal()

    def __init__(self, words, parent=None, selection=None):
        super().__init__(parent)
        self.selection = selection if selection is not None else Selection()   # never `or`: an empty choice is falsy (it has a len)
        self.list_model = VariablesModel(self.selection, words, self)
        self.setModel(self.list_model)
        self.header = Header(self)
        self.setHorizontalHeader(self.header)
        self.header.toggled.connect(self.toggle_all)
        self.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setShowGrid(False)
        self.setWordWrap(False)
        self.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.verticalHeader().hide()
        self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self.verticalHeader().setDefaultSectionSize(self.fontMetrics().height() + 10)
        self.delegate = ListDelegate(self)
        self.setItemDelegate(self.delegate)
        header = self.header
        header.setMinimumSectionSize(36)
        header.setSectionResizeMode(BOX, QHeaderView.ResizeMode.Fixed)
        for column in (SYMBOL, VALUE, UNIT):
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(True)
        header.resizeSection(BOX, BOX_WIDTH)
        self.set_widths({})

    # -- the widths (UI-007) --

    def widths(self):
        return {WIDTH_NAMES[c]: self.header.sectionSize(c) for c in WIDTH_NAMES}

    def set_widths(self, kept):
        """The widths kept by the tab's state, each one missing or unreadable at its default (a state of before has none)."""
        kept = kept if isinstance(kept, dict) else {}
        for column, name in WIDTH_NAMES.items():
            value = kept.get(name)
            self.header.resizeSection(column, int(value) if isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 24 else default_width(column))

    # -- what it lists --

    def set_groups(self, groups, describe):
        widths = self.widths()
        self.list_model.set_groups(groups, describe)
        self.clearSpans()
        for row, (kind, _d, _x) in enumerate(self.list_model.rows):
            if kind == TITLE:
                self.setSpan(row, 0, 1, len(COLUMNS))
        self.set_widths(widths)   # never a width that follows the list (UI-007)
        self.header.viewport().update()

    def shown(self):
        return list(self.list_model.keys)

    def refresh(self):
        self.list_model.selection_changed()
        self.header.viewport().update()

    def scroll_to(self, key):
        row = self.list_model.row_of(key)
        if row >= 0:
            self.scrollTo(self.list_model.index(row, SYMBOL))

    # -- the gestures --

    def toggle_all(self, on):
        self.selection.set_all(self.shown(), on)
        self.refresh()
        self.changed.emit()

    def gesture(self, row, column, ctrl=False, shift=False):
        """A click on `row`, `column`: what the mouse does, callable by a test. A title line does nothing."""
        key = self.list_model.key(row)
        if key is None:
            return False
        self.selection.click(key, self.shown(), ctrl=ctrl, shift=shift, box=(column == BOX and not self.selection.single))
        self.refresh()
        self.changed.emit()
        return True

    def mousePressEvent(self, event):
        index = self.indexAt(event.position().toPoint())
        if not index.isValid() or event.button() != Qt.MouseButton.LeftButton:
            return super().mousePressEvent(event)
        mods = event.modifiers()
        self.setFocus()
        self.gesture(index.row(), index.column(), ctrl=bool(mods & Qt.KeyboardModifier.ControlModifier), shift=bool(mods & Qt.KeyboardModifier.ShiftModifier))
        event.accept()

    def mouseDoubleClickEvent(self, event):
        event.accept()   # a double click is two clicks, never an editor

    def keyPressEvent(self, event):
        key, mods = event.key(), event.modifiers()
        shift = bool(mods & Qt.KeyboardModifier.ShiftModifier)
        ctrl = bool(mods & Qt.KeyboardModifier.ControlModifier)
        if key in (Qt.Key.Key_Down, Qt.Key.Key_Up):
            reached = self.selection.step(self.shown(), +1 if key == Qt.Key.Key_Down else -1, shift=shift, ctrl=ctrl)
        elif key == Qt.Key.Key_Space:
            self.selection.space(self.shown())
            reached = self.selection.focus
        elif key == Qt.Key.Key_A and ctrl:
            self.selection.set_all(self.shown(), True)
            reached = self.selection.focus
        else:
            return super().keyPressEvent(event)
        self.refresh()
        if reached is not None:
            self.scroll_to(reached)
        self.changed.emit()
        event.accept()
