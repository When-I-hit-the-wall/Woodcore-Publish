"""A check box centred in its table cell (v0.77).

Qt draws an item's check box at the left of its cell, where its text would begin, and there is no alignment to ask it for the middle: `Qt.AlignCenter` on the item moves the text, never the indicator. A column that holds nothing but a tick -- «visible», «connecteur» in the «Schémas» lists -- then reads as a row of boxes pushed against the column's left edge, under a header centred over the whole width. The engineer asked for them centred.

`CentredCheck` is the delegate that does it, and it does both halves, because either alone is a defect: **it paints** the cell's ground, selection and focus as the style would and the indicator in the middle of the cell, and **it takes the click** on that same middle rectangle -- a box drawn in the middle that still toggled only where Qt would have drawn it is a box that ignores the pointer. The rectangle both use is the style's own indicator rectangle, moved to the cell's centre, so the size, the style sheet and the dark theme are the style's and nothing is drawn by hand. The space bar still toggles the current cell.

What the model holds does not change: the item stays `ItemIsUserCheckable`, its `CheckStateRole` is what is set, and `itemChanged` fires as it did -- so every tab reading a tick reads it as before.
"""

from PySide6.QtCore import QEvent, Qt
from PySide6.QtWidgets import QApplication, QStyle, QStyledItemDelegate, QStyleOptionViewItem


def _checked(value):
    """A CheckStateRole value as a Qt.CheckState, whether PySide hands it over as the enum or as its int."""
    if value is None:
        return None
    try:
        return Qt.CheckState(value)
    except (TypeError, ValueError):
        return Qt.CheckState(getattr(value, "value", 0))


class CentredCheck(QStyledItemDelegate):
    """Draws and toggles a check box in the middle of its cell. Set it on the columns that hold a tick and nothing else (`QTableView.setItemDelegateForColumn`)."""

    def _checkable(self, index):
        flags = index.flags()
        return bool(flags & Qt.ItemFlag.ItemIsUserCheckable) and _checked(index.data(Qt.ItemDataRole.CheckStateRole)) is not None

    def indicator_rect(self, option, index):
        """The indicator's rectangle, in the view's coordinates: the style's own, centred in the cell."""
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        style = opt.widget.style() if opt.widget is not None else QApplication.style()
        rect = style.subElementRect(QStyle.SubElement.SE_ItemViewItemCheckIndicator, opt, opt.widget)
        rect.moveCenter(option.rect.center())
        return rect

    def paint(self, painter, option, index):
        if not self._checkable(index):
            super().paint(painter, option, index)
            return
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        style = opt.widget.style() if opt.widget is not None else QApplication.style()
        rect = self.indicator_rect(option, index)
        state = _checked(index.data(Qt.ItemDataRole.CheckStateRole))
        # the cell itself -- its ground, the selection, the focus -- with no indicator and no text in it
        opt.features &= ~QStyleOptionViewItem.ViewItemFeature.HasCheckIndicator
        opt.text = ""
        style.drawControl(QStyle.ControlElement.CE_ItemViewItem, opt, painter, opt.widget)
        # then the indicator, in the middle
        check = QStyleOptionViewItem(opt)
        check.rect = rect
        check.state &= ~(QStyle.StateFlag.State_On | QStyle.StateFlag.State_Off | QStyle.StateFlag.State_NoChange)
        check.state |= {Qt.CheckState.Checked: QStyle.StateFlag.State_On,
                        Qt.CheckState.PartiallyChecked: QStyle.StateFlag.State_NoChange}.get(state, QStyle.StateFlag.State_Off)
        style.drawPrimitive(QStyle.PrimitiveElement.PE_IndicatorItemViewItemCheck, check, painter, opt.widget)

    def editorEvent(self, event, model, option, index):
        """QStyledItemDelegate's own rule, on the centred rectangle: a press or a double-click on the box is taken, a release on it toggles, the space bar toggles."""
        if not self._checkable(index) or not (index.flags() & Qt.ItemFlag.ItemIsEnabled):
            return super().editorEvent(event, model, option, index)
        kind = event.type()
        if kind in (QEvent.Type.MouseButtonPress, QEvent.Type.MouseButtonRelease, QEvent.Type.MouseButtonDblClick):
            if event.button() != Qt.MouseButton.LeftButton:
                return False
            if not self.indicator_rect(option, index).contains(event.position().toPoint()):
                return False
            if kind != QEvent.Type.MouseButtonRelease:
                return True
        elif kind == QEvent.Type.KeyPress:
            if event.key() not in (Qt.Key.Key_Space, Qt.Key.Key_Select):
                return False
        else:
            return False
        state = _checked(index.data(Qt.ItemDataRole.CheckStateRole))
        new = Qt.CheckState.Unchecked if state == Qt.CheckState.Checked else Qt.CheckState.Checked
        return model.setData(index, new, Qt.ItemDataRole.CheckStateRole)
