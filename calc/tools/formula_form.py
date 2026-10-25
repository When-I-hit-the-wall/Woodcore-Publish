"""The «Formulaire» of the «Domaines» tab: a column of rows, one a line of the domain's file (issue #113, spec docs/requirements/completed/2026-10-24-onglet-domaines-formulaire-code.md, UI-005 to UI-011, UI-013, UI-018, ARCH-002, ARCH-010, ARCH-RISK-008).

**A column of row widgets in a scroll area** (ARCH-002, the review's choice over a QTableView: the rows are of many shapes -- fields, a message under them, the detail of the row chosen, the + between two, a text holding its commands). Each row is a calc/tools/formula_row.py `FormRow`; between two, an `InsertBar` whose + offers var, eq, verify, texte, lier une variable (UI-008); at the foot, the line typed and inferred (calc/tools/formula_new_line.py, UI-010).

**A value changed updates its row in place**: nothing is rebuilt but where rows come or go -- an insert, a delete, a move (ARCH-RISK-008). **The calculation a click writes into** (UI-011) is held as (the item, the field), found again in the column as it is **now** when a name is clicked on the right, and written at the position its cursor had -- the defect the prototype found (T41: the field kept was the old one, taken off the page by a redraw) cannot come back, no widget being kept across a rebuild.

**Several rows** (UI-013): Ctrl+click adds a row to the group or takes it away, Shift+click a range, a plain click or Escape lets the group go -- the choice «comme dans Windows» of the «Variables» tab, its one model (calc/variable_select.py, ARCH-010), here with the rows' items for keys. The group has a dashed frame and a banner; dragging the grip of one of its rows moves them all, in their order, to where they are dropped; a bar shows where. Never a key (D-10).

**The linked hovers** (UI-018): a row under the pointer lit, the rows it is computed from in blue, those computed from it in green -- `formula_links.dependencies`, given by the tab, never parsed here.
"""

from PySide6.QtCore import QPoint, Qt, QTimer
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QFrame, QLabel, QMenu, QScrollArea, QVBoxLayout, QWidget

import theme
import variable_select
from domains.formula_state import UNFOLD_STATES
from formula_new_line import NewLine
from formula_row import MIME, FormRow, InsertBar


class _Column(QWidget):
    """The column of rows, which takes the drops of the grips (UI-013)."""

    def __init__(self, view):
        super().__init__()
        self.view = view
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat(MIME):
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat(MIME):
            self.view.show_drop(self.view.drop_index(event.position().toPoint().y()))
            event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        self.view.show_drop(None)

    def dropEvent(self, event):
        if not event.mimeData().hasFormat(MIME):
            return
        rows = [int(r) for r in bytes(event.mimeData().data(MIME)).decode("ascii").split(",") if r]
        target = self.view.drop_index(event.position().toPoint().y())
        self.view.show_drop(None)
        event.acceptProposedAction()
        QTimer.singleShot(0, self.view, lambda: self.view.tab.write_move_rows(rows, target))


