"""«Lier une variable…» of the «Domaines» tab: variables of the project chosen in a list, linked all at once (issue #113, spec docs/requirements/completed/2026-10-24-onglet-domaines-formulaire-code.md, UI-014, REQ-013, D-5, D-12, ARCH-010).

Opened by the button of the module «Variables du domaine» or by the + between two rows → «lier une variable…». The variables a link may take -- the export's cases, the other domains of the tab (calc/domains/formula_links.py `linkable`, the same source as the «Variables» tab's and the linked fields', #42, #114) -- **grouped by tab and by case**, with a search. **A box on the left** of each; **a click** chooses one alone, without linking it; **Ctrl+click** adds or takes one away, **Shift+click** a range, a click on its box adds or takes it away -- the choice «comme dans Windows» of the «Variables» tab, its one model (calc/variable_select.py, ARCH-010); **«Valider (n)»** writes the links of everything ticked, at once, in the order of the list, above the row chosen -- one write, which «Annuler» takes back (D-17) --; Enter validates, Escape closes. A variable already in the domain is greyed, «déjà dans ce domaine».
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTreeWidget, QTreeWidgetItem, QVBoxLayout

import richtext
import theme
import units
import variable_select

KEY_ROLE = Qt.ItemDataRole.UserRole + 1


class LinkDialog(QDialog):
    """See the module's docstring. `candidates` [{key, calc, instance, symbol, label, value, unit, group}], `taken` the keys the domain holds, `group_title(candidate)` the title of its group («Neige · SL»)."""

    def __init__(self, t, domain_name, candidates, taken, group_title, parent=None):
        super().__init__(parent)
        self.t = t
        self.setWindowTitle(t("fm_pick_t", domain=domain_name))
        self.candidates = list(candidates)
        self.taken = set(taken)
        self.group_title = group_title
        self.selection = variable_select.Selection()
        self.chosen_result = None
        self.resize(560, 520)
        column = QVBoxLayout(self)
        self.search = QLineEdit()
        self.search.setPlaceholderText(t("fm_pick_s"))
        self.search.textChanged.connect(lambda _t: self.fill())
        column.addWidget(self.search)
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setColumnCount(4)   # the box, the symbol (as Typst sets it), the value, the label
        self.tree.setItemDelegateForColumn(1, richtext.MathDelegate(self.tree, (1,)))
        self.tree.itemPressed.connect(self.pressed)
        column.addWidget(self.tree, 1)
        help_ = QLabel(t("fm_pick_help"))
        help_.setWordWrap(True)
        help_.setStyleSheet("color: %s;" % theme.colour("muted"))
        column.addWidget(help_)
        foot = QLabel(t("fm_pick_f"))
        foot.setWordWrap(True)
        foot.setStyleSheet("color: %s;" % theme.colour("muted"))
        column.addWidget(foot)
        row = QHBoxLayout()
        row.addStretch(1)
        cancel = QPushButton(t("fm_nl_no"))
        cancel.clicked.connect(self.reject)
        row.addWidget(cancel)
        self.ok = QPushButton(t("fm_pick_ok", n=0))
        self.ok.setDefault(True)
        self.ok.clicked.connect(self.validate)
        row.addWidget(self.ok)
        column.addLayout(row)
        self.items = {}
        self.fill()

    @staticmethod
    def key_of(candidate):
        return (candidate.get("calc") or "", candidate.get("instance") or "", candidate["key"])

    def shown(self):
        """The candidates the search leaves, in the order of the list: by group, then as given."""
        text = self.search.text().strip().casefold()
        out = []
        for c in self.candidates:
            hay = " ".join(str(c.get(k) or "") for k in ("key", "symbol", "label", "calc", "instance")).casefold()
            if not text or text in hay:
                out.append(c)
        groups = []
        for c in out:
            title = self.group_title(c)
            if title not in groups:
                groups.append(title)
        return sorted(out, key=lambda c: groups.index(self.group_title(c)))

    def shown_keys(self):
        return [self.key_of(c) for c in self.shown() if c["key"] not in self.taken]

    def fill(self):
        self.tree.clear()
        self.items = {}
        groups = {}
        for c in self.shown():
            title = self.group_title(c)
            parent = groups.get(title)
            if parent is None:
                parent = QTreeWidgetItem(self.tree, [title])
                parent.setFlags(Qt.ItemFlag.ItemIsEnabled)
                font = parent.font(0)
                font.setBold(True)
                parent.setFont(0, font)
                parent.setFirstColumnSpanned(True)
                parent.setExpanded(True)
                groups[title] = parent
            value = units.shown(c["value"], c.get("unit", "")) if isinstance(c.get("value"), (int, float)) else str(c.get("value") or "")
            item = QTreeWidgetItem(parent, ["", c.get("symbol") or c["key"], value, c.get("label") or ""])
            key = self.key_of(c)
            item.setData(0, KEY_ROLE, key)
            if c["key"] in self.taken:
                item.setFlags(Qt.ItemFlag.NoItemFlags)
                item.setText(3, self.t("fm_pick_has"))
                item.setForeground(3, Qt.GlobalColor.gray)
            else:
                item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(0, Qt.CheckState.Checked if key in self.selection else Qt.CheckState.Unchecked)
            self.items[key] = item
        for column in (0, 1, 2):
            self.tree.resizeColumnToContents(column)
        self.paint()

    def paint(self):
        for key, item in self.items.items():
            if item.flags() & Qt.ItemFlag.ItemIsUserCheckable:
                item.setCheckState(0, Qt.CheckState.Checked if key in self.selection else Qt.CheckState.Unchecked)
        self.ok.setText(self.t("fm_pick_ok", n=len(self.selection)))
        self.ok.setEnabled(len(self.selection) > 0)

    def click(self, key, ctrl=False, shift=False, box=False):
        """A click on the variable `key`: the gesture of variable_select.Selection."""
        self.selection.click(key, self.shown_keys(), ctrl=ctrl, shift=shift, box=box)
        self.paint()

    def pressed(self, item, column):
        from PySide6.QtWidgets import QApplication
        key = item.data(0, KEY_ROLE)
        if key is None or not (item.flags() & Qt.ItemFlag.ItemIsUserCheckable):
            return
        modifiers = QApplication.keyboardModifiers()
        on_box = column == 0
        self.click(key, ctrl=bool(modifiers & Qt.KeyboardModifier.ControlModifier), shift=bool(modifiers & Qt.KeyboardModifier.ShiftModifier), box=on_box)

    def chosen(self):
        """The candidates ticked, in the order of the list (UI-014)."""
        order = self.selection.keys(self.shown_keys())
        by_key = {self.key_of(c): c for c in self.candidates}
        return [by_key[k] for k in order if k in by_key]

    def validate(self):
        if not len(self.selection):
            return
        self.chosen_result = self.chosen()
        self.accept()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.validate()
            return
        super().keyPressEvent(event)
