"""FormulaTab's card of a member check printed unfolded (spec docs/requirements/completed/2026-10-15-calculs-deplies-balises-figures-natives.md, UI-002): where each line of the domain stands against its check and its file, and what Woodcore can do with it -- «Importer», «Tout importer», «Reprendre», «Réinsérer», «Régénérer», and in a conflict «Garder la mienne» or «Prendre celle de l'export».

**Nothing is decided here** (ARCH-005): the states and every write are calc/domains/unfold.py's, the very functions `woodcore-cli unfold` calls; this mixin shows them, gives each row of the form its line's state -- the stripe of the row since issue #113 (REQ-015), where it was the outline of a pill (`item_states`, coloured by calc/domains/formula_state.py `COLOURS`) -- and calls them. Every action that writes is one of woodcore_gui.WRITERS, refused while the project is read only.
"""

import html

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget

import cards
import notifications
import notices_ui
import project
import theme
import validation
from domains import unfold

from domains import formula_state


class FormulaUnfoldMixin:
    """Methods of formula_tab.FormulaTab for an unfolded check's domain: the class names this mixin among its bases."""

    def build_unfold_card(self):
        """The card shown while the domain open is an unfolded check (its `gen:`): the check it is written from, whether its form is still the export's, the lines that are not in step and the actions on them."""
        self.unfold_states = {}
        self.unfold_status = None
        card = cards.card(self.t("fm_unfold"))
        v = QVBoxLayout(card)
        self.unfold_head = QLabel("")
        self.unfold_head.setWordWrap(True)
        v.addWidget(self.unfold_head)
        self.unfold_list = QTreeWidget()
        self.unfold_list.setColumnCount(2)
        self.unfold_list.setHeaderHidden(True)
        self.unfold_list.setRootIsDecorated(False)
        self.unfold_list.setMaximumHeight(180)
        self.unfold_list.itemSelectionChanged.connect(self.unfold_selection)
        v.addWidget(self.unfold_list)
        self.unfold_none = cards.note(self.t("fm_unfold_in_step"))
        v.addWidget(self.unfold_none)
        row = QWidget()
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 0, 0, 0)
        self.unfold_buttons = {}
        for key, slot in (("import", self.write_unfold_import), ("import_all", self.write_unfold_import_all), ("take_back", self.write_unfold_take_back),
                          ("reinsert", self.write_unfold_reinsert), ("mine", lambda: self.write_unfold_choice("mine")),
                          ("theirs", lambda: self.write_unfold_choice("theirs")), ("regenerate", self.write_unfold_regenerate)):
            button = QPushButton(self.t(f"fm_unfold_{key}"))
            button.setToolTip(self.t(f"fm_unfold_{key}_tip"))
            button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            button.clicked.connect(lambda _checked=False, slot=slot: slot())
            self.unfold_buttons[key] = button
        for key in ("import", "import_all", "take_back", "reinsert", "mine", "theirs", "regenerate"):
            v.addWidget(self.unfold_buttons[key], 0, Qt.AlignmentFlag.AlignLeft)
        self.unfold_card = card
        card.setVisible(False)
        return card

    # --- reading ----------------------------------------------------------------------------------

    @staticmethod
    def _in_unfold_base(rid):
        """Whether Woodcore wrote domain `rid` from its data -- a member check, a steel check (unfold.DOMAIN_KINDS) --: the base of its kind holds it -- a file of the generator 2 carries no `gen:` (spec 2026-10-21-commandes-typst-refonte, REQ-012), one written before carries one."""
        from domains import unfold
        for kind in unfold.DOMAIN_KINDS:
            try:
                if rid in unfold.read_base(project.current(), kind)["domains"]:
                    return True
            except Exception:  # broad: a base that cannot be read shows no card, and the export names it
                continue
        return False

    def refresh_unfold(self):
        """The card filled for the domain open, and every pill's state read: nothing for a domain written by hand; for an unfolded check, unfold.status -- a check gone or a domain that cannot be compared said in the head, never raised."""
        self.unfold_states, self.unfold_status = {}, None
        domain = getattr(self, "domain", None)
        unfolded = domain is not None and domain.state != "unreadable" and (domain.gen is not None or self._in_unfold_base(domain.id))
        self.unfold_card.setVisible(unfolded)
        if not unfolded:
            return
        try:
            with project.using(project.current()):
                self.unfold_status = unfold.status(project.current(), domain.id)
        except (unfold.UnfoldError, validation.ValidationError, OSError) as exc:
            self.unfold_head.setText(html.escape(str(exc)))
            self.unfold_list.clear()
            self.unfold_selection()
            return
        st = self.unfold_status
        self.unfold_states = {line.id: line.state for line in st.lines}
        head = html.escape(self.t("fm_unfold_head", id=domain.id))
        # the red alert of the domain's head (spec 2026-10-21-commandes-typst-refonte, REQ-012, UI-004): what data/domain-state.json says and the report prints in red at the domain's head, in the window too
        alert = self.t("fm_unfold_gone") if not st.unfolded else self.t("fm_unfold_no_match") if not st.matches else None
        if alert is not None:
            head += f' — <span style="color: {theme.colour("danger")}">{html.escape(alert)}</span>'
        self.unfold_head.setText(head)
        self.unfold_list.clear()
        for line in st.lines:
            if line.state == "in_sync":
                continue
            item = QTreeWidgetItem([line.id, self.t(f"fm_unfold_state_{line.state}")])
            item.setData(0, Qt.ItemDataRole.UserRole, line.id)
            self.unfold_list.addTopLevelItem(item)
        self.unfold_none.setVisible(self.unfold_list.topLevelItemCount() == 0)
        self.unfold_list.setVisible(self.unfold_list.topLevelItemCount() > 0)
        self.unfold_selection()

    def unfold_line_of(self, command):
        """The id of the line a command of the domain is (`var:N_t_d`, `verify:v-6`), as unfold.status names it."""
        if command is None or command.is_text:
            return None
        name = command.options.get("id") if command.kind == "verify" else command.key
        return f"{command.kind}:{name}" if name else None

    def item_states(self):
        """{index of an item of the domain: its line's state} where it is not in step -- what the stripe of its row says (REQ-015, ARCH-RISK-018); {} for a domain that is no unfolded check."""
        states = getattr(self, "unfold_states", {}) or {}
        if not states or self.domain is None:
            return {}
        out = {}
        for i, c in enumerate(self.domain.commands):
            state = states.get(self.unfold_line_of(c))
            if state in formula_state.UNFOLD_STATES:
                out[i] = state
        return out

    def unfold_chosen(self):
        item = self.unfold_list.currentItem()
        return None if item is None else item.data(0, Qt.ItemDataRole.UserRole)

    def unfold_selection(self):
        """The actions the line chosen allows: «Importer» a line changed in the file, «Reprendre» an engineer's own value, «Réinsérer» a line taken out, a choice in a conflict; «Tout importer» while a line is changed in the file, «Régénérer» while the form no longer matches."""
        chosen = self.unfold_chosen()
        state = self.unfold_states.get(chosen)
        st = self.unfold_status
        enabled = {"import": state == "local", "take_back": state == "own", "reinsert": state == "missing", "mine": state == "conflict", "theirs": state == "conflict",
                   "import_all": any(s == "local" for s in self.unfold_states.values()),
                   "regenerate": st is not None and st.unfolded and not st.matches}
        for key, button in self.unfold_buttons.items():
            button.setEnabled(enabled[key])

    # --- writing: each one of woodcore_gui.WRITERS ---------------------------------------------------

    def _unfold_do(self, action, done_key, **values):
        domain = self.domain
        if domain is None:
            return False
        here = project.current()
        try:
            with project.using(here):
                result = action(here, domain.id)
        except (unfold.UnfoldError, validation.ValidationError, OSError) as exc:
            return self.fail(str(exc))
        conflicts = (result or {}).get("conflicts") if isinstance(result, dict) else None
        if conflicts:
            notices_ui.tell(self.t("fm_unfold_conflicts", lines=", ".join(conflicts)), notifications.WARNING, key="fm_unfold_conflicts", source="formula_tab")
        else:
            self.app.set_status(self.t(done_key, id=domain.id, **values))
        self.reload(keep=domain.id)
        return True

    def write_unfold_import(self):
        line = self.unfold_chosen()
        return line is not None and self._unfold_do(lambda here, rid: unfold.import_lines(here, rid, [line]), "fm_unfold_done_import", line=line)

    def write_unfold_import_all(self):
        return self._unfold_do(lambda here, rid: unfold.import_lines(here, rid, None), "fm_unfold_done_import_all")

    def write_unfold_take_back(self):
        line = self.unfold_chosen()
        return line is not None and self._unfold_do(lambda here, rid: unfold.take_back(here, rid, line), "fm_unfold_done_take_back", line=line)

    def write_unfold_reinsert(self):
        line = self.unfold_chosen()
        return line is not None and self._unfold_do(lambda here, rid: unfold.reinsert(here, rid, line), "fm_unfold_done_reinsert", line=line)

    def write_unfold_choice(self, choice):
        line = self.unfold_chosen()
        return line is not None and self._unfold_do(lambda here, rid: unfold.import_lines(here, rid, [line], {line: choice}), "fm_unfold_done_import", line=line)

    def write_unfold_regenerate(self):
        return self._unfold_do(lambda here, rid: unfold.regenerate(here, rid), "fm_unfold_done_regenerate")
