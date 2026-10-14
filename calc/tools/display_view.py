"""The «Affichage» view of a tab (v0.117; docs/ui/window.md §10quater): the command chosen, its options, the call to copy, and in the middle the page that call prints.

The engineer's request of 07.10.2026: «dans le mode affichage, le volet de gauche ne change pas. Au centre, on a le compilé comme cela apparaîtrait dans le rapport. Et dans le volet de droite, on a les différentes options pour la commande, ainsi qu'on peut copier à la fin la commande» -- and, for the variables, «afficher l'une ou l'autre des commandes et ainsi voir les options qui sont disponibles pour l'une ou l'autre». Until then a tab's right pane mixed its Python result, the calls to copy, a command's options and its compiled preview (T18).

**One widget for every tab** (ARCH-002, rule 16): `DisplayView` gives a tab two pieces to place -- `right` (the drop-down of the commands, the chosen command's panel, the call and «Copier» at the end, the import line under it) and `preview` (what the export says of the object, then the compiled page) -- and the tab hands it, for the object chosen on its left, the `Entry` of each command that can show it (`set_entries`). Everything else is here: the panels (`SpecPanel`, drawn from display_options.SPECS), the call (`build_reference.call_command`, defaults read off the signature), the compile (`pdf_pane.PdfPane.request_snippet`, the newest request winning).

**Nothing compiles that is not seen** (review A10, B08): the pane is made the first time the view is shown (`activate`), its cache folder is the tab's own (`cache_key`), and leaving the view gives up a compile asked for -- never `stop()`, which waits for Typst.

**The plans' panel is their own** (`plan_command_builder.CommandOptions`, v0.114): a widget with the same three things a SpecPanel answers -- `values()`, `changed(dict)`, `set_context` is not needed -- handed as an Entry's `panel`. It stays a class of its own because what it offers depends on the plan's export record (the positions it carries, whether it has a scale), which a declaration cannot say; the reason is written here as rule 16 asks.
"""

from dataclasses import dataclass, field

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDoubleSpinBox, QHBoxLayout, QLabel, QLineEdit,
                               QListWidget, QListWidgetItem, QPushButton, QStackedWidget, QVBoxLayout, QWidget)

import build_reference as ref
import cards
import chrome
import display_options as opts
import flowbar
import pdf_pane
import project
import richtext
import structure_preview
import theme
import usersettings

STRINGS = opts.STRINGS

# What a typed width may be (plan_command_builder.WIDTH_PATTERN): anything else is left out of the call.
from plan_command_builder import WIDTH_PATTERN, CommandField  # noqa: E402  -- the call's field and the width's pattern are the plans' since v0.114


@dataclass
class Entry:
    """One command that can show the object chosen on the left: what the drop-down lists, and what the view needs to write its call and compile it."""
    key: str                         # unique among the entries of one object
    title: str                       # what the drop-down shows: the command's name, and a word where two entries share it
    command: str = ""                # the command whose panel is shown (display_options.SPECS); "" for a call written out (`call`)
    positional: tuple = ()           # the positional arguments of the call
    call: str = ""                   # a call written out -- a loop, a binding -- with no panel
    note: str = ""                   # the key of the words said instead of a preview (display_options.NOTES), "" to compile
    note_text: str = ""              # words of the tab's own said instead of a preview: why a draft cannot be computed
    banner: str = ""                 # what the export says of the object: not in it, or older than it -- said above the page
    context: dict = field(default_factory=dict)   # what an `ids` option offers, by option name
    always: tuple = ()               # options written even at their default (show-polar-moment's N, V, M)
    preset: dict = field(default_factory=dict)    # options set when the entry is first shown (the forces a polar moment was saved with)
    call_fn: object = None           # values -> the call, where call_command is not enough (the member check's own call_show_check_member)
    snippet_fn: object = None        # values -> the Typst the preview compiles in place of the header and the call (a member check's draft)
    panel: object = None             # a panel of the entry's own (the plans' CommandOptions), in place of the SpecPanel
    view: str = ""                    # the view of the command's declaration the panel offers (display_options.Spec.for_view): "display" for a command the «Formules» tab writes, "" for all of it
    panel_key: str = ""               # a panel of its own for this object, where the command's is shared by every object: an equation's options are that equation's (issue #19)
    apply_fn: object = None          # values -> whether they were written: what a change of the options writes before the page is compiled again -- the «Formules» tab's call in its file (issue #19, ARCH-006)


