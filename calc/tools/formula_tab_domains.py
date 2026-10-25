"""FormulaTab's domains: the list on the left, a domain opened, its name line and its ID, a new domain and a copy (split out of calc/tools/formula_tab.py by issue #30; the list folded by issue #113).

**The list on the left** (issue #113, UI-002, ARCH-RISK-015): the domains of the tab, each under its name with its state -- «✔ 70 %» after its last check, «1 ✘» for a fault (calc/domains/formula_state.py `summary`) --, then the groups of the specialised tabs -- «Neige», «Traction» … -- whose domains Woodcore wrote out, and «Archives» last; **no domain is unfolded line by line** any more (more than 300 lines in the example): its lines are the form's. What a list shows of a domain is words, never Typst (`c_("red", "b/h")`, defect 7).
"""

from PySide6.QtCore import QEvent, Qt

import project
import units
from domains import formula_domain as fd
from domains import formula_state
import theme


class FormulaDomainsMixin:
    """Methods of formula_tab.FormulaTab for its domains: the class names this mixin among its bases."""

    def reload(self, keep=None):
        """The domains read again from the project's Domains/: what VS Code changed is what the tab shows (REQ-006 of v0.117)."""
        keep = keep if keep is not None else self.current_id
        here = project.current()
        self.domains = fd.list_domains(here)
        found = next((d for d in self.domains if d.id == keep), None)
        if found is None and keep is None and self.domain is None and self.domains:
            found = self.domains[0]   # the tab never opens on nothing where there is a domain to show
        if found is not None:
            self.current_id = found.id
        self.fill_tree()
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
        from domains import formula_links
        try:
            return fd.compute(domain, self.resolve, describe=formula_links.describer(project.current(), self.domains))
        except units.FormulaError as exc:
            return [fd.Result(error=str(exc), code=exc.code, values=dict(exc.values)) for _c in domain.commands]

    def fill_tree(self):
        """The list on the left: each domain under its name and its state, the folder the engineer filed it in, in his order; the domains of the specialised tabs in their groups; «Archives» last (UI-002)."""
        entries = []
        for domain in self.domains:
            entry = {"id": domain.id, "text": self.list_text(domain)}
            if domain.state != "canonical":
                entry["colour"] = theme.colour("warning" if domain.state == "misnamed" else "danger")
                entry["tooltip"] = self.state_text(domain)
            group = fd.group_of(project.current(), domain)
            if group is not None:
                # a specialised tab's domain written out whole -- a member check unfolded -- in the group of its kind, «Traction», «Neige» …, which the engineer does not move (issue #64, REQ-016)
                entry["group"], entry["fixed"], entry["folded"] = self.group_label(group), True, True   # folded (UI-002): its lines are the form's
            entries.append(entry)
        archived = self.backend.entries(None, self.list._t)
        self.list.set_entries(entries, empty_folders=self.app.folder_settings(self.KEY), archived=archived, select=self.current_id)
        self.empty.setVisible(not self.domains and not archived)
        self.update_list_marker()

    def list_text(self, domain):
        """A domain as the list names it: its name, and its state -- «✔ 88 %», «✘ 127 %», «1 ✘» (UI-002)."""
        name = domain.name or domain.id
        if domain.state == "unreadable":
            return f"{name}   ✘"
        said = formula_state.summary(domain, self.compute(domain))
        if said is None:
            return name
        kind, value = said
        if kind == "bad":
            return f"{name}   {value} ✘"
        if value is None:
            return name
        return f"{name}   {'✔' if kind == 'ok' else '✘'} {value} %"

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
        """A folder made, renamed or removed: an empty one kept in the project file as every tab keeps them, and the list rebuilt."""
        self.app.save_folder_settings(self.KEY, self.list.empty_folders())
        self.fill_tree()

    def state_text(self, domain):
        if domain.state == "misnamed":
            return self.t("fm_state_misnamed")
        if domain.state == "unreadable":
            return self.t("fm_state_unreadable", reason=domain.problem)
        return ""

    def on_tree_clicked(self, item, _column=0):
        import grouped_list
        if item.data(0, grouped_list.KIND_ROLE) not in ("leaf", "child"):
            return
        domain_id = str(item.data(0, grouped_list.ID_ROLE))
        found = next((d for d in self.domains if d.id == domain_id), None)
        if found is None or found.id == self.current_id:
            return
        if not self.confirm_leave():
            return
        self.open_domain(found)

    def open_domain(self, domain, select=True):
        self.domain = domain
        self.current_id = domain.id
        self.dirty = False
        self.id_typed = True        # a domain written has its ID: a name changed never renames its file (REQ-004)
        self.form.chosen = None
        self.chosen_item = None
        self.form.target = None
        self.form.selection.clear()
        self.undo.forget()
        self.show_undo(None)
        self.show_domain()
        if select:
            self.list.select(domain.id)
        self.update_display()

    def show_domain(self):
        """The centre and the right for the domain open, or the note that none is."""
        domain = self.domain
        has = domain is not None
        for widget in (self.name_edit, self.id_edit, self.file_label, self.legend, self.work):
            widget.setVisible(has)
        self.centre_note.setVisible(not has)
        self.duplicate_button.setEnabled(has and self.current_id is not None)
        if not has:
            self.state_note.setVisible(False)
            self.results, self.state = [], None
            self.refresh_unfold()
            self.form.show_domain(None, [], rebuild=True)
            self.refresh_modules()
            return
        self.name_edit.setText(domain.name)
        self.name_edit.setReadOnly(domain.state == "unreadable")
        self.id_edit.setText(domain.id)
        self.state_note.setText(self.state_text(domain))
        self.state_note.setVisible(domain.state != "canonical")
        self.file_label.setText(project.current().rel(domain.path) if domain.path is not None else "")
        self.refresh_unfold()
        self.recompute(rebuild=True)
        if self.view == "code":
            self.code.set_text(domain.text or fd.file_text(domain))

    # --- the name line and the ID ------------------------------------------------------------------

    def eventFilter(self, obj, event):
        if obj is self.name_edit and event.type() == QEvent.Type.KeyPress and event.key() == Qt.Key.Key_Down:
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
        """The domain's ID changed: its file renamed and its `#domain` rewritten, its place and folder in the list following it, and what still cites the old ID listed -- never rewritten (D-11)."""
        import notifications
        import notices_ui
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
        """Enter, or ↓, on the domain's line: the name kept -- the domain written where it is new, under the ID shown, with `#calc-defaults(presets: "block", scope: "domain")` (D-3)."""
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
            self.save_domain(self.domain.commands)
        self.name_edit.clearFocus()

    def new_domain(self):
        """«Domaine» (D-01 of v0.117): a new domain, its name to type on the first line (UI-004), opening on `#calc-defaults(presets: "block", scope: "domain")` (D-3). Nothing is written before the name is validated."""
        if not self.confirm_leave():
            return
        here = project.current()
        self.domain = fd.new_domain(here, self.t("fm_new_name"), self.domains)
        self.current_id = None
        self.id_typed = False
        self.dirty = True
        self.undo.forget()
        self.show_domain()
        self.update_list_marker()
        self.name_edit.setFocus()
        self.name_edit.selectAll()

    def duplicate_domain(self):
        """«Dupliquer» (REQ-009 of issue #15): a copy written at once under «<name> (copie)» and a free ID, beside what it copies in the list and in its folder."""
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
