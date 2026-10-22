"""FormulaTab's domains -- the list on the left, a domain opened and computed, its blocks laid out -- and its name line and ID, new and duplicated domains: a mixin of methods moved verbatim out of calc/tools/formula_tab.py (issue #30). FormulaTab names it among its bases.
"""

from PySide6.QtCore import QEvent, QObject, Qt, QTimer, Signal
from PySide6.QtWidgets import (QApplication, QComboBox, QFrame, QGridLayout, QHeaderView, QLabel, QLineEdit, QPlainTextEdit, QPushButton,
                               QScrollArea, QSplitter, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)
import project
import units
from domains import formula_domain as fd
import grouped_list
import notifications
import notices_ui
import theme
from domains import formula_layout as fl
from formula_tab_widgets import Block, FIELDS, FORMULA_FIELDS, FormulaText, _ClickOutside, _Keys, math  # split out of this module (issue #30): every name it had is still importable from it


class FormulaDomainsMixin:
    """Methods of formula_tab.FormulaTab, moved verbatim (issue #30): the class names this mixin among its bases."""

    def reload(self, keep=None):
        """The domains read again from the project's Formules/: what VS Code changed is what the tab shows (REQ-006 of v0.117)."""
        keep = keep if keep is not None else self.current_id
        here = project.current()
        self.domains = fd.list_domains(here)
        self.fill_tree()
        found = next((d for d in self.domains if d.id == keep), None)
        if found is None and keep is None and self.domain is None and self.domains:
            found = self.domains[0]   # the tab never opens on nothing where there is a domain to show
        if found is not None:
            self.open_domain(found, select=False)
        elif self.domain is not None and self.current_id is None:
            self.show_domain()
        else:
            self.domain = None
            self.current_id = None
            self.show_domain()

    def resolve(self, command):
        """A variable taken from elsewhere (REQ-015 of v0.117): the export or another domain of the tab (formula_domain.resolve_import), named by its id -- or, for a domain of a document, the value the «Variables» tab last read off that document's PDF."""
        # the domain open as it is being edited, not as its file last was, and counted as the first of the chain -- a circle it closes is found
        domains = [self.domain if self.domain is not None and d.id == self.domain.id else d for d in self.domains]
        if self.domain is not None and self.domain not in domains:
            domains.append(self.domain)
        stack = (self.domain.id,) if self.domain is not None else ()
        got = fd.resolve_import(project.current(), command, domains, stack)
        if got is None and command.source and command.source[0] == "domain" and isinstance(command.source[1], str):
            listing = next((t for t in getattr(self.app, "tabs", ()) if hasattr(t, "begin_pick")), None)
            for (_origin, name), domain in (getattr(listing, "domains", None) or {}).items():
                var = domain.variable(command.key) if name == command.source[1] else None
                if var is not None and isinstance(var.value, (int, float)) and not isinstance(var.value, bool):
                    return var.value, var.unit
        return got

    def compute(self, domain):
        try:
            return fd.compute(domain, self.resolve)
        except units.FormulaError as exc:
            return [fd.Result(error=str(exc)) for _c in domain.commands]

    @staticmethod
    def block_results(domain, results):
        """The results of the commands alone -- a text gives none (ARCH-RISK-108) --, in the blocks' order."""
        return [r for c, r in zip(domain.commands, results) if not c.is_text]

    def fill_tree(self):
        """The list on the left: each domain under its name, the folder the engineer filed it in, in his order, unfolding into what it computes; «Archives» last."""
        entries = []
        for domain in self.domains:
            entry = {"id": domain.id, "text": domain.name or domain.id}
            if domain.state != "canonical":
                entry["colour"] = theme.colour("warning" if domain.state == "misnamed" else "danger")
                entry["tooltip"] = self.state_text(domain)
            results = self.block_results(domain, self.compute(domain)) if domain.state != "unreadable" else []
            commands = [c for c in domain.commands if not c.is_text]
            # a `val` in italics: a variable shown again, not one made (issue #19, D-04 -- in both views, the list being the same)
            entry["children"] = [{"id": f"{domain.id}#{index}", "text": self.summary(c, r), "italic": False} for index, (c, r) in enumerate(zip(commands, results))]
            group = fd.group_of(project.current(), domain)
            if group is not None:
                # a specialised tab's domain written out whole -- a member check unfolded -- in the group of its kind, «Traction», «Neige» …, which the engineer does not move (issue #64, REQ-016)
                entry["group"], entry["fixed"] = self.group_label(group), True
            entries.append(entry)
        archived = self.backend.entries(None, self.list._t)
        shown = self.shown_index()
        self.list.set_entries(entries, empty_folders=self.app.folder_settings(self.KEY), archived=archived,
                              select=f"{self.current_id}#{shown}" if shown is not None else self.current_id)   # the line chosen stays chosen: an option written in «Affichage» saves and rebuilds the list
        self.empty.setVisible(not self.domains and not archived)
        self.update_list_marker()

    def group_label(self, group):
        """The name of the group a specialised tab's domain is shown in (REQ-016): a member check's kind in the words of the checks' tabs -- «Traction» --, a steel check's after «Acier», every other kind its own word (fm_group_*)."""
        import member_check_tab_words
        import steel_tab_words
        kind, sub = group
        lang = self.app.lang
        if kind == "check":
            words = member_check_tab_words.STRINGS.get(lang, member_check_tab_words.STRINGS["fr"])
            return words.get("tab_mc_" + {"lateral-torsional": "ltb"}.get(sub, sub), sub)
        if kind == "steel":
            words = steel_tab_words.STRINGS.get(lang, steel_tab_words.STRINGS["fr"])
            return self.t("fm_group_steel", kind=words.get("tab_st_" + {"lateral-torsional": "ltb"}.get(sub, sub), sub))
        return self.t("fm_group_" + kind)

    def on_folders_changed(self):
        """A folder made, renamed or removed: an empty one kept in the project file as every tab keeps them, and the list rebuilt -- a domain's folder is written by the list itself (attach_order's `groups`)."""
        self.app.save_folder_settings(self.KEY, self.list.empty_folders())
        self.fill_tree()

    def summary(self, command, result):
        if result.error:
            return f"{command.shown_symbol or command.kind} — {result.error[:60]}"
        if command.kind == "verify":
            return f"{fd.display_formula(command.formula, [])} {'✔' if result.holds else '✘'}"
        return f"{command.shown_symbol} = {units.shown(result.value, result.unit)}"

    def state_text(self, domain):
        if domain.state == "misnamed":
            return self.t("fm_state_misnamed")
        if domain.state == "unreadable":
            return self.t("fm_state_unreadable", reason=domain.problem)
        return ""

    def on_tree_clicked(self, item, _column=0):
        if item.data(0, grouped_list.KIND_ROLE) not in ("leaf", "child"):
            return
        domain_id, _sep, index = str(item.data(0, grouped_list.ID_ROLE)).partition("#")
        index = int(index) if index else None
        listed = self.block_listed(index) if domain_id == self.current_id and index is not None else None
        if self.target is not None and listed is not None and self.target_alive():
            command = listed.command
            if command.defines:
                self.insert(command.shown_symbol)      # T19: a click on a variable of the domain writes it into the formula being typed
                return
        found = next((d for d in self.domains if d.id == domain_id), None)
        if found is None:
            return
        if found.id != self.current_id:
            if not self.confirm_leave():
                return
            self.open_domain(found)
        listed = self.block_listed(index) if index is not None else None
        self.shown_ref = self.ref_of(listed.command) if listed is not None else None
        self.update_display()        # «Affichage» offers the line chosen, or the domain (D-17)
        if listed is not None:
            self.show_pill(listed)

    def block_listed(self, index):
        """The block of the `index`-th command of the domain open -- the list on the left counts its commands, a text being none."""
        commands = [c for c in self.domain.commands if not c.is_text] if self.domain is not None else []
        return self.block_of(commands[index]) if index is not None and 0 <= index < len(commands) else None

    def block_of(self, command):
        return next((b for b in self.blocks if b.command is command), None)

    def show_pill(self, block):
        """The middle pane scrolled to the pill of `block`, or to its fields where it is open."""
        if block is self.open_block:
            self.scroll.ensureWidgetVisible(block)
            return
        for zone in self.zones:
            rect = zone.pill_rect(block.uid)
            if rect is not None:
                centre = zone.mapTo(self.scroll.widget(), rect.center())
                self.scroll.ensureVisible(centre.x(), centre.y(), 20, 40)
                return

    def open_domain(self, domain, select=True):
        self.domain = domain
        self.current_id = domain.id
        self.shown_ref = None
        self.dirty = False
        self.id_typed = True        # a domain written has its ID: a name changed never renames its file (REQ-004)
        self.target = None
        self.show_domain()
        if select:
            self.list.select(domain.id)
        self.update_display()

    def show_domain(self):
        """The middle and the right for the domain open, or the note that none is: the domain as one text, a pill for every command (issue #40)."""
        for widget in self.blocks + self.zones:
            widget.setParent(None)
            widget.deleteLater()
        self.blocks, self.zones, self.pills = [], [], {}
        self.open_block = None
        self.chosen_block = None
        self.domain_line = False
        domain = self.domain
        has = domain is not None
        self.name_edit.setVisible(has)
        self.scroll.setVisible(has)
        self.centre_note.setVisible(not has)
        usable = has and domain.state != "unreadable"
        why = "" if usable else self.t("fm_no_domain") if not has else self.state_text(domain)
        for button in list(self.command_buttons.values()) + [self.import_button]:
            button.setEnabled(usable)
            button.setToolTip(why if not usable else self.t("fm_import_tip") if button is self.import_button else "")   # a disabled button says why (tests/test_window.py)
        if not has:
            self.state_note.setVisible(False)
            self.refresh_unfold()
            self.results = []
            self.fill_variables()
            self.show_right()
            return
        self.name_edit.setText(domain.name)
        self.name_edit.setReadOnly(domain.state == "unreadable")
        self.id_edit.setText(domain.id)
        self.state_note.setText(self.state_text(domain))
        self.state_note.setVisible(domain.state != "canonical")
        self.domain_file.setText(project.current().rel(domain.path) if domain.path is not None else "")   # Domains/<id>.typ, or the specialised tab's folder of a domain written there (issue #64)
        self.results = self.compute(domain)
        for command, result in zip(domain.commands, self.results):
            if not command.is_text:
                self.blocks.append(self.new_block(command, result))
        # an unfolded check: its lines' states, read before the pills are drawn with them (UI-002)
        self.refresh_unfold()
        self.render()
        self.fill_variables()
        self.show_right()

    # --- the text and its pills (issue #40) --------------------------------------------------------

    def new_block(self, command, result=None, editing=False):
        """A block for `command`, named by a uid its pill carries (FormulaText.pill_format)."""
        block = self.connect_block(Block(self, command, result, editing=editing))
        self._uid = getattr(self, "_uid", 0) + 1
        block.uid = self._uid
        block.removed = False
        self.pills[block.uid] = block
        return block

    def pill_block(self, uid):
        return self.pills.get(uid) if uid is not None else None

    def render(self):
        """The domain open as one text again -- its commands pills where formula_layout lays them, inline in their sentence or on a line of their own -- and no block open: what a validation, a drop, a block given up end with. The blocks follow the domain's order."""
        for widget in self.zones:
            widget.setParent(None)
            widget.deleteLater()
        if self.open_block is not None:
            self.open_block.setParent(None)
        self.open_block = None
        by_command = {id(b.command): b for b in self.blocks}
        paragraphs = fl.to_paragraphs(self.domain.commands) if self.domain is not None else []
        shown = [[(kind, value if kind == "text" else by_command[id(value)].uid) for kind, value in p] for p in paragraphs
                 if all(kind == "text" or id(value) in by_command for kind, value in p)]
        self.zones = [self.make_zone(shown)]
        self.blocks = [by_command[id(c)] for c in (self.domain.commands if self.domain else ()) if not c.is_text and id(c) in by_command]
        self.relayout()

    def merged_runs(self):
        """The middle pane's paragraphs, a pill by its block: the one text, or -- a block open -- the text before it, the block, and the text after it, put back together as they were parted (D-04)."""
        def runs(zone):
            return [[(kind, value if kind == "text" else self.pills.get(value)) for kind, value in p if kind == "text" or value in self.pills] for p in zone.paragraphs()]
        if self.open_block is None:
            return runs(self.zones[0]) if self.zones else []
        before, after = runs(self.zones[0]), runs(self.zones[1])
        joined_before, joined_after = self.split_join
        own = ("cmd", self.open_block)
        if joined_before and before and before[-1]:
            paragraph = before.pop()
        else:
            paragraph = []
        paragraph.append(own)
        if joined_after and after and after[0]:
            paragraph.extend(after.pop(0))
        return before + [paragraph] + after

    def items(self):
        """The domain's items as the middle shows them now (formula_layout.from_paragraphs): its texts and its commands validated, a block added and not yet validated, or taken away, left out -- the text around it run together again."""
        paragraphs = []
        for runs in self.merged_runs():
            out = []
            for kind, value in runs:
                if kind == "cmd":
                    if value.fresh or value.removed:
                        continue
                    out.append(("cmd", value.command))
                elif out and out[-1][0] == "text":
                    left, right = out[-1][1], value
                    out[-1] = ("text", (left[:-1] if left.endswith(" ") else left) + " " + (right[1:] if right.startswith(" ") else right))
                else:
                    out.append(("text", value))
            paragraphs.append(out)
        return fl.from_paragraphs(paragraphs)

    def sync_blocks(self):
        """The blocks in the order the middle shows them -- a pill moved, or deleted with the text round it."""
        self.blocks = [value for runs in self.merged_runs() for kind, value in runs if kind == "cmd" and not value.removed]

    def open_at(self, block, before, after, joined=(False, False)):
        """`block` open as its row of fields on a line of its own, the text parted around it (D-04): `before` and `after` the paragraphs of either side; `joined` says whether the last of `before` and the first of `after` are the parts of the sentence the block stands in, put back round it when it closes."""
        self.split_join = (joined[0] and bool(before) and bool(before[-1]), joined[1] and bool(after) and bool(after[0]))
        for widget in self.zones:
            widget.setParent(None)
            widget.deleteLater()
        self.zones = [self.make_zone(before), self.make_zone(after)]
        self.open_block = block
        self.sync_blocks()
        self.relayout()
        block.show_editor()     # built once the block is in the window: a Tab order is set between fields of one window only
        self.show_pill(block)

    def open_pill(self, block):
        """A pill opened by a double-click: its fields in its place, the text before and after it parted (D-04)."""
        if self.open_block is not None or self.read_only_now():
            return
        zone = next((z for z in self.zones if z.pill_position(block.uid) is not None), None)
        if zone is None:
            return
        paragraphs = zone.paragraphs()
        p, r = next((p, r) for p, runs in enumerate(paragraphs) for r, (kind, value) in enumerate(runs) if kind == "cmd" and value == block.uid)
        head, tail = paragraphs[p][:r], paragraphs[p][r + 1:]
        self.open_at(block, paragraphs[:p] + ([head] if head else []), ([tail] if tail else []) + paragraphs[p + 1:], (bool(head), bool(tail)))

    def read_only_now(self):
        return bool(getattr(self.app, "read_only", False)) or self.domain is None or self.domain.state == "unreadable"

    def pill_clicked(self, zone, uid):
        block = self.pill_block(uid)
        if block is not None:
            self.on_block_chosen(block)
            for z in self.zones:
                z.repaint_pills()

    def pill_opened(self, zone, uid):
        """A double-click on a pill. A block being written elsewhere is validated first by the press (pressed_on), then this one opens -- if it validated."""
        if self.open_block is not None:
            QTimer.singleShot(0, self, lambda: self.open_pill(self.pills[uid]) if uid in self.pills and self.open_block is None else None)
            return
        if uid in self.pills:
            self.open_pill(self.pills[uid])

    def may_drag(self, zone):
        return self.open_block is None and not self.read_only_now() and zone in self.zones

    def drop_refusal(self, zone, position):
        """Why a pill may not be dropped at `position` of `zone`, or None (formula_layout.drop_refusal, D-06)."""
        p, r, k = zone.place_of(position)
        return fl.drop_refusal(zone.paragraphs(), (p, r, k if k is not None else 0))

    def pill_dropped(self, zone, uid, position):
        """A pill dropped elsewhere in the text (REQ-004): moved, the domain computed in its new order -- a variable dropped above what it is computed from refused with the domain's reason and put back --, written, and laid out again."""
        refusal = self.drop_refusal(zone, position)
        if refusal is not None:
            self.app.set_status(self.t("fm_drop_" + refusal[0]))
            return
        if not zone.move_pill(uid, position):
            return
        self.sync_blocks()
        items = self.items()
        if self.same(items, self.domain.commands):
            self.render()
            return
        trial = fd.Domain(id=self.domain.id, name=self.domain.name, commands=items)
        before = {id(c): r.error for c, r in zip(self.domain.commands, self.compute(self.domain))}
        broken = [(c, r.error) for c, r in zip(items, self.compute(trial)) if not c.is_text and r.error and not before.get(id(c))]
        if broken:
            self.fail(self.t("fm_drop_order", reason=broken[0][1]))
            self.sync_blocks_from_domain()
            self.render()
            return
        self.domain.commands = items
        self.dirty = True
        self.save(close_open=False)
        self.render()
        self.refresh_results()

    def sync_blocks_from_domain(self):
        by_command = {id(b.command): b for b in self.pills.values()}
        self.blocks = [by_command[id(c)] for c in self.domain.commands if not c.is_text and id(c) in by_command]

    def make_zone(self, paragraphs=()):
        zone = FormulaText(self, paragraphs)
        zone.setReadOnly(bool(getattr(self.app, "read_only", False)) or (self.domain is not None and self.domain.state == "unreadable"))
        zone.edited.connect(lambda _z: self.text_timer.start())
        zone.left.connect(lambda _z: self.write_text() if self.text_timer.isActive() else None)
        zone.entered.connect(self.zone_entered)
        return zone

    def zone_entered(self, _zone):
        self.domain_line = False
        self.show_right()

    def connect_block(self, block):
        block.validated.connect(self.on_validated)
        block.abandoned.connect(self.remove_block)
        block.focused.connect(self.on_field_focused)
        block.chosen.connect(self.on_block_chosen)
        return block

    def relayout(self):
        """The middle's widgets in their order -- the text, or the text before the block open, the block, the text after it -- and the stretch below them."""
        while self.blocks_layout.count():
            self.blocks_layout.takeAt(0)
        if self.zones:
            self.blocks_layout.addWidget(self.zones[0])
        if self.open_block is not None and len(self.zones) > 1:
            self.blocks_layout.addWidget(self.open_block)
            self.open_block.show()
            self.blocks_layout.addWidget(self.zones[1])
        self.blocks_layout.addStretch(1)

    def fill_variables(self):
        """The domain's variables, always on the right (T23): the symbol as mathematics, the value and its unit."""
        self.var_list.clear()
        rows = fd.variables_of(self.domain, self.results) if self.domain is not None else []
        for key, symbol, value, unit in rows:
            item = QTreeWidgetItem(self.var_list, [symbol or key, units.shown(value, unit)])
            item.setData(0, Qt.ItemDataRole.UserRole, key)
        self.var_none.setVisible(not rows)
        self.var_list.setVisible(bool(rows))

    def variables_before(self, block=None):
        """[(key, symbol)] of what the domain defines above `block` (all of it where None): what a formula may name."""
        out = []
        for b in self.blocks:
            if b is block:
                break
            c = b.command
            if c.defines and c.key not in dict(out):
                out.append((c.key, c.symbol))
        if block is None or block not in self.blocks:
            seen = dict(out)
            for c in (self.domain.commands if self.domain else ()):
                if c.defines and c.key not in seen:
                    out.append((c.key, c.symbol))
                    seen[c.key] = c.symbol
        return out

    def eventFilter(self, obj, event):
        if obj is self.name_edit:
            if event.type() == QEvent.Type.FocusIn and self.domain is not None:
                self.domain_line = True          # the domain's line chosen: its card, with its ID (T8 of v0.117, REQ-004)
                self.show_right()
            elif event.type() == QEvent.Type.KeyPress and event.key() == Qt.Key.Key_Down:
                self.name_done()
                return True
        return super().eventFilter(obj, event)

    def free_id(self, name):
        here = project.current()
        return fd.free_id(here, fd.slug(name or self.t("fm_new_name")), {d.id for d in self.domains})

    def name_typed(self, text):
        """The name typed: the ID made from it, as long as the domain is not written and its ID not typed by hand (REQ-004)."""
        if self.domain is not None and self.current_id is None and not self.id_typed:
            self.id_edit.setText(self.free_id(text.strip()))

    def id_typed_now(self, _text):
        self.id_typed = True

    def id_done(self):
        """The ID field left: checked; for a domain not yet written, the ID its first write takes; for one written, its file renamed (REQ-004)."""
        if self.domain is None:
            return
        new = self.id_edit.text().strip()
        if self.current_id is None:
            try:
                fd.check_id(new, self.domains, here=project.current())
            except fd.DomainError as exc:
                self.fail(self.refusal(exc))
                self.id_edit.setText(self.domain.id)
                return
            self.domain.id, self.domain.path = new, project.current().formulas_dir / f"{new}.typ"
            return
        if new != self.current_id:
            self.rename_id(new)

    def rename_id(self, new):
        """The domain's ID changed: its file renamed and its `#var-domain` rewritten, its place and folder in the list following it, and what still cites the old ID listed -- never rewritten (D-11)."""
        old = self.current_id
        here = project.current()
        try:
            saved, cited = fd.rename(here, self.domain, new, self.domains)
        except (fd.DomainError, ValueError, OSError) as exc:
            self.id_edit.setText(old)
            if getattr(exc, "code", "") == "changed_on_disk":
                return self.changed_on_disk(exc)
            return self.fail(self.refusal(exc))
        self.index_refused(saved)
        self.app.list_store.rename(self.KEY, old, new)
        self.current_id = new
        self.domain = saved
        self.app.set_status(self.t("fm_renamed", id=new))
        if cited:
            lines = "\n".join(f"{file}:{line}  {text}" for file, line, text in cited)
            notices_ui.tell(self.t("fm_cited", old=old, lines=lines), notifications.WARNING, key="fm_cited", source="formula_tab")
        self.reload(keep=new)
        return True

    def name_done(self):
        """Enter, or ↓, on the domain's line: the name kept -- the domain written where it is new, under the ID shown -- and the commands offered (T9 of v0.117)."""
        if self.domain is None:
            return
        name = self.name_edit.text().strip()
        if name != self.domain.name or self.current_id is None:
            try:
                fd.check_name(name)
            except fd.DomainError as exc:
                self.fail(self.refusal(exc))
                self.name_edit.setText(self.domain.name)
                return
            if self.current_id is None:
                fid = self.id_edit.text().strip() if self.id_typed else self.free_id(name)
                try:
                    fd.check_id(fid, self.domains, here=project.current())
                except fd.DomainError as exc:
                    self.fail(self.refusal(exc))
                    return
                self.domain.id, self.domain.path = fid, project.current().formulas_dir / f"{fid}.typ"
            self.domain.name = name
            self.dirty = True
            self.save()
        self.name_edit.clearFocus()
        self.domain_line = False
        self.show_right()

    def new_domain(self):
        """«Domaine» (D-01 of v0.117): a new domain, its name to type on the first line (UI-004). Nothing is written before the name is validated."""
        if not self.confirm_leave():
            return
        here = project.current()
        name = self.t("fm_new_name")
        self.domain = fd.new_domain(here, name, self.domains)
        self.current_id = None
        self.id_typed = False
        self.dirty = True
        self.show_domain()
        self.update_list_marker()
        self.name_edit.setFocus()
        self.name_edit.selectAll()

    def duplicate_domain(self):
        """«Dupliquer le domaine» (REQ-009): a copy written at once under «<name> (copie)» and a free ID, beside what it copies in the list and in its folder."""
        if self.domain is None or self.current_id is None or not self.confirm_leave():
            return False
        here = project.current()
        try:
            copy = fd.duplicate(here, self.domain, self.t("fm_copy", name=self.domain.name), self.domains)
        except (fd.DomainError, ValueError, OSError) as exc:
            return self.fail(self.refusal(exc))
        self.index_refused(copy)
        store = self.app.list_store
        store.insert_after(self.KEY, copy.id, self.current_id, store.tab(self.KEY)[1].get(self.current_id, ""))
        self.reload(keep=copy.id)
        return True