class ColumnsControl(QWidget):
    """The columns of a table, one row each: a check box and the width the column is given beside it (v0.117, display_options kind `columns`). A width is a number of mm, `30mm`, or a percentage of the text width, `20%`; empty, the column takes what its content needs. The last column ticked cannot be unticked -- a table with no column is no table -- and a width is only read where its column is ticked and what is typed is one (display_options.column_width): what is not is marked, and left out of the call."""

    changed = Signal()

    def __init__(self, keys, t, parent=None):
        super().__init__(parent)
        self.keys = tuple(keys)
        self.rows = {}
        self.quiet = False
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(3)
        for key in self.keys:
            row = QHBoxLayout()
            check = QCheckBox(t(f"ds_col_{key}"))
            check.setChecked(True)
            line = QLineEdit()
            line.setPlaceholderText(t("ds_width_placeholder"))
            line.setMaximumWidth(86)
            line.setToolTip(t("ds_width_bad"))
            check.toggled.connect(self._edited)
            line.textChanged.connect(self._edited)
            row.addWidget(check, 1)
            row.addWidget(line)
            v.addLayout(row)
            self.rows[key] = (check, line)
        self._guard()

    def _guard(self):
        ticked = [key for key in self.keys if self.rows[key][0].isChecked()]
        for key, (check, line) in self.rows.items():
            check.setEnabled(not (len(ticked) == 1 and key == ticked[0]))   # the last one stays
            line.setEnabled(check.isChecked())
            bad = bool(line.text().strip()) and opts.column_width(line.text()) is None
            line.setStyleSheet(f"border: 1px solid {theme.colour('danger')};" if bad else "")   # the theme's danger colour, as every other mark of a wrong value

    def _edited(self, *_args):
        self._guard()
        if not self.quiet:
            self.changed.emit()

    def state(self):
        """(the keys ticked, in their order; the widths typed for them, as Typst source -- `{key: "30mm"}`)."""
        ticked = tuple(key for key in self.keys if self.rows[key][0].isChecked())
        widths = {}
        for key in ticked:
            width = opts.column_width(self.rows[key][1].text())
            if width is not None:
                widths[key] = width
        return ticked, widths

    def set_state(self, ticked, widths):
        self.quiet = True
        try:
            keep = set(ticked) or set(self.keys)
            for key, (check, line) in self.rows.items():
                check.setChecked(key in keep)
                line.setText(str((widths or {}).get(key, "")))
        finally:
            self.quiet = False
        self._guard()


class LevelControl(QWidget):
    """The level of a command that takes `shown:` (issue #20, v0.117, display_options kind `detail`): a drop-down of the levels the command accepts and, where it takes `shown:`, -1 «Sélection manuelle» -- under which every variable the command can print stands with its level, **four buttons joined into one, `0 | 1 | 2 | 3`** (chrome.SegmentedSwitch, issue #41), the one down lightly set apart; 0 leaves the variable out of `shown:`, where until issue #41 a box was unticked beside a drop-down. The variables **flow side by side as the pane's width allows** (flowbar.FlowLayout, issue #41), one a row only where the pane is narrow. The engineer never types a name (T7): the variables are what the tab hands over (`set_keys`, `context["shown"]`, calc/shown_variables.py), a level chosen staying where its key is still there. A key that is the command's result (issue #39) is printed always: it offers `1 | 2 | 3` only, its 0 left out (the engineer's answer to issue #41). A class of the module and not a piece of SpecPanel, so that a tab's own panel -- the member checks' -- shows the same control (rule 16)."""

    changed = Signal()

    def __init__(self, levels, t, parent=None):
        super().__init__(parent)
        self.t = t
        self.quiet = False
        self.rows = {}           # key -> its switch, `0 | 1 | 2 | 3`
        self.wanted = {}         # {key: level} given back before the keys are known
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(4)
        self.combo = QComboBox()
        for value in levels:
            words = t("ds_level_auto") if value == "auto" else t("ds_level_manual") if value == opts.SELECTION else value
            self.combo.addItem(words, value)
        self.combo.currentIndexChanged.connect(self._edited)
        v.addWidget(self.combo)
        self.listing = flowbar.FlowWidget()
        self.listing.setToolTip(t("ds_shown_tip"))
        self.grid = flowbar.FlowLayout(self.listing, margin=0, spacing=8)
        self.grid.setContentsMargins(8, 2, 0, 2)
        v.addWidget(self.listing)
        self.empty = QLabel(t("ds_shown_none"))
        self.empty.setObjectName("meta")
        self.empty.setWordWrap(True)
        v.addWidget(self.empty)
        self._show()

    def level(self):
        return self.combo.currentData()

    @staticmethod
    def _value(switch):
        return int(switch.current_key() or 0)

    def picked(self):
        """{key: level} of the variables printed -- a level above 0 --, in the order they stand."""
        return {key: self._value(switch) for key, switch in self.rows.items() if self._value(switch)}

    def set_keys(self, keys):
        """The variables offered, as [key], [(key, words)] or [(key, words, math)]: words -- a table's title, display_options' own `ds_shown_<key>` -- are set as prose, `$…$` as math; a key without words by its math, the export's symbol or else shown_variables.key_math. Every key, a check's verdict included, goes from 0 to 3 (issue #58, which retired the locked result of issue #39). A key the new list lacks keeps its level, and comes back with it where a later list holds it again -- a draft a moment not calculable, or an angle changed, clears no choice (ARCH-RISK-206); the same list rebuilds nothing."""
        import shown_variables
        items = [(tuple(item) + (None, None))[:3] if isinstance(item, (tuple, list)) else (item, None, None) for item in keys or ()]
        if [item[0] for item in items] == list(self.rows):
            return
        kept = {**self.wanted, **self.picked()}
        for switch in self.rows.values():
            row = switch.parentWidget()
            self.grid.removeWidget(row)
            row.deleteLater()
        self.rows = {}
        self.quiet = True
        try:
            for key, words, math in items:
                row = QWidget()
                h = QHBoxLayout(row)
                h.setContentsMargins(0, 0, 0, 0)
                h.setSpacing(4)
                label = QLabel()
                label.setTextFormat(Qt.TextFormat.RichText)
                if words is None and f"ds_shown_{key}" in opts.STRINGS["en"]:
                    words = self.t(f"ds_shown_{key}")
                label.setText(richtext.prose_html(words) if words is not None else richtext.math_html(math or shown_variables.key_math(key)))
                label.setToolTip(key)
                n = int(kept.get(key, 0) or 0)
                switch = chrome.SegmentedSwitch([(str(m), str(m), "") for m in (0, 1, 2, 3)], str(n), soft=True)
                switch.changed.connect(self._edited)
                h.addWidget(label)
                h.addWidget(switch)
                self.grid.addWidget(row)
                self.rows[key] = switch
            self.wanted = {key: n for key, n in kept.items() if key not in self.rows}
        finally:
            self.quiet = False
        self.listing.updateGeometry()
        self._show()

    def set_state(self, value):
        """(level, {key: level}), or a level alone."""
        level, picked = value if isinstance(value, tuple) else (value, {})
        self.quiet = True
        try:
            self.combo.setCurrentIndex(max(self.combo.findData(str(level)), 0))
            for key, switch in self.rows.items():
                switch.set_current(str(int((picked or {}).get(key, 0) or 0)))
            self.wanted = {key: n for key, n in (picked or {}).items() if key not in self.rows}
        finally:
            self.quiet = False
        self._show()

    def state(self):
        return (self.level(), {**self.wanted, **self.picked()})

    def _show(self):
        manual = self.level() == opts.SELECTION
        self.listing.setVisible(manual and bool(self.rows))
        self.empty.setVisible(manual and not self.rows)

    def _edited(self, *_args):
        self._show()
        if not self.quiet:
            self.changed.emit()


