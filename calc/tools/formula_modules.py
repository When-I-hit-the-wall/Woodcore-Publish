"""The modules on the right of the «Domaines» tab: État du domaine, Arguments de la ligne, Résultats, Variables du domaine, and the excerpts of the norm pinned under them (issue #113, spec docs/requirements/completed/2026-10-24-onglet-domaines-formulaire-code.md, UI-004, UI-011, UI-012, UI-015, UI-016, UI-017, REQ-014, ARCH-003).

They are modules of the common pane (calc/tools/module_pane.py, issues #94, #95): moved by their header, folded, opened in a window of their own, their order kept on this machine -- in this order the first time (UI-004). Each body is told to show the tab again (`refresh`); nothing is computed here, everything is the tab's (its domain, its results, its state) and every write is one of its guarded writers.

* **État du domaine** (UI-015): the faults in red and the warnings in orange, each said once, in the window's language (formula_tab_words.say); a click on one goes to its line -- the row flashes and its field takes the cursor, in «Code» the line is selected --; its fix where it has one («Lier q_k1 depuis Neige · SL», «Ouvrir les options du domaine»).
* **Arguments de la ligne** (UI-012): in «Code» every argument of the command of the cursor, in «Formulaire» the others of the row chosen; a value changed is written into the line; under them, the line as the file writes it.
* **Résultats** (UI-016): every `eq` and `verify`; a click unfolds the formula in letters and in numbers; «Tout déplier», «Tout replier», «Copier les valeurs»; the name of a result, dotted, writes itself into the calculation being typed (UI-011).
* **Variables du domaine** (UI-017): symbol, value, origin -- «ce domaine» or «↗ Neige · SL» --; a click writes the variable into the calculation being typed; «Lier une variable…».

The clickable parts take no focus: the field being typed keeps its cursor (UI-011).
"""

import html

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (QComboBox, QFormLayout, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QPlainTextEdit, QPushButton,
                               QVBoxLayout, QWidget)

import module_pane
import richtext
import theme
import units
from domains import formula_args

ORDER = ("state", "args", "results", "variables")


