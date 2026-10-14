"""FormulaTab's blocks and texts -- a block added, validated, removed, its options and its command, what is typed inserted where the cursor stands -- and the variables taken from elsewhere: a mixin of methods moved verbatim out of calc/tools/formula_tab.py (issue #30). FormulaTab names it among its bases.
"""

import html
from dataclasses import replace
from PySide6.QtCore import QEvent, QObject, Qt, QTimer, Signal
from PySide6.QtWidgets import (QApplication, QComboBox, QFrame, QGridLayout, QHeaderView, QLabel, QLineEdit, QPlainTextEdit, QPushButton,
                               QScrollArea, QSplitter, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)
import units
import build_reference as ref
from domains import formula_domain as fd
import cards
import display_options as opts
import display_view
from formula_tab_widgets import Block, FIELDS, FORMULA_FIELDS, FormulaText, _ClickOutside, _Keys, math  # split out of this module (issue #30): every name it had is still importable from it


def merged_options(options, offered, values):
    """The options of a call once a panel offering `offered` (option names) says `values`: what it does not offer kept as it was, what it offers as it says -- an option left at its default, absent from `values`, gone from the call (issue #19, ARCH-005: «Calcul» and «Affichage» write one call)."""
    out = {name: value for name, value in options.items() if name not in offered}
    out.update({name: (str(value) if isinstance(value, ref.Raw) else value) for name, value in values.items() if value is not None})
    return out