class SpecPanel(QWidget):
    """The panel of one command, drawn from its declaration (display_options.Spec) in cards. `values()` are the keyword arguments of `build_reference.call_command` -- only what is set, a default left at its own state being dropped there. `changed(dict)` is emitted at every change the engineer makes, never at what the tab says (`set_context`, `set_values`)."""

    changed = Signal(dict)

    def __init__(self, spec, t, parent=None):
        super().__init__(parent)
        self.spec = spec
        self.t = t
        self.quiet = False
        self.controls = {}       # option name -> (Option, its control or controls)
        self.context = {}        # what the tab says of the object chosen: the ids an option offers, the flags an option needs (`@flag`)
        self.wanted = {}         # option name -> the ids a state given back (set_values) ticks, once the tab says which ids there are (set_context)
        self.defaults = ref.signature_defaults(spec.command) if spec.command in ref._signatures() else {}
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(8)
        layout = opts.card_layout(spec)
        if not layout:
            v.addWidget(cards.note(t("ds_no_options")))
        for title, options in layout:
            box = cards.card(t(title) if title else t("ds_options"))
            form = cards.form(box)
            for option in options:
                form.addRow(*self._row(option))
            v.addWidget(box)
        self.reset()
        self._enable()

    # -- the controls --

    def _row(self, option):
        t = self.t
        kind = option.kind
        label = t(option.label)
        if kind == "bool":
            check = QCheckBox(label)
            check.toggled.connect(self._edited)
            self.controls[option.name] = (option, check)
            return ("", check)
        if kind == "width":
            combo = QComboBox()
            combo.setEditable(True)
            combo.addItems(opts.WIDTHS)
            combo.setToolTip(t("ds_opt_width_tip"))
            combo.currentTextChanged.connect(self._edited)
            self.controls[option.name] = (option, combo)
            return (label, combo)
        if kind in ("level", "choice"):
            combo = QComboBox()
            for value in (option.choices or opts.LEVELS):
                if kind == "level":
                    words = t("ds_level_auto") if value == "auto" else t("ds_choice_none") if value == "none" else value
                else:
                    words = t(f"ds_choice_{value}")
                combo.addItem(words, value)
            combo.currentIndexChanged.connect(self._edited)
            self.controls[option.name] = (option, combo)
            return (label, combo)
        if kind in ("title", "caption"):
            holder = QWidget()
            hv = QVBoxLayout(holder)
            hv.setContentsMargins(0, 0, 0, 0)
            combo = QComboBox()
            for state in ("auto", "none", "custom"):
                combo.addItem(t(f"ds_{state}"), state)
            line = QLineEdit()
            line.setPlaceholderText(t("ds_custom_text"))
            hv.addWidget(combo)
            hv.addWidget(line)
            combo.currentIndexChanged.connect(self._edited)
            line.textChanged.connect(self._edited)
            self.controls[option.name] = (option, (combo, line))
            return (label, holder)
        if kind == "number":
            spin = QDoubleSpinBox()
            low, high, step = option.choices or (-1e6, 1e6, 1)
            spin.setRange(low, high)
            spin.setSingleStep(step)
            spin.setDecimals(3)
            spin.valueChanged.connect(self._edited)
            self.controls[option.name] = (option, spin)
            return (label, spin)
        if kind == "ids":
            listing = QListWidget()
            listing.setMaximumHeight(150)
            listing.itemChanged.connect(self._edited)
            self.controls[option.name] = (option, listing)
            return (label, listing)
        if kind == "detail":
            levels = tuple(option.choices or opts.LEVELS_SHOWN) + ((opts.SELECTION,) if "shown" in self.defaults else ())   # -1 where the command takes `shown:`, read off its signature (ARCH-008)
            control = LevelControl(levels, t)
            control.changed.connect(self._edited)
            self.controls[option.name] = (option, control)
            return (label, control)
        if kind == "columns":
            columns = ColumnsControl(option.choices, t)
            columns.setToolTip(t("ds_opt_columns_tip"))
            columns.changed.connect(self._edited)
            self.controls[option.name] = (option, columns)
            return (label, columns)
        line = QLineEdit()
        line.textChanged.connect(self._edited)
        self.controls[option.name] = (option, line)
        return (label, line)

    def reset(self):
        """Every control at its argument's default, as the signature writes it (display_options.initial)."""
        self.quiet = True
        try:
            for name, (option, control) in self.controls.items():
                start = opts.initial(option, self.defaults.get(name))
                self._set(option, control, start)
        finally:
            self.quiet = False
        self._enable()

    def _set(self, option, control, value):
        kind = option.kind
        if kind == "bool":
            control.setChecked(bool(value))
        elif kind == "width":
            control.setCurrentText(str(value))
        elif kind in ("level", "choice"):
            index = control.findData(str(value))
            control.setCurrentIndex(max(index, 0))
        elif kind in ("title", "caption"):
            combo, line = control
            state, text = value if isinstance(value, tuple) else ("custom", str(value))
            combo.setCurrentIndex(max(combo.findData(state), 0))
            line.setText(text)
        elif kind == "number":
            control.setValue(float(value or 0))
        elif kind == "ids":
            ticked = set(value or ())
            self.wanted[option.name] = ticked
            for row in range(control.count()):
                item = control.item(row)
                item.setCheckState(Qt.CheckState.Checked if item.data(Qt.ItemDataRole.UserRole) in ticked else Qt.CheckState.Unchecked)
        elif kind == "columns":
            ticked, widths = value if isinstance(value, tuple) and len(value) == 2 else (value or (), {})
            control.set_state(ticked, widths)
        elif kind == "detail":
            control.set_state(value)
        else:
            control.setText(str(value or ""))

    def set_values(self, values):
        """Controls set from `values` (option name -> the state `_set` takes): the forces a polar moment was saved with."""
        self.quiet = True
        try:
            for name, value in values.items():
                if name in self.controls:
                    option, control = self.controls[name]
                    self._set(option, control, value)
        finally:
            self.quiet = False
        self._enable()

    def set_context(self, context):
        """What the `ids` options offer for the object chosen -- the ids it carries; a tick stays where the id is still there -- and the flags an option needs (`@flag`)."""
        self.context = dict(context or {})
        self.quiet = True
        try:
            for name, (option, control) in self.controls.items():
                if option.kind == "detail":
                    control.set_keys(self.context.get(option.also[0], ()))
                    continue
                if option.kind != "ids":
                    continue
                kept = set(self._ids(control)) | self.wanted.pop(name, set())
                control.clear()
                for value in context.get(name, ()):
                    item = QListWidgetItem(str(value))
                    item.setData(Qt.ItemDataRole.UserRole, value)
                    item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                    item.setCheckState(Qt.CheckState.Checked if value in kept else Qt.CheckState.Unchecked)
                    control.addItem(item)
        finally:
            self.quiet = False
        self._enable()

    @staticmethod
    def _ids(listing):
        return [listing.item(row).data(Qt.ItemDataRole.UserRole) for row in range(listing.count())
                if listing.item(row).checkState() == Qt.CheckState.Checked]

    # -- the values --

    def values(self):
        """The keyword arguments of `build_reference.call_command` the controls say: only what is set -- a level left to the report, a title or a caption left automatic, an empty text, no id ticked are left out, and so is a width Typst would not read."""
        out = {}
        for name, (option, control) in self.controls.items():
            if option.needs and not self._needed(option.needs):
                continue          # greyed: it has no effect, and the command would refuse it (an option whose other option is off, or whose flag the object lacks)
            kind = option.kind
            if kind == "bool":
                out[name] = control.isChecked()
            elif kind == "width":
                width = control.currentText().strip()
                if WIDTH_PATTERN.match(width):
                    out[name] = ref.Raw(width)
            elif kind == "level":
                value = control.currentData()
                if value == "none":
                    out[name] = None
                elif value != "auto":
                    out[name] = int(value)
            elif kind == "choice":
                value = control.currentData()
                if value:
                    out[name] = value
            elif kind in ("title", "caption"):
                combo, line = control
                state = combo.currentData()
                if state == "none":
                    out[name] = None
                elif state == "custom" and line.text().strip():
                    out[name] = line.text()
            elif kind == "number":
                value = round(control.value(), 3)
                out[name] = int(value) if value == int(value) else value
            elif kind == "ids":
                ticked = self._ids(control)
                if ticked:
                    out[name] = tuple(ticked) if len(ticked) > 1 else ticked[0]
            elif kind == "detail":
                value = control.level()
                if value == opts.SELECTION:
                    out[name] = int(value)
                    out[option.also[0]] = control.picked()      # empty is `(:)`: the title and the verdict alone (D-09)
                elif value != "auto":
                    out[name] = int(value)
            elif kind == "columns":
                ticked, widths = control.state()
                start = opts.initial(option, self.defaults.get(name))[0]   # the command's own default, read off its signature: nothing written where it is what is ticked
                if ticked and tuple(ticked) != tuple(start):
                    out[name] = tuple(ticked)
                if widths and option.also:
                    out[option.also[0]] = {key: ref.Raw(width) for key, width in widths.items()}
            else:
                if control.text().strip():
                    out[name] = control.text().strip()
        return out

    def state(self):
        """What every control says, as `_set` takes it back: what a window rebuilt after an export is given again (DisplayView.snapshot), so that an option chosen stays chosen (v0.117, the engineer's decision D-012)."""
        out = {}
        for name, (option, control) in self.controls.items():
            kind = option.kind
            if kind == "bool":
                out[name] = control.isChecked()
            elif kind == "width":
                out[name] = control.currentText()
            elif kind in ("level", "choice"):
                out[name] = control.currentData()
            elif kind in ("title", "caption"):
                combo, line = control
                out[name] = (combo.currentData(), line.text())
            elif kind == "number":
                out[name] = control.value()
            elif kind == "ids":
                out[name] = self._ids(control)
            elif kind == "columns":
                ticked, _widths = control.state()
                out[name] = (ticked, {key: control.rows[key][1].text() for key in ticked})
            elif kind == "detail":
                out[name] = control.state()
            else:
                out[name] = control.text()
        return out

    # -- what the engineer does --

    def _edited(self, *_args):
        if self.quiet:
            return
        self._enable()
        self.changed.emit(self.values())

    def _enable(self):
        """What has an effect says so: a text box only for «my text», an option that needs another greyed until it is set."""
        for name, (option, control) in self.controls.items():
            if option.kind in ("title", "caption"):
                combo, line = control
                line.setEnabled(combo.currentData() == "custom")
            if option.needs:
                on = self._needed(option.needs)
                widget = control[0] if isinstance(control, tuple) else control
                widget.setEnabled(on)
                widget.setToolTip("" if on else self.t(option.needs_tip) if option.needs_tip else "")

    def _needed(self, needs):
        """Whether what an option needs is there (display_options.Option.needs): a flag of the object chosen (`@flag`), another option at a value (`name=value`), or another option on or not empty (`name`)."""
        if needs.startswith("@"):
            return bool(self.context.get(needs))
        name, _, wanted = needs.partition("=")
        if name not in self.controls:
            return True
        other, needed = self.controls[name]
        if wanted:
            return (needed.currentData() == wanted if other.kind in ("choice", "level") else needed.level() == wanted if other.kind == "detail" else False)
        return needed.isChecked() if other.kind == "bool" else bool(self._ids(needed)) if other.kind == "ids" else True