class FormView(QScrollArea):
    """The form -- see the module's docstring. `tab` is the FormulaTab: what it shows comes from it, what is typed goes to it."""

    def __init__(self, tab):
        super().__init__()
        self.tab = tab
        self.t = tab.t
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.inner = _Column(self)
        self.column = QVBoxLayout(self.inner)
        self.column.setContentsMargins(0, 4, 4, 4)
        self.column.setSpacing(0)
        self.setWidget(self.inner)
        self.rows = []            # FormRow, in order
        self.bars = []
        self.domain, self.results = None, []
        self.chosen = None        # the row chosen, by its first item
        self.selection = variable_select.Selection()
        self.target = None        # (item, field) of the calculation a click writes into
        self.insert_line = None   # the NewLine the + opened
        self.banner = QLabel("")
        self.banner.setWordWrap(True)
        self.banner.setStyleSheet("background: %s; color: %s; padding: 4px; border-radius: 4px;" % (theme.colour("accent-soft"), theme.colour("ink")))
        self.banner.setVisible(False)
        self.drop_bar = QFrame(self.inner)
        self.drop_bar.setFixedHeight(3)
        self.drop_bar.setStyleSheet("background: %s;" % theme.colour("link-uses-line"))
        self.drop_bar.setVisible(False)
        self.foot = None

    # --- built, and updated -----------------------------------------------------------------------

    def shape(self, domain):
        from domains import formula_rows
        return [(r.items, r.kind) for r in formula_rows.rows(domain)] if domain is not None else []

    def show_domain(self, domain, results, rebuild=False):
        """The domain's rows: in place where they are the same rows (a value changed), built again where rows came or went."""
        from domains import formula_rows
        same = not rebuild and self.domain is not None and domain is not None and self.shape(domain) == [(r.row.items, r.row.kind) for r in self.rows] \
            and [c.kind for c in domain.commands] == [c.kind for c in self.domain.commands]
        self.domain, self.results = domain, results
        if same:
            for row, shape in zip(self.rows, formula_rows.rows(domain)):
                row.row = shape
                row.number.setText(str(shape.line))
                row.update_result()
            return
        self.build()

    def build(self):
        from domains import formula_rows
        focus = self._focus_key()
        while self.column.count():
            item = self.column.takeAt(0)
            widget = item.widget()
            if widget is not None and widget is not self.banner:
                widget.setParent(None)
                widget.deleteLater()
        self.rows, self.bars, self.insert_line = [], [], None
        self.column.addWidget(self.banner)
        if self.domain is None or self.domain.state == "unreadable":
            self.foot = None
            self.column.addStretch(1)
            return
        for index, shape in enumerate(formula_rows.rows(self.domain)):
            bar = InsertBar(self, index)
            self.bars.append(bar)
            self.column.addWidget(bar)
            row = FormRow(self, index, shape)
            self.rows.append(row)
            self.column.addWidget(row)
            if self.chosen is not None and shape.first == self.chosen:
                row.set_chosen(True)
            row.set_grouped((shape.first,) in self.selection and len(self.selection) > 1)
        bar = InsertBar(self, len(self.rows))
        self.bars.append(bar)
        self.column.addWidget(bar)
        self.foot = NewLine(self, None, foot=True)
        self.foot.committed.connect(lambda line: self.tab.write_new_line(line, None, self.foot))
        self.column.addWidget(self.foot)
        self.column.addStretch(1)
        self.show_banner()
        self._restore_focus(focus)

    def _focus_key(self):
        for row in self.rows:
            for key, widget in row.fields.items():
                try:
                    if widget.hasFocus():
                        return key, widget.cursorPosition() if hasattr(widget, "cursorPosition") else None
                except RuntimeError:
                    continue
        return None

    def _restore_focus(self, focus):
        if focus is None:
            return
        (item, name), position = focus
        widget = self.field(item, name)
        if widget is not None:
            widget.setFocus()
            if position is not None and hasattr(widget, "setCursorPosition"):
                widget.setCursorPosition(min(position, len(widget.text())))

    def set_states(self, st, say, results):
        """Each row's stripe and message (UI-009): its own state -- a fault, a warning, a line that only inherits a fault -- said once."""
        for row in self.rows:
            states = [st.rows.get(i) for i in row.row.items if st.rows.get(i)]
            messages = [say(m) for i in row.row.items for m in st.of_item(i)]
            if states and states[0] in UNFOLD_STATES and not messages:
                messages = [self.t("fm_unfold_state_" + states[0])]   # a line of an unfolded check says its state under its stripe (REQ-015)
            row.set_state(states[0] if states else None, "<br>".join(messages))

    def row_of(self, item):
        return next((r for r in self.rows if item in r.row.items), None)

    def field(self, item, name):
        """The field `name` of item `item` as the column holds it now, or None."""
        if name == "new":
            line = self.insert_line if self.insert_line is not None and self.insert_line.at == item else self.foot
            return line.text if line is not None else None
        row = self.row_of(item)
        return row.field(item, name) if row is not None else None

    # --- what the rows tell -----------------------------------------------------------------------

    def row_clicked(self, row, modifiers):
        """A click on a row: it alone chosen, the group let go; Ctrl+click adds it to the group or takes it away (the row chosen before entering it), Shift+click a range (UI-013, P-4)."""
        ctrl = bool(modifiers & Qt.KeyboardModifier.ControlModifier)
        shift = bool(modifiers & Qt.KeyboardModifier.ShiftModifier)
        keys = [(r.row.first,) for r in self.rows]
        if ctrl and len(self.selection) == 0 and self.chosen is not None and (self.chosen,) in keys:
            self.selection.click((self.chosen,), keys)
        self.selection.click((row.row.first,), keys, ctrl=ctrl, shift=shift)
        self.choose(row.row.first)
        self.show_group()

    def choose(self, item):
        """The row of `item` chosen -- its detail under it, its other arguments on the right (UI-006, UI-012)."""
        self.chosen = item
        for row in self.rows:
            row.set_chosen(item in row.row.items and item == row.row.first)
        self.tab.row_chosen(item)

    def choose_item(self, row, item):
        """A command inside a line of text chosen (D-16): its fields and arguments on the right."""
        self.chosen = row.row.first
        for r in self.rows:
            r.set_chosen(r is row)
        self.tab.row_chosen(item)

    def show_group(self):
        group = set(self.selection.keys([(r.row.first,) for r in self.rows]))
        for row in self.rows:
            row.set_grouped(len(group) > 1 and (row.row.first,) in group)
        self.show_banner()

    def show_banner(self):
        n = len(self.selection)
        self.banner.setText(self.t("fm_msel", n=n) if n > 1 else "")
        self.banner.setVisible(n > 1)

    def clear_group(self):
        self.selection.clear()
        self.show_group()

    def group_rows(self):
        keys = self.selection.keys([(r.row.first,) for r in self.rows])
        return [r.index for r in self.rows if (r.row.first,) in set(keys)]

    def dragged_rows(self, row):
        """The rows a grip drags: the group where the row is in it (UI-013), else the row alone."""
        group = self.group_rows()
        return group if row.index in group and len(group) > 1 else [row.index]

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape and len(self.selection) > 1:
            self.clear_group()
            return
        super().keyPressEvent(event)

    def row_hovered(self, row, on):
        self.tab.light(row.row.first if on else None)

    def light(self, item, uses=(), used=()):
        """The rows lit: `item`'s in yellow, those it uses in blue, those using it in green (UI-018) -- nothing else."""
        for row in self.rows:
            items = set(row.row.items)
            row.set_lit("self" if item in items else "uses" if items & set(uses) else "used" if items & set(used) else None)

    def field_done(self, row, item, name, value):
        self.tab.write_field(item, name, value)

    def text_done(self, row, item, text):
        self.tab.write_field(item, "text", text)

    def delete_rows(self, indexes):
        self.tab.write_delete_rows(indexes)

    def formula_focused(self, row, item, name, field):
        """A calculation took the cursor: the one a click on a variable writes into (UI-011)."""
        self.target = (item, name)

    def insert(self, text):
        """`text` written into the calculation being typed where its cursor is, the cursor left there (UI-011); False where there is none."""
        if self.target is None:
            return False
        field = self.field(*self.target)
        if field is None:
            return False
        try:
            position = field.cursorPosition() if field.hasFocus() else field.kept
        except RuntimeError:
            return False
        position = min(position, len(field.text()))
        field.setText(field.text()[:position] + text + field.text()[position:])
        field.setFocus()
        field.setCursorPosition(position + len(text))
        field.kept = position + len(text)
        if hasattr(field, "textEdited"):
            field.textEdited.emit(field.text())
        return True

    # --- the + between two rows, and the line it opens ------------------------------------------------

    def insert_menu(self, bar):
        menu = QMenu(self)
        for kind, word in (("var", "fm_ins_var"), ("eq", "fm_ins_eq"), ("verify", "fm_ins_verify"), ("text", "fm_ins_text"), ("link", "fm_ins_link")):
            action = QAction(self.t(word), menu)
            action.triggered.connect(lambda _c=False, k=kind: self.open_insert(bar.at, k))
            menu.addAction(action)
        menu.popup(bar.mapToGlobal(QPoint(28, bar.height())))
        self._menu = menu

    def open_insert(self, row_index, kind):
        """The + chose `kind` before row `row_index`: a new line with its pill fixed (UI-008), or the window «Lier une variable…» with that row for its target."""
        if kind == "link":
            self.tab.open_link_dialog(row_index)
            return
        if self.insert_line is not None:
            self.insert_line.setParent(None)
            self.insert_line.deleteLater()
        at = self.rows[row_index].row.first if row_index < len(self.rows) else None
        line = NewLine(self, at, kind=kind)
        line.committed.connect(lambda inferred, r=row_index, l=line: self.tab.write_new_line(inferred, r, l))
        line.cancelled.connect(lambda l=line: self.close_insert(l))
        place = self.column.indexOf(self.bars[row_index]) + 1
        self.column.insertWidget(place, line)
        self.insert_line = line
        line.text.setFocus()
        return line

    def close_insert(self, line):
        if line is self.insert_line:
            self.insert_line = None
        line.setParent(None)
        line.deleteLater()

    # --- what the rows ask of the tab ----------------------------------------------------------------

    def symbol_table(self, item):
        return self.tab.symbol_table(item)

    def attach_completion(self, field, item):
        self.tab.attach_completion(field, item)

    def excerpt_for(self, norm, section):
        return self.tab.excerpt_for(norm, section)

    def attach_bubble(self, mark, excerpt):
        self.tab.attach_bubble(mark, excerpt)

    def origin_text(self, origin, command):
        return self.tab.origin_text(origin, command)

    def plain_line(self, command, result):
        return self.tab.plain_line(command, result)

    def taken_keys(self):
        return {c.key for c in (self.domain.commands if self.domain else ()) if c.defines}

    # --- the drop ---------------------------------------------------------------------------------

    def drop_index(self, y):
        """The row a drop at `y` of the column goes before (len(rows): the end)."""
        for row in self.rows:
            if y < row.y() + row.height() / 2:
                return row.index
        return len(self.rows)

    def show_drop(self, index):
        if index is None:
            self.drop_bar.setVisible(False)
            return
        y = self.rows[index].y() - 2 if index < len(self.rows) else (self.rows[-1].y() + self.rows[-1].height() if self.rows else 0)
        self.drop_bar.setGeometry(0, max(0, y), self.inner.width(), 3)
        self.drop_bar.raise_()
        self.drop_bar.setVisible(True)

    def flash(self, item):
        """The row of `item` flashed and scrolled to (UI-015), its first field given the cursor."""
        from blink import Blinker
        row = self.row_of(item)
        if row is None:
            return None
        self.ensureWidgetVisible(row, 0, 40)
        row.blinker = Blinker(row, "#formRow")
        row.blinker.start()
        first = next((w for (i, _n), w in row.fields.items() if i == item and hasattr(w, "setFocus")), None)
        if first is not None:
            first.setFocus()
        return row