class _Clickable(QLabel):
    def __init__(self, text, on_click, tip=""):
        super().__init__(text)
        self.on_click = on_click
        self.setTextFormat(Qt.TextFormat.RichText)
        self.setWordWrap(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        if tip:
            self.setToolTip(tip)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.on_click()
            event.accept()
            return
        super().mousePressEvent(event)


def _button(text, slot):
    button = QPushButton(text)
    button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    button.clicked.connect(lambda _c=False: slot())
    return button


class _Body(QWidget):
    def __init__(self, tab):
        super().__init__()
        self.tab = tab
        self.box = QVBoxLayout(self)
        self.box.setContentsMargins(4, 2, 4, 4)
        self.refresh()

    def __init_subclass__(cls, **kwargs):
        """Each body's `refresh` followed by `_fit`: its height held to what it now holds -- the pane's column, which caches the heights of its modules, would keep the old one (a body refilled from one line to twenty)."""
        super().__init_subclass__(**kwargs)
        refresh = cls.__dict__.get("refresh")
        if refresh is not None:
            def fitted(self, *args, _refresh=refresh, **kw):
                _refresh(self, *args, **kw)
                self._fit()
            cls.refresh = fitted

    def hasHeightForWidth(self):
        """No height for a width of its own: the pane's column, laying out modules of heights for widths, kept the first height of a body refilled since (a body grown from one line to twenty stayed one line high) -- its height is its `minimumHeight`, set by `_fit`."""
        return False

    def _fit(self):
        """The body's least height, measured once its new widgets are shown -- a widget added to a shown parent is shown at the next turn of the loop, and measures nothing until then."""
        QTimer.singleShot(0, self, self._fit_now)

    def _fit_now(self):
        try:
            self.box.invalidate()
            width = self.width() if self.width() > 50 else 300
            height = self.box.heightForWidth(width) if self.box.hasHeightForWidth() else self.box.sizeHint().height()
            self.setMinimumHeight(max(0, height))
        except RuntimeError:
            pass   # the body went with a rebuilt pane

    def clear(self):
        while self.box.count():
            item = self.box.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()
            elif item.layout() is not None:
                _clear_layout(item.layout())


def _clear_layout(layout):
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
            widget.setParent(None)
            widget.deleteLater()
        elif item.layout() is not None:
            _clear_layout(item.layout())


class StateBody(_Body):
    """État du domaine -- see the module's docstring."""

    def refresh(self):
        self.clear()
        tab = self.tab
        st = tab.state
        self.messages = []
        if st is None:
            return
        for m in st.errors + st.warnings:
            colour = theme.colour("danger" if m.level == "error" else "warning")
            text = html.escape(tab.say(m))
            if m.level == "error" and m.dependents:
                text += '<br><span style="color:%s">%s</span>' % (theme.colour("muted"), html.escape(tab.t("fm_e_cascade", n=m.dependents)))
            label = _Clickable('<span style="color:%s">%s</span> %s' % (colour, "!" if m.level == "error" else "ⓘ", text), lambda m=m: tab.go_to(m))
            self.box.addWidget(label)
            self.messages.append((m, label))
            if m.fix:
                self.box.addWidget(_button(tab.say_fix(m.fix), lambda m=m: tab.apply_fix(m)), 0, Qt.AlignmentFlag.AlignLeft)
        if not st.errors:
            ok = QLabel('<span style="color:%s">✓</span> %s' % (theme.colour("ok"), html.escape(tab.t("fm_ok"))))
            ok.setWordWrap(True)
            self.box.addWidget(ok)


class ArgsBody(_Body):
    """Arguments de la ligne -- see the module's docstring."""

    def refresh(self):
        self.clear()
        tab = self.tab
        t = tab.t
        context = tab.args_context()
        self.fields = {}
        if isinstance(context, str):
            note = QLabel(context)
            note.setWordWrap(True)
            note.setStyleSheet("color: %s;" % theme.colour("muted"))
            self.box.addWidget(note)
            return
        index, everything, command, result, table, where = context
        head = QLabel('<span style="color:%s">%s</span> · %s' % (theme.colour("syn-call"), command.kind, html.escape(where)))
        head.setFont(tab.app.mono_font)
        self.box.addWidget(head)
        self.head = head
        note = QLabel(t("fm_a_all" if everything else "fm_a_other"))
        note.setWordWrap(True)
        note.setStyleSheet("color: %s;" % theme.colour("muted"))
        self.box.addWidget(note)
        form = QFormLayout()
        for argument in formula_args.arguments(command, everything, result, table):
            if argument.kind in ("choice", "unit"):
                combo = QComboBox()
                combo.addItem(t("fm_a_auto"), "")
                for value in argument.choices:
                    combo.addItem(str(value), str(value))
                if argument.value and combo.findData(argument.value) < 0:
                    combo.addItem(argument.value, argument.value)
                combo.setCurrentIndex(max(0, combo.findData(argument.value)))
                combo.activated.connect(lambda _i, n=argument.name, c=combo: tab.write_argument(index, n, c.currentData()))
                widget = combo
            else:
                line = QLineEdit(argument.value)
                line.setPlaceholderText("—")
                line.editingFinished.connect(lambda n=argument.name, l=line: tab.write_argument(index, n, l.text()))
                widget = line
            self.fields[argument.name] = widget
            label = QLabel(argument.name)
            label.setFont(tab.app.mono_font)
            form.addRow(label, widget)
        self.box.addLayout(form)
        self.box.addWidget(QLabel(t("fm_a_line")))
        written = QPlainTextEdit(formula_args.written(command))
        written.setReadOnly(True)
        written.setMaximumHeight(64)
        written.setFont(tab.app.mono_font)
        self.written = written
        self.box.addWidget(written)


class ResultsBody(_Body):
    """Résultats -- see the module's docstring."""

    def refresh(self):
        self.tab.forget_lit("results")
        self.clear()
        tab = self.tab
        t = tab.t
        self.names = {}
        self.open = getattr(self, "open", set())
        self.entries = []
        domain = tab.domain
        if domain is None:
            return
        grid = QGridLayout()
        grid.setColumnStretch(0, 1)
        for column, word in ((0, "fm_r_line"), (1, "fm_r_val")):
            head = QLabel(t(word))
            head.setStyleSheet("color: %s;" % theme.colour("muted"))
            grid.addWidget(head, 0, column)
        row = 1
        for i, c in enumerate(domain.commands):
            if c.kind not in ("eq", "verify"):
                continue
            r = tab.results[i] if i < len(tab.results) else None
            if r is None:
                continue
            if c.kind == "eq":
                name = _Clickable('<span style="border-bottom: 1px dotted %s">%s</span>' % (theme.colour("muted"), richtext.math_html(c.symbol or c.key)),
                                  lambda c=c: tab.insert_variable(c.key), t("fm_r_ins"))
                value = "✘" if r.error else units.shown(r.value, r.unit)
            else:
                name = QLabel(richtext.math_html(c.formula))
                name.setTextFormat(Qt.TextFormat.RichText)
                value = "✘" if r.error else ("✔" if r.holds else "✘")
            toggle = _Clickable("<b>%s</b>" % html.escape(value), lambda i=i: self.toggle(i))
            grid.addWidget(name, row, 0)
            grid.addWidget(toggle, row, 1)
            tab.hover(name, i, "results")
            self.names[i] = name
            cite = " ".join(str(x) for x in (c.options.get("norm"), c.options.get("norm-section")) if x)
            if cite:
                grid.addWidget(QLabel('<span style="color:%s">%s</span>' % (theme.colour("muted"), html.escape(cite))), row, 2)
            row += 1
            self.entries.append(i)
            if i in self.open:
                text = html.escape(r.error) if r.error else (richtext.math_html(r.letters) + ("<br>= " + richtext.math_html(r.numbers) if r.numbers else ""))
                detail = QLabel(text)
                detail.setTextFormat(Qt.TextFormat.RichText)
                detail.setWordWrap(True)
                grid.addWidget(detail, row, 0, 1, 3)
                row += 1
        self.box.addLayout(grid)
        buttons = QHBoxLayout()
        buttons.addWidget(_button(t("fm_r_unfold"), self.unfold_all))
        buttons.addWidget(_button(t("fm_r_fold"), self.fold_all))
        buttons.addWidget(_button(t("fm_r_copy"), tab.copy_values))
        buttons.addStretch(1)
        self.box.addLayout(buttons)

    def toggle(self, i):
        self.open ^= {i}
        self.refresh()

    def unfold_all(self):
        self.open = set(self.entries)
        self.refresh()

    def fold_all(self):
        self.open = set()
        self.refresh()


class VariablesBody(_Body):
    """Variables du domaine -- see the module's docstring."""

    def refresh(self):
        self.clear()
        tab = self.tab
        t = tab.t
        self.entries = []
        domain = tab.domain
        grid = QGridLayout()
        grid.setColumnStretch(2, 1)
        row = 0
        for i, c in enumerate(domain.commands if domain is not None else ()):
            if not c.defines:
                continue
            r = tab.results[i] if i < len(tab.results) else None
            symbol = c.symbol or (r.symbol if r is not None else "") or c.key
            name = _Clickable(richtext.math_html(symbol), lambda c=c: tab.insert_variable(c.key), t("fm_variables_tip"))
            value = QLabel(html.escape(units.shown(r.value, r.unit)) if r is not None and not r.error else "—")
            origin = tab.origin_text(r.origin if r is not None else None, c) if c.source else t("fm_v_own")
            where = QLabel('<span style="color:%s">%s</span>' % (theme.colour("muted"), html.escape(origin)))
            grid.addWidget(name, row, 0)
            grid.addWidget(value, row, 1)
            grid.addWidget(where, row, 2)
            self.entries.append((c.key, name))
            row += 1
        self.box.addLayout(grid)
        self.box.addWidget(_button(t("fm_v_link"), lambda: tab.open_link_dialog(None)), 0, Qt.AlignmentFlag.AlignLeft)


def build(tab, store=None):
    """The pane of modules of the tab, in the order of UI-004 the first time; `tab.pane_bodies` its bodies by id."""
    pane = module_pane.ModulePane(tab.t, tab.KEY, store)
    tab.pane_bodies = {}
    for mid, title, factory in (("state", "fm_m_state", StateBody), ("args", "fm_m_args", ArgsBody), ("results", "fm_m_res", ResultsBody), ("variables", "fm_m_vars", VariablesBody)):
        def make(factory=factory, mid=mid):
            body = factory(tab)
            tab.pane_bodies.setdefault(mid, body)
            return body
        pane.add(module_pane.ModuleSpec(mid, tab.t(title), make, kind=mid))
    return pane