class OwnPanel(QWidget):
    """A panel a tab builds itself and hands over as an Entry's `panel` -- the member checks' options, which also say the unit of the verdict in the «Calcul» view and the options of the draft the preview compiles. It says only that it changed: the tab writes the call (`Entry.call_fn`)."""

    changed = Signal(dict)

    def __init__(self, body, parent=None):
        super().__init__(parent)
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.addWidget(body)

    def values(self):
        return {}


class DisplayView(QObject):
    """The «Affichage» view's two pieces for a tab: `right` and `preview` (see the module's docstring). `t` is the window's, `cache_key` the tab's own folder of compiled previews."""

    commandChanged = Signal(str)

    def __init__(self, t, mono_font=None, copy=None, cache_key="display", import_line=True, lang="fr", parent=None, import_fn=None, import_text=""):
        super().__init__(parent)
        self.t = t
        self.lang = lang
        self.cache_key = cache_key
        self.copy_text = copy or (lambda text: QApplication.clipboard().setText(text))
        self.here = None
        self.mode = None
        self.entries = []
        self.panels = {}          # entry command (or key, for a panel of its own) -> its panel, kept across objects: an option chosen stays chosen
        self.pending = {}         # panel key -> the state a window rebuilt after an export gives back, put in the panel when it is first made (restore)
        self.active = False
        self._pane = None
        self.filling = False

        # the right pane: the command, its options, the call at the end
        self.right = QWidget()
        rv = QVBoxLayout(self.right)
        rv.setContentsMargins(0, 0, 0, 0)
        scroll, column = cards.column()
        rv.addWidget(scroll)
        box = cards.card(t("ds_command"))
        bv = QVBoxLayout(box)
        self.chooser = QComboBox()
        self.chooser.setObjectName("displayCommand")
        self.chooser.setToolTip(t("ds_command_tip"))
        self.chooser.currentIndexChanged.connect(self._chosen)
        bv.addWidget(self.chooser)
        column.addWidget(box)
        self.stack = QStackedWidget()
        column.addWidget(self.stack)
        call_box = cards.card(t("ds_call"))
        cv = QVBoxLayout(call_box)
        font = mono_font
        if font is None:
            import theme
            font = theme.mono_font(self.right.font().pointSizeF())
        self.field = CommandField("", font)
        cv.addWidget(self.field)
        row = QHBoxLayout()
        row.addStretch(1)
        self.copy_button = richtext.copy_button(t("ds_copy"), t("ds_copied"), lambda: self.copy_text(self.command()))
        row.addWidget(self.copy_button)
        cv.addLayout(row)
        if import_line:
            cv.addWidget(cards.note(t("ds_import_line")))
            self.import_field = richtext.CodeField(ref.import_line(), font)
            irow = QHBoxLayout()
            irow.addWidget(self.import_field, 1)
            irow.addWidget(richtext.copy_button(t("ds_copy"), t("ds_copied"), lambda: self.copy_text(self.import_field.code)))
            cv.addLayout(irow)
        column.addWidget(call_box)
        column.addStretch(1)

        # the centre: what the export says of the object, what cannot be previewed, the page
        self.preview = QWidget()
        pv = QVBoxLayout(self.preview)
        pv.setContentsMargins(0, 0, 0, 0)
        pv.setSpacing(6)
        self.banner = QLabel()
        self.banner.setWordWrap(True)
        self.banner.setProperty("callout", "warning")
        self.banner.hide()
        banner_row = QHBoxLayout()
        banner_row.addWidget(self.banner, 1)
        # «Import données» beside what the export lacks (review B04): the engineer's own click, never an export in silence
        self.import_button = QPushButton(import_text) if import_fn is not None else None
        if self.import_button is not None:
            self.import_button.clicked.connect(lambda: import_fn())
            self.import_button.hide()
            banner_row.addWidget(self.import_button, 0, Qt.AlignmentFlag.AlignTop)
        pv.addLayout(banner_row)
        self.note = QLabel()
        self.note.setWordWrap(True)
        self.note.setProperty("callout", "info")
        self.note.hide()
        pv.addWidget(self.note)
        self.pane_box = QVBoxLayout()
        pv.addLayout(self.pane_box, 1)

    # -- the pane, made when it is first needed --

    @property
    def pane(self):
        if self._pane is None:
            self._pane = pdf_pane.PdfPane(self.preview, lang=self.lang, snippets_only=True)   # never the document's own PDF, whose title page showed while the first snippet compiled (issue #21)
            self._pane.preview_folder = usersettings.cache_dir("display", self.cache_key)   # a folder of each tab's own: two panes compiling at once never write one file (review B08)
            self.pane_box.addWidget(self._pane, 1)
        return self._pane

    # -- what the tab says --

    def set_project(self, here, mode=None):
        self.here = here
        self.mode = None
        if here is not None:
            self.mode = mode if mode in here.modes else here.modes[0]
        self.refresh()

    def activate(self, on):
        """The tab shows its «Affichage» view (`on`), or leaves it: shown, the page is asked for; left, a compile asked for and not started is given up."""
        self.active = bool(on)
        if self.active:
            self.refresh()
        elif self._pane is not None:
            self._pane.show_document()

    def set_entries(self, entries):
        """The commands that can show the object chosen on the left, the first chosen -- or the one of the same key as before, where it is still there: another object of the same tab keeps the command the engineer was looking at."""
        keep = self.current().key if self.current() is not None else None
        self.entries = list(entries)
        self.filling = True
        try:
            self.chooser.clear()
            for entry in self.entries:
                self.chooser.addItem(entry.title, entry.key)
            keys = [entry.key for entry in self.entries]
            self.chooser.setCurrentIndex(keys.index(keep) if keep in keys else (0 if keys else -1))
            self.chooser.setEnabled(len(self.entries) > 1)
        finally:
            self.filling = False
        self._show_entry()

    def current(self):
        index = self.chooser.currentIndex()
        return self.entries[index] if 0 <= index < len(self.entries) else None

    def panel(self):
        entry = self.current()
        if entry is None:
            return None
        return self.panels.get(self._panel_key(entry))

    @staticmethod
    def _panel_key(entry):
        if entry.panel_key:
            return entry.panel_key
        return f"own:{entry.key}" if entry.panel is not None else entry.command or f"call:{entry.key}"

    def values(self):
        panel = self.panel()
        return panel.values() if hasattr(panel, "values") else {}   # a call written out (a loop) has a panel with no option

    def snapshot(self):
        """The state of every panel drawn from a declaration -- {panel key: its controls' state} -- and the command chosen: what the window keeps through the rebuild every export ends in (D-012). A panel of a tab's own (the plans') says its own state or none."""
        panels = {key: panel.state() for key, panel in self.panels.items() if isinstance(panel, SpecPanel)}
        entry = self.current()
        return {"panels": panels, "entry": entry.key if entry is not None else None}

    def restore(self, snapshot):
        """The state a `snapshot` of the display before the rebuild holds, put back: in the panels already made, and in those made later, when their entry is first shown."""
        if not snapshot:
            return
        self.pending = dict(snapshot.get("panels") or {})
        for key in list(self.pending):
            panel = self.panels.get(key)
            if panel is not None and hasattr(panel, "set_values"):
                panel.set_values(self.pending.pop(key))

    def command(self):
        """The call the options say, for the command chosen -- "" with nothing chosen."""
        entry = self.current()
        if entry is None:
            return ""
        return entry_call(entry, self.values())

    def source(self):
        """The Typst the preview compiles: the snippet's header and the call -- or the entry's own (`snippet_fn`)."""
        entry = self.current()
        if entry is None or self.here is None:
            return None
        if entry.snippet_fn is not None:
            return entry.snippet_fn(self.values())
        return "\n".join(structure_preview.header(self.here, self.mode)) + "\n\n" + self.command() + "\n"

    def refresh(self):
        """The page of the call as it stands asked for -- only while the view is shown, and not for an entry that says why it has none."""
        entry = self.current()
        self.banner.setText(entry.banner if entry is not None else "")
        self.banner.setVisible(bool(entry is not None and entry.banner))
        if self.import_button is not None:
            self.import_button.setVisible(bool(entry is not None and entry.banner))
        note = entry.note if entry is not None else ""
        if entry is None:
            note = "ds_nothing"
        elif self.here is None:
            note = "ds_no_project"
        words = (self.t(note) if note else "") or (entry.note_text if entry is not None else "")
        self.note.setText(words)
        self.note.setVisible(bool(words))
        note = words
        if not self.active:
            return
        if note:
            if self._pane is not None:
                self._pane.show_document()
                self._pane.setVisible(False)
            return
        source = self.source()
        if source is None:
            return
        self.pane.setVisible(True)
        self.pane.request_snippet(self.here, self.mode, source, self.command())

    def stop(self):
        if self._pane is not None:
            self._pane.stop()

    # -- what the engineer does --

    def _chosen(self, _index):
        if not self.filling:
            self._show_entry()

    def _show_entry(self):
        entry = self.current()
        if entry is not None:
            key = self._panel_key(entry)
            panel = self.panels.get(key)
            if panel is None:
                spec = opts.spec(entry.command)
                panel = entry.panel if entry.panel is not None else SpecPanel(spec.for_view(entry.view) if entry.view else spec, self.t) if entry.command else QWidget()
                if hasattr(panel, "changed"):
                    panel.changed.connect(self._changed)
                self.panels[key] = panel
                self.stack.addWidget(panel)
                if key in self.pending and hasattr(panel, "set_values"):
                    panel.set_values(self.pending.pop(key))
            if entry.preset and hasattr(panel, "set_values") and getattr(panel, "preset", None) != entry.preset:
                panel.set_values(entry.preset)   # the tab's own values -- a polar moment's trial forces -- set again only when they change
                panel.preset = dict(entry.preset)
            if hasattr(panel, "set_context"):
                panel.set_context(entry.context)
            self.stack.setCurrentWidget(panel)
            self.stack.setVisible(True)
        else:
            self.stack.setVisible(False)
        self._show_command()
        self.refresh()

    def _show_command(self):
        command = self.command()
        self.field.set_code(command)
        self.copy_button.setEnabled(bool(command))
        return command

    def _changed(self, values):
        entry = self.current()
        if entry is not None and entry.apply_fn is not None and not entry.apply_fn(values):
            self._show_command()
            return      # refused -- a project open read-only: nothing written, nothing compiled again
        self.commandChanged.emit(self._show_command())
        self.refresh()