class FormulaBlocksMixin:
    """Methods of formula_tab.FormulaTab, moved verbatim (issue #30): the class names this mixin among its bases."""

    def add_block(self, kind, zone=None):
        """A command of the palette clicked: a block of it, being written on a line of its own (D-04) -- where the cursor of the text stands, the sentence cut there (REQ-006 of issue #15): the text that has the focus, the palette's buttons taking none --; else after the pill chosen, in its sentence, or at the end."""
        if self.domain is None or self.read_only_now():
            return
        if self.open_block is not None:
            if not self.open_block.fresh:
                return
            self.remove_block(self.open_block)     # an empty block added a moment ago gives way to the one asked for now
        focus = zone if zone is not None else QApplication.focusWidget()
        block = self.new_block(fd.Command(kind), editing=True)
        text = self.zones[0] if self.zones else None
        paragraphs = text.paragraphs() if text is not None else []
        if focus is text and text is not None:
            p, r, k = text.place_of(text.textCursor().position())
            runs = paragraphs[p] if p < len(paragraphs) else []
            if k is not None and r < len(runs):
                value = runs[r][1]
                head = runs[:r] + ([("text", value[:k])] if value[:k] else [])
                tail = ([("text", value[k:])] if value[k:] else []) + runs[r + 1:]
            else:
                head, tail = runs[:r], runs[r:]
            before, after = paragraphs[:p] + ([head] if head or not tail else []), ([tail] if tail else []) + paragraphs[p + 1:]
            joined = (bool(head), bool(tail))
        elif self.chosen_block is not None and text is not None and text.pill_position(self.chosen_block.uid) is not None:
            p, r = next((p, r) for p, runs in enumerate(paragraphs) for r, (kind, value) in enumerate(runs) if kind == "cmd" and value == self.chosen_block.uid)
            head, tail = paragraphs[p][:r + 1], paragraphs[p][r + 1:]
            before, after, joined = paragraphs[:p] + [head], ([tail] if tail else []) + paragraphs[p + 1:], (True, bool(tail))
        else:
            before, after, joined = paragraphs, [], (False, False)
        self.open_at(block, before, after, joined)
        self.on_block_chosen(block)   # made being written: its `chosen` went out before it was connected

    def panel_options(self, block):
        """(options, output unit) the right pane says for `block`, where it is the block chosen -- over the options it does not offer, which «Affichage» wrote and which stay (issue #19, ARCH-005: the two views write one call, neither erasing the other's)."""
        options = merged_options(block.command.options, self.panel.controls, self.panel.values())
        unit = self.unit_box.currentData() if self.unit_box is not None else block.command.unit
        return options, unit

    def command_from(self, block):
        """The command a block's fields say -- a key made from the shown variable where none is typed (REQ-008), a formula's symbols written as their keys and its units quoted (D-17) -- and the options of the right pane: its own while it is chosen, those it was left with where another block was chosen since (ARCH-RISK-103). Raises fd.DomainError."""
        old = block.command
        kind = old.kind
        taken = {c.defines for b in self.blocks if b is not block for c in [b.command] if c.defines and c.kind != "var-unit"}
        variables = self.variables_before(block)
        options, out_unit = dict(old.options), old.unit
        if self.panel is not None and self.chosen_block is block:
            options, out_unit = self.panel_options(block)
        elif getattr(block, "pending", None) is not None:
            options, out_unit = block.pending
        command = fd.Command(kind, options=options, source=old.source)
        if kind in ("var", "eq"):
            symbol = block.text("symbol")
            if kind == "var":
                key = block.text("key")
            else:   # an equation keeps its key while its symbol is the one it was given, and takes one from a new symbol (T18)
                key = old.key if old.key and symbol == (old.symbol or old.key) else ""
            if not key and not symbol:
                raise fd.DomainError("missing", self.t("fm_missing", field=self.t("fm_f_symbol")))
            if not key:
                key = fd.key_from_symbol(symbol, taken)
            if key in taken:
                raise fd.DomainError("key_taken", self.t("fm_key_taken", name=key), key=key)
            command.key = key
            command.symbol = fd.symbol_for(symbol, key)
        if kind == "var":
            command.unit = units.written_unit(block.text("unit"))
            if old.source:
                command.value = old.value
            else:
                text = block.text("value").replace(",", ".").replace(" ", "")
                try:
                    command.value = int(text) if text.lstrip("-").isdigit() else float(text)
                except ValueError:
                    raise fd.DomainError("value", self.t("fm_not_number", text=text))
        elif kind == "eq":
            command.formula = fd.typst_formula(block.text("formula"), variables)
            command.unit = out_unit
        elif kind == "verify":
            command.formula = fd.typst_formula(block.text("formula"), variables)
        elif kind == "val":
            typed = block.text("key")
            command.key = dict((s or k, k) for k, s in variables).get(typed, typed)
        elif kind == "var-unit":
            typed = block.text("key")
            command.key = dict((s or k, k) for k, s in variables).get(typed, typed)
            command.unit = units.written_unit(block.text("unit"))
        # what the report would refuse is refused here, before the file is written (Python never laxer than Typst)
        trial = fd.Domain(id=self.domain.id, name=self.domain.name,
                          commands=[command if b is block else b.command for b in self.blocks if not b.removed])
        results = self.compute(trial)
        error = results[[b for b in self.blocks if not b.removed].index(block)].error
        if error:
            raise fd.DomainError("formula", error)
        return command

    def refresh_results(self):
        """What every pill shows once the domain is computed again: drawn again, not laid out again -- the cursor and the typing stay where they are."""
        self.results = self.compute(self.domain)
        by_command = {id(c): r for c, r in zip(self.domain.commands, self.results)}
        for b in self.pills.values():
            if id(b.command) in by_command:
                b.result = by_command[id(b.command)]
        for zone in self.zones:
            zone.repaint_pills()
        self.fill_variables()

    def on_validated(self, block, command):
        """A block validated: its command written, the domain laid out again as one text -- the block a pill where formula_layout puts it (D-04) --, its options left on the right."""
        block.command = command
        block.fresh = False
        block.pending = None
        self.domain.commands = self.items()
        self.dirty = True
        if not self.save():
            if not block.editing:
                block.show_editor()
            return
        self.render()
        self.refresh_results()
        block.show_view()
        self.block_closed(block)

    def give_up_block(self, block):
        """Escape on a block validated before: its pill again, as it was; what was typed in the text meanwhile kept."""
        self.write_text()
        block.show_view()
        self.render()
        self.refresh_results()
        self.block_closed(block)

    def block_closed(self, block):
        if self.target is not None and not self.target_alive():
            self.target = None
        if self.chosen_block is block:
            self.on_block_chosen(block, again=True)   # its options stay, now written as they change (REQ-003)

    def remove_block(self, block):
        """A block taken away -- its ✕, or one added and left empty: the text around it run together again, the domain written without it."""
        block.removed = True
        items = self.items()
        if self.chosen_block is block:
            self.chosen_block = None
        if self.domain is not None and self.current_id is not None and not self.same(items, self.domain.commands):
            self.domain.commands = items
            self.dirty = True
            self.save(close_open=False)
        self.pills.pop(block.uid, None)
        if block is self.open_block or block in self.blocks:
            self.blocks = [b for b in self.blocks if b is not block]
        if self.domain is not None:
            self.render()
            self.refresh_results()
        block.setParent(None)
        block.deleteLater()
        self.show_right()

    @staticmethod
    def same(a, b):
        """Two lists of items the same, as the file would write them."""
        key = lambda c: (c.kind, c.raw if c.is_text else fd.to_call(c))   # noqa: E731
        return [key(c) for c in a] == [key(c) for c in b]

    def write_text(self):
        """The text written into the file once the typing pauses, or the text is left (REQ-006 of issue #15): what the file would not read back -- a computing command, a tag line, a bracket too many -- refused with its reason, nothing written. A pill deleted with the text around it is a command taken away (issue #40): the others computed again."""
        self.text_timer.stop()
        if self.domain is None or self.current_id is None or self.domain.state == "unreadable":
            return False
        items = self.items()
        if self.same(items, self.domain.commands):
            return True
        previous = self.domain.commands
        gone = {id(c) for c in previous if not c.is_text} != {id(c) for c in items if not c.is_text}
        self.domain.commands = items
        self.dirty = True
        if not self.save(close_open=False):
            self.domain.commands = previous
            return False
        self.sync_blocks()
        if gone:
            self.refresh_results()
        return True

    def write_options(self):
        """An option of a validated block changed on the right (REQ-003): written at once into the file, the block left closed."""
        self.option_timer.stop()
        block = self.chosen_block
        if block is None or block.editing or block not in self.blocks or self.panel is None or self.domain is None:
            return False
        options, unit = self.panel_options(block)
        command = replace(block.command, options=options, unit=unit if block.command.kind == "eq" else block.command.unit)
        if self.same([command], [block.command]):
            return True
        self.replace_command(block, command)
        self.dirty = True
        if not self.save(close_open=False):
            return False
        self.refresh_results()
        return True

    def replace_command(self, block, command):
        """An option of a line changed (REQ-003, issue #19): the command put in its place in the domain, and nothing else re-read from the pane -- a `note:` that moved the pill onto a line of its own and back writes no paragraph (issue #40, REQ-002). What was typed in the text and not yet written is written first."""
        if self.text_timer.isActive():
            self.write_text()
        self.domain.commands = [command if c is block.command else c for c in self.domain.commands]
        block.command = command

    def pressed_on(self, widget):
        """A press anywhere (_ClickOutside): in the middle pane but outside the block being written, that block validated as Enter does -- after the press, which may be rebuilding what it landed on (REQ-007, ARCH-RISK-110). A block added and left empty is taken away. The right pane, the list and the name line validate nothing."""
        open_blocks = [b for b in self.blocks if b.editing]
        if not open_blocks:
            return
        viewport = self.scroll.viewport()
        try:
            inside = widget is viewport or viewport.isAncestorOf(widget)
        except RuntimeError:
            return
        if not inside:
            return
        for block in open_blocks:
            if widget is block or block.isAncestorOf(widget):
                continue
            if block.fresh and not any(f.text().strip() for f in block.fields.values()):
                QTimer.singleShot(0, block, block.give_up)
            else:
                QTimer.singleShot(0, block, block.validate)

    def on_field_focused(self, field):
        if field.property("formulaField") in FORMULA_FIELDS:
            self.target = field

    def target_alive(self):
        try:   # a field of a block still being written: not deleted (a block validated rebuilds its content) and not hidden
            return self.target is not None and not self.target.isHidden() and any(self.target in b.fields.values() for b in self.blocks if b.editing)
        except RuntimeError:
            return False

    def insert(self, text):
        """`text` written into the formula being typed, where its cursor was (REQ-010 of v0.117), and the focus given back to it."""
        if not self.target_alive():
            return
        field = self.target
        pos = field.cursorPosition()   # a field keeps its cursor when it loses the focus to the click
        field.setText(field.text()[:pos] + text + field.text()[pos:])
        field.setFocus()
        field.setCursorPosition(pos + len(text))

    def on_variable_clicked(self, item, _column=0):
        key = item.data(0, Qt.ItemDataRole.UserRole)
        symbol = dict(self.variables_before()).get(key) or key
        self.insert(symbol)

    def on_block_chosen(self, block, again=False):
        """A block chosen -- being written, or validated, by a single click (REQ-003): its options on the right, above the commands -- every argument of the command its middle does not fill, read off the signature (ARCH-003) -- and an equation's output unit (T21). For a block validated, an option changed is written into the file once the typing pauses."""
        if block is self.chosen_block and self.panel is not None and not again:
            self.domain_line = False
            self.show_right()
            return
        previous = self.chosen_block
        if previous is not None and previous is not block and previous in self.blocks and previous.editing and self.panel is not None:
            previous.pending = self.panel_options(previous)    # what was set for it is not lost to the block chosen now
        if self.option_timer.isActive():
            self.write_options()                               # an option of the block left, changed a moment ago, written before its panel goes
        self.chosen_block = block
        self.domain_line = False
        while self.options_layout.count():
            item = self.options_layout.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()
        kind = block.command.kind
        command = block.command
        pending = getattr(block, "pending", None)
        options, unit = (pending if pending is not None else (command.options, command.unit))
        self.unit_box = None
        if kind == "eq":
            card = cards.card(self.t("fm_out_unit"))
            form = cards.form(card)
            self.unit_box = QComboBox()
            result = block.result or fd.Result()
            dims = units.parse_unit(result.unit)[1] if result.unit and units.parse_unit(result.unit) else None
            offered = units.offered_units(dims) if dims is not None else []
            auto_unit = units.pick_unit(dims) if dims is not None else ""
            self.unit_box.addItem(self.t("fm_out_auto", unit=auto_unit or "—"), "")
            for one in offered:
                if one:
                    self.unit_box.addItem(one, one)
            if unit and self.unit_box.findData(unit) < 0:
                self.unit_box.addItem(unit, unit)
            self.unit_box.setCurrentIndex(max(0, self.unit_box.findData(unit)))
            form.addRow(self.t("fm_out_unit"), self.unit_box)
            self.options_layout.addWidget(card)
        # «Calcul» offers what the line is -- its label, its description, its citation --, and «Affichage» how it is printed (issue #19, display_options.Spec.for_view)
        spec = opts.spec(kind).for_view("calc")
        self.panel = display_view.SpecPanel(spec, self.t)
        self.panel.set_values({k: v for k, v in options.items() if k in self.panel.controls})
        self.options_layout.addWidget(QLabel(f"<b>{html.escape(self.t('fm_options', command=kind))}</b>"))
        self.options_layout.addWidget(self.panel)
        if not block.editing:
            self.panel.changed.connect(lambda *_a: self.option_timer.start())
            if self.unit_box is not None:
                self.unit_box.currentIndexChanged.connect(lambda *_a: self.option_timer.start())
        self.show_right()

    def import_variable(self):
        """«Importer…»: the «Variables» tab in its choosing mode, every other tab unavailable until a variable is chosen or the choice given up (UI-007)."""
        if self.domain is None:
            return
        begin = getattr(self.app, "begin_variable_pick", None)
        if begin is None or not begin(self.on_picked, self.t("fm_pick_title", domain=self.domain.name)):
            self.app.set_status(self.t("fm_import_unavailable"))

    def on_picked(self, chosen):
        """What the «Variables» tab gave back: (source, domain, variable, its export address or None), or None where the choice was given up. A domain of this tab is named by its id (D-06)."""
        if chosen is None or self.domain is None:
            return
        source, domain_name, var, address = chosen
        taken = {c.defines for c in self.domain.commands if c.defines}
        key = var.key if var.key not in taken else fd.key_from_symbol(var.key, taken)
        if address is not None:
            call = "var-of(" + ", ".join(ref.typst_str(x) for x in (address[0], address[1], var.key)) + ")"
            command = fd.Command("var", key=key, symbol="" if key == var.key else var.key, source=("var-of", call))
        elif domain_name:
            command = fd.Command("var", key=key, source=("domain", domain_name))
        else:
            self.fail(self.t("fm_import_refused", name=var.key))
            return
        self.domain.commands.append(command)
        result = self.compute(self.domain)[-1]
        if fd.CIRCLE in result.error:   # two domains taking their values from each other: refused here, nothing written
            self.domain.commands.pop()
            self.fail(result.error)
            return
        self.dirty = True
        self.save()
        self.reload(self.current_id)