def entry_call(entry, values=None):
    """The call `entry` gives with the options `values` -- none, its bare call: what «Copier» copies before anything is changed."""
    values = dict(values or {})
    if entry.call:
        return entry.call
    if entry.call_fn is not None:
        return entry.call_fn(values)
    return ref.call_command(entry.command, *entry.positional, always=entry.always, **values)


def saved_state(t, oid, unsaved_text, unsaved, data_file, key, source_file):
    """The banner of an object of a tab that writes sources: `unsaved_text` while the draft is not saved -- the call would name what the export does not hold --, else what the export says of it (export_state), `key` being the dictionary of `data_file` that holds the objects by id."""
    if unsaved:
        return unsaved_text
    import json
    try:
        exported = oid in (json.loads(data_file.read_text(encoding="utf-8")).get(key) or {})
    except (OSError, ValueError, AttributeError):
        exported = False
    return export_state(t, oid, exported, source_file, data_file)


def export_state(t, oid, exported, source_file=None, export_file=None):
    """The banner of an object whose call reads the export (review B04): «not in the export yet» where `exported` is False, «changed since the last export» where its source was written after the export -- "" where the export is up to date. Nothing is exported here: «Import données» is the engineer's."""
    if not exported:
        return t("ds_not_exported", id=oid)
    try:
        if source_file is not None and export_file is not None and source_file.stat().st_mtime > export_file.stat().st_mtime + 1:
            return t("ds_stale", id=oid)
    except OSError:
        pass
    return ""


class ViewPanes:
    """A tab's splitter given its «Affichage» view (v0.117): in a tab of three panes -- the list, the form, the result -- the centre becomes a stack of the form and the preview, the right a stack of the result and the display's right pane; in a tab of two -- the list and the form -- the form becomes a stack of itself and the preview, and the display's right pane is a third pane shown only in «Affichage». The left pane never changes (T21: «le volet de gauche ne change pas»)."""

    def __init__(self, splitter, display, centre=1, right=2):
        self.display = display
        self.on = False
        self.centre = cards.CurrentStack()
        work = splitter.replaceWidget(centre, self.centre)
        self.centre.addWidget(work)
        self.centre.addWidget(display.preview)
        if right is not None:
            self.right = cards.CurrentStack()
            work = splitter.replaceWidget(right, self.right)
            self.right.addWidget(work)
            self.right.addWidget(display.right)
            self.third = None
        else:
            self.right = None
            self.third = display.right
            splitter.addWidget(display.right)
            display.right.setVisible(False)

    def show(self, on, enter=True):
        """The «Affichage» panes (`on`) or the work view's; with `enter` the display is activated -- its page compiled."""
        self.on = bool(on)
        self.centre.show_page(1 if on else 0)
        if self.right is not None:
            self.right.show_page(1 if on else 0)
        if self.third is not None:
            self.third.setVisible(self.on)
        self.display.activate(self.on and enter)


class DisplayTab:
    """What a tab of two views -- its work view and «Affichage» -- has in common (v0.117): mixed in before QWidget (`class StaticsTab(DisplayTab, QWidget)`), it builds the display and its panes on the tab's `splitter` (`install_display`), answers the top bar's switch (`set_view`), and tells the display, at every change of what is chosen, the entries the tab gives (`update_display` -> `display_entries`, the tab's own). The tab declares `VIEWS` (views.py) and calls `update_display()` where it filled its calls to copy until v0.117."""

    def install_display(self, cache_key, centre=1, right=2):
        self.display = DisplayView(self.t, mono_font=self.app.mono_font, copy=self.app.copy, cache_key=cache_key, lang=self.app.lang,
                                   import_fn=lambda: self.app.reexport(), import_text=self.t("reexport"), parent=self)   # owned by the tab: a QObject without a parent outlived the application and crashed the interpreter's exit
        self.panes = ViewPanes(self.splitter, self.display, centre, right)
        self.view = self.VIEWS[0]

    def set_view(self, key, enter=True):
        """The view `key` (views.py): the list stays, the other panes change. The page is compiled only in «Affichage», and only once the tab is shown (review A10)."""
        if key not in self.VIEWS or not hasattr(self, "panes"):
            return
        self.view = key
        on = key == "display"
        if on:
            self.update_display(force=True)
        self.panes.show(on, enter and self.isVisible())

    def update_display(self, force=False):
        """The display told what the tab has chosen: nothing is done outside «Affichage», where nothing is seen."""
        if self.view != "display" and not force:
            return
        self.display.set_project(project.current(), self.app.current_document())
        self.display.set_entries(self.display_entries())

    def display_entries(self):
        return []

    def showEvent(self, event):
        super().showEvent(event)
        if getattr(self, "view", None) == "display":
            self.panes.show(True)

    def loop_entry(self, command, call):
        """The loop over every object, which a preview does not show: the PDF does."""
        return Entry("loop", self.t("ds_loop", command=command), call=call, note="ds_note_loop")
