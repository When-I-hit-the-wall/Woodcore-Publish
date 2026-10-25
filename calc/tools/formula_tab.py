"""Woodcore's «Domaines» tab (`tab_formula`, group Référence): the engineer's own calculations, each a domain written in a file of its own, `Domains/<id>.typ`, of `#var`, `#eq`, `#verify` and his Typst between them -- rebuilt by issue #113 (spec docs/requirements/completed/2026-10-24-onglet-domaines-formulaire-code.md) on the prototype «Domaines de calcul» v2 the engineer validated on 24.10.2026; the text with a pill for each command of v0.117 to v0.122 (issue #40, D-01 to D-05) is gone.

**Three modes on the same file** (UI-001, D-1, D-2), chosen in the top bar, the file staying the one source -- each writes it and reads it back (REQ-012):

* **Formulaire** -- a row a line of the file (calc/tools/formula_form.py): its symbol, its value or its calculation typed with the symbols, its result, its clause; the + between two rows and the line at the foot, inferred as it is typed; the × of a row and «Annuler»; the grip, one row or a group (Ctrl+click) dragged, refused where a line would stand above what it is computed from;
* **Code** -- the file itself, coloured, the numbers of its lines red or orange at a fault or a warning, the result of each line at its right; the command of the cursor recognised at once (calc/tools/formula_code.py); a buffer that does not read is not written;
* **Affichage** -- the file compiled as the report prints it, its lines set one by one and the domain's options ticked (calc/tools/formula_display.py, the view of the snow and the wind).

**On the left** the domains of the tab with their state, then the groups of the specialised tabs, folded, «Archives» last; «Domaine» and «Dupliquer» (calc/tools/formula_tab_domains.py). **In the centre** the line of the name and the ID, the file, the legend of the hovers, then the mode. **On the right** the modules of the common pane (calc/tools/formula_modules.py): État du domaine, Arguments de la ligne, Résultats, Variables du domaine, the excerpts of the norm pinned.

Everything a domain computes is calc/domains/'s -- `formula_domain.compute` and its neighbours `formula_rows`, `formula_state`, `formula_infer`, `formula_args`, `formula_defaults`, `formula_links`, `formula_undo` --, Qt-free (ARCH-001): this tab shows, edits and calls them; every method that writes is one of tab_guard.WRITERS, refused in a project opened read-only (ARCH-013).
"""

import source_editor  # Ctrl+S bound the one way (source_editor.save_shortcut)
import html
import re

from PySide6.QtCore import QStringListModel, Qt
from PySide6.QtWidgets import (QApplication, QCompleter, QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QSplitter, QStackedWidget,
                               QVBoxLayout, QWidget)

import project
import units
import validation
from domains import formula_args, formula_defaults, formula_domain as fd, formula_infer, formula_links, formula_rows, formula_state, formula_undo

import autosave
import cards
import display_view
import grouped_list
import norm_bubble
import notifications
import notices_ui
import source_archive
import theme
from domain_file_display import DomainFileDisplay
from formula_code import CodeView
from formula_display import FormulaSource
from formula_form import FormView
from formula_tab_domains import FormulaDomainsMixin  # split out of this module (issue #30)
from formula_tab_unfold import FormulaUnfoldMixin  # an unfolded check's card, the states of its lines (spec 2026-10-15, UI-002)
from formula_tab_words import REFUSALS, STRINGS, say, say_fix  # split out of this module (issue #113): `formula_tab.STRINGS` is still what woodcore_gui_words merges
import formula_modules

_WORD = re.compile(r"[A-Za-z_][A-Za-z0-9_]*(?:\([^()]*\)?)?$")


class FormulaTab(FormulaUnfoldMixin, FormulaDomainsMixin, source_editor.SourceEditorTab, display_view.DisplayTab, QWidget):
    """See the module's docstring."""

    VIEWS = ("form", "code", "display")
    KEY = "tab_formula"
    GRAPH_KIND = "formula"      # «formula:<id>» of the graph of dependencies: what «Ouvrir l'onglet» of the «Variables» tab opens here (REQ-018)
    REFUSALS = REFUSALS

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.t = app.t
        self.domains = []
        self.domain = None
        self.current_id = None
        self.results, self.state, self.deps, self.lines = [], None, {}, []
        self.chosen_item = None
        self.code_domain = None     # the domain the buffer of «Code» reads as, its file not yet written where it does not read
        self.code_line = 1
        self.id_typed = False
        self.dirty = False
        self.view = "form"
        self.undo = formula_undo.Undo()
        self._candidates = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.addWidget(self.build_left())
        self.splitter.addWidget(self.build_centre())
        self.splitter.addWidget(self.build_right())
        self.display = DomainFileDisplay(self, self.KEY, parent=self, source=FormulaSource)
        self.panes = display_view.ViewPanes(self.splitter, self.display, 1, 2)
        for index, stretch in enumerate((2, 5, 3)):
            self.splitter.setStretchFactor(index, stretch)
        self.pane.setMinimumWidth(300)
        layout.addWidget(self.splitter, 1)
        source_editor.save_shortcut(self)   # Ctrl+S
        self.bubbles = norm_bubble.BubbleController(self.t, lambda: self.app.lang, self, is_pinned=self.is_pinned)
        self.bubbles.pinned.connect(self.pin_excerpt)
        self.bubbles.unpinned.connect(self.unpin_excerpt)
        self.bubbles.opened.connect(self.open_excerpt)
        self.pane.removed.connect(lambda _mid: self.bubbles.refresh_marks())
        self.reload()
        self.restore(app.views.get(self.KEY))

    # --- building ---------------------------------------------------------------------------------

    def build_left(self):
        """The domains, by the one list every tab's left pane is (grouped_list.GroupedList): folders, «Archives», the order dropped; «Domaine» and «Dupliquer» under it (UI-002)."""
        box = QWidget()
        v = QVBoxLayout(box)
        v.setContentsMargins(0, 0, 0, 0)
        title = QLabel(f"<b>{html.escape(self.t('fm_domains'))}</b>")
        self.list = grouped_list.GroupedList(STRINGS.get(self.app.lang, STRINGS["fr"]), lang=self.app.lang)
        self.list.attach_order(self.KEY, self.app.list_store, groups=True)
        self.list.setIconSize(self.app.mark_size)
        self.list.roots_first = True
        v.addWidget(grouped_list.title_row(title, self.list))
        self.list.itemClicked.connect(self.on_tree_clicked)
        self.list.foldersChanged.connect(self.on_folders_changed)
        self.list.reordered.connect(self.fill_tree)
        self.backend = fd.ArchiveBackend(project.current, self.app.list_store, self.KEY)
        self.archive = source_archive.Actions(self, lambda: project.current().formulas_dir, self.app.set_status,
                                              lambda select: self.reload(keep=select or ""), self.forget_current, backend=self.backend)
        self.archive.connect()
        v.addWidget(self.list, 1)
        self.empty = cards.note(self.t("fm_empty"))
        v.addWidget(self.empty)
        buttons = QHBoxLayout()
        self.domain_button = QPushButton(self.t("fm_cmd_domain"))
        self.domain_button.setToolTip(self.t("fm_cmd_domain_tip"))
        self.domain_button.clicked.connect(self.new_domain)
        buttons.addWidget(self.domain_button)
        self.duplicate_button = QPushButton(self.t("fm_duplicate"))
        self.duplicate_button.clicked.connect(self.duplicate_domain)
        buttons.addWidget(self.duplicate_button)
        v.addLayout(buttons)
        return box

    def build_centre(self):
        """The line of the name and the ID, the file and the legend of the hovers (UI-003), the card of an unfolded check, the message «Annuler» offers, then the mode."""
        box = QWidget()
        v = QVBoxLayout(box)
        v.setContentsMargins(0, 0, 0, 0)
        head = QHBoxLayout()
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText(self.t("fm_name_placeholder"))
        self.name_edit.setToolTip(self.t("fm_name_tip"))
        font = self.name_edit.font()
        font.setPointSizeF(font.pointSizeF() * 1.25)
        font.setBold(True)
        self.name_edit.setFont(font)
        self.name_edit.installEventFilter(self)
        self.name_edit.returnPressed.connect(self.name_done)
        self.name_edit.textEdited.connect(self.name_typed)
        head.addWidget(self.name_edit, 3)
        head.addWidget(QLabel(self.t("fm_id")))
        self.id_edit = QLineEdit()
        self.id_edit.setToolTip(self.t("fm_id_tip"))
        self.id_edit.textEdited.connect(self.id_typed_now)
        self.id_edit.editingFinished.connect(self.id_done)
        head.addWidget(self.id_edit, 1)
        v.addLayout(head)
        line = QHBoxLayout()
        self.file_label = QLabel("")
        self.file_label.setStyleSheet("color: %s;" % theme.colour("muted"))
        self.file_label.setFont(self.app.mono_font)
        self.file_label.setToolTip(self.t("fm_file"))
        self.file_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        line.addWidget(self.file_label)
        line.addStretch(1)
        self.legend = QLabel(self.legend_html())
        self.legend.setTextFormat(Qt.TextFormat.RichText)
        line.addWidget(self.legend)
        v.addLayout(line)
        self.state_note = cards.note("")
        self.state_note.setVisible(False)
        v.addWidget(self.state_note)
        v.addWidget(self.build_unfold_card())
        self.undo_bar = QFrame()
        self.undo_bar.setObjectName("undoBar")
        self.undo_bar.setStyleSheet("#undoBar { background: %s; border-radius: 4px; }" % theme.colour("accent-soft"))
        bar = QHBoxLayout(self.undo_bar)
        bar.setContentsMargins(8, 2, 8, 2)
        self.undo_text = QLabel("")
        bar.addWidget(self.undo_text, 1)
        self.undo_button = QPushButton(self.t("fm_undo"))
        self.undo_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.undo_button.clicked.connect(self.write_undo)
        bar.addWidget(self.undo_button)
        self.undo_bar.setVisible(False)
        v.addWidget(self.undo_bar)
        self.work = QStackedWidget()
        self.form = FormView(self)
        self.work.addWidget(self.form)
        self.code = CodeView(self)
        self.code.editor.margins = self.code_margin
        self.code.cursorLine.connect(self.code_cursor)
        self.code.editor.hovered.connect(self.code_hover)
        self.code.paused.connect(self.write_code)
        self.work.addWidget(self.code)
        v.addWidget(self.work, 1)
        self.centre_note = cards.note(self.t("fm_no_domain"))
        v.addWidget(self.centre_note)
        return box

    def legend_html(self):
        """The legend of the linked hovers (UI-003, UI-018): the line, what it uses, what uses it -- the colours of theme.json."""
        swatch = '<span style="background:%s; border:1px solid %s">&nbsp;&nbsp;&nbsp;</span> %s'
        return (html.escape(self.t("fm_legend")) + " &nbsp;" + "&nbsp;&nbsp;".join(swatch % (theme.colour(ground), theme.colour(line), html.escape(self.t(word))) for ground, line, word in
                (("lit", "warning", "fm_legend_self"), ("link-uses", "link-uses-line", "fm_legend_uses"), ("link-used", "link-used-line", "fm_legend_used"))))

    def build_right(self):
        self.pane = formula_modules.build(self, getattr(self.app, "layout_store", None))
        return self.pane

    # --- the three modes (UI-001, ARCH-004) -----------------------------------------------------------

    def set_view(self, key, enter=True):
        """`form` and `code` show the work page -- the form or the buffer --, `display` the page compiled (display_view.DisplayTab)."""
        if key not in self.VIEWS or not hasattr(self, "panes"):
            return
        if self.view == "code" and key != "code":
            self.code.flush()
        if key == "display":
            display_view.DisplayTab.set_view(self, key, enter)
            return
        self.view = key
        self.work.setCurrentIndex(1 if key == "code" else 0)
        self.panes.show(False, False)
        if key == "code" and self.domain is not None:
            self.code_domain = None
            self.code.set_text(self.domain.text or fd.file_text(self.domain))
            self.code.editor.refresh_margins()
        self.refresh_modules()

    def display_entries(self):
        """«Affichage»: the domain as a section prints it, `#include "/Domains/<id>.typ"` (issue #15, D-01) -- its page compiled, its lines set (UI-021)."""
        if self.domain is None or self.current_id is None:
            return []
        from formula_display import failure_text
        faults = [self.say(m) for m in self.state.errors] if self.state is not None else []
        note = failure_text(self.t, faults, "") if self.domain.state == "unreadable" else ""
        return [display_view.Entry("file", "#include", call=fd.include_call(self.domain), note_text=note)]

    # --- computed, and shown -----------------------------------------------------------------------

    def recompute(self, rebuild=False):
        """The domain open computed again, its state read, and everything shown again: the rows in place (a new row structure rebuilt), the modules, the margins of the code."""
        domain = self.domain
        if domain is None:
            return
        here = project.current()
        if domain.state == "unreadable":
            self.results, self.deps, self.lines = [], {}, []
        else:
            self.results = self.compute(domain)
            self.deps = formula_links.dependencies(domain, self.results)
            self.lines = formula_rows.item_lines(domain)
        self.state = formula_state.state(domain, self.results, self.lines, here=here, candidates=self.candidates(),
                                         tab_domains=self.domains, unfold_states=self.item_states())
        self.form.show_domain(domain, self.results, rebuild=rebuild)
        self.form.set_states(self.state, self.say, self.results)
        self.refresh_modules()
        self.code.editor.refresh_margins()

    def candidates(self):
        """The variables a link may take (formula_links.linkable), read once a domain is open."""
        if self._candidates is None:
            try:
                self._candidates = formula_links.linkable(project.current(), self.domain)
            except (OSError, ValueError) as exc:
                self.app.set_status(str(exc))
                self._candidates = []
        return [c for c in self._candidates if self.domain is None or c.get("calc") != self.domain.id]

    def refresh_modules(self):
        self.pane.refresh()
        st = self.state
        if st is not None:
            errors, infos = len(st.errors), len(st.warnings)
            summary = self.t("fm_s_err", n=errors) if errors else self.t("fm_s_ok")
            if infos:
                summary += " · " + self.t("fm_s_info", n=infos)
            self.pane.summary("state", html.escape(summary))
        self.pane.summary("variables", str(sum(1 for c in (self.domain.commands if self.domain else ()) if c.kind == "var")))
        if hasattr(self, "bubbles"):
            self.bubbles.refresh_marks()

    def say(self, message):
        """A message of the state in the window's language, «Ligne 13 de Domains/panne-p2.typ : …» (REQ-005, REQ-007)."""
        here = project.current()
        rel = here.from_root(self.domain.path).lstrip("/") if self.domain is not None and self.domain.path is not None else ""
        return say(self.t, message, rel)

    def say_fix(self, fix):
        origin = self.origin_text(("export", fix.get("calc"), fix.get("instance")) if fix.get("instance") else ("domain", fix.get("calc")), None) if fix.get("kind") == "link" else ""
        return say_fix(self.t, fix, origin.lstrip("↗ "))

    def symbol_table(self, upto):
        return formula_infer.symbol_table(self.domain, upto, self.results) if self.domain is not None else formula_infer.Table([])

    def origin_text(self, origin, command):
        """«↗ Neige · SL», «↗ Poutre P1»: where a linked variable comes from, in the window's words (REQ-010)."""
        if origin is None and command is not None:
            found = fd.reference(command)
            origin = ("export", found[0], found[1]) if found and found[1] is not None else ("domain", found[0]) if found else None
        if origin is None:
            return ""
        if origin[0] == "export":
            word = self.t("fm_group_" + origin[1]) if ("fm_group_" + origin[1]) in STRINGS.get(self.app.lang, STRINGS["fr"]) else origin[1]
            return self.t("fm_origin_export", kind=word, instance=origin[2])
        other = next((d for d in self.domains if d.id == origin[1]), None)
        return self.t("fm_origin_domain", domain=(other.name if other is not None else origin[1]))

    def plain_line(self, command, result):
        """A command in a line of text, as its small block says it: symbol = value (D-16)."""
        if command.kind == "verify":
            return (command.formula + ("  ✔" if result is not None and result.holds else "  ✘"))
        value = units.shown(result.value, result.unit) if result is not None and not result.error and result.value is not None else "?"
        return f"{command.symbol or command.key} = {value}"

    # --- the norm's bubbles (REQ-014) ------------------------------------------------------------------

    def excerpt_for(self, norm, section):
        from norms import excerpts
        return excerpts.for_citation(norm, section, self.app.lang)

    def attach_bubble(self, mark, excerpt):
        self.bubbles.attach(mark, excerpt.norm, (excerpt.id,))

    def is_pinned(self, norm, ids):
        from tab_host import excerpt_module_id
        return excerpt_module_id(norm, tuple(ids)) in getattr(self.pane, "modules", {})

    def pin_excerpt(self, norm, ids):
        """A bubble clicked: its excerpt pinned under the modules (issue #96), once (norm_bubble.pin_excerpts)."""
        module = norm_bubble.pin_excerpts(self.pane, norm, ids, self.app.lang, self.t, lambda items: " + ".join(f"{e.edition} {e.ref}" for e in items), after="variables")
        self.bubbles.refresh_marks()
        return module

    def unpin_excerpt(self, norm, ids):
        from tab_host import excerpt_module_id
        self.pane.remove(excerpt_module_id(norm, tuple(ids)))
        self.bubbles.refresh_marks()

    def open_excerpt(self, norm, eid):
        """Ctrl+click: the edition in Woodcore's reader at the clause."""
        import norm_reader
        from norms import excerpts
        e = excerpts.excerpt(norm, eid, self.app.lang)
        shown = norm_reader.reader(self.app).show_excerpt(e)
        if not shown:
            self.app.set_status(self.t("ct_reader_missing", file=e.file))
        return shown

    # --- the linked hovers (UI-018) ------------------------------------------------------------------

    def light(self, item):
        """A line hovered -- a row, a line of the code, a result, an element of «Affichage» (UI-018) --: it in yellow, what it is computed from in blue, what is computed from it in green, wherever the tab shows them; nothing else."""
        entry = self.deps.get(item, {}) if item is not None else {}
        uses, used = entry.get("uses", ()), entry.get("used", ())
        self.form.light(item, uses, used)
        grounds = {"self": "lit", "uses": "link-uses", "used": "link-used"}
        for target, widget, kept, _owner in getattr(self, "lit_targets", []):
            lit = "self" if target == item else "uses" if target in uses else "used" if target in used else None
            widget.setStyleSheet(kept + ((" background: %s;" % theme.colour(grounds[lit])) if lit else ""))
            widget.lit = lit
        lines = {}
        for target, kind in [(item, "self")] + [(u, "uses") for u in uses] + [(u, "used") for u in used]:
            if target is not None and target < len(self.lines):
                lines[self.lines[target]] = kind
        self.code.editor.light_lines({line: theme.colour(grounds[kind]) for line, kind in lines.items()})

    def forget_lit(self, owner):
        """The widgets `owner` (a module, the list of «Affichage») registered, forgotten before it deletes them: a deleted widget is never painted."""
        self.lit_targets = [t for t in getattr(self, "lit_targets", []) if t[3] != owner]

    def hover(self, widget, item, owner):
        """`widget` lights the line `item` while the pointer is on it, and is lit with it (UI-018); `owner` forgets it before deleting it (`forget_lit`)."""
        from PySide6.QtCore import QEvent, QObject
        tab = self

        class _Hover(QObject):
            def eventFilter(self, obj, event):
                if event.type() == QEvent.Type.Enter:
                    tab.light(item)
                elif event.type() == QEvent.Type.Leave:
                    tab.light(None)
                return False
        widget.installEventFilter(_Hover(widget))
        widget.lit = None
        targets = getattr(self, "lit_targets", [])
        targets.append((item, widget, widget.styleSheet(), owner))
        self.lit_targets = targets

    def code_hover(self, line):
        """The pointer on line `line` of «Code»: the command that begins there lit with what it uses and what uses it."""
        item = None
        if line and self.domain is not None:
            item = next((i for i, first in enumerate(self.lines) if first == line and not self.domain.commands[i].is_text), None)
        self.light(item)

    # --- the row chosen, the arguments, the cursor of «Code» -----------------------------------------

    def row_chosen(self, item):
        self.chosen_item = item
        self.pane.refresh("args")

    def code_cursor(self, line):
        self.code_line = line
        self.pane.refresh("args")

    def args_context(self):
        """What the module «Arguments de la ligne» shows (UI-012): (item, every argument?, the command, its result, the symbols' table, «file:line») -- or a sentence where it has none to show."""
        t = self.t
        if self.domain is None:
            return t("fm_a_none_form")
        here = project.current()
        rel = here.from_root(self.domain.path).lstrip("/") if self.domain.path is not None else self.domain.id
        if self.view == "code":
            domain = self.code_domain or self.domain
            at = formula_args.command_at(domain, self.code_line, self.code.text())
            if at is None:
                return t("fm_a_none_code")
            if not at.reads:
                return t("fm_a_broken", line=at.first)
            if at.kind == "text":
                return t("fm_a_text", line=self.code_line)
            results = self.results if domain is self.domain else self.compute(domain)
            return (at.index, True, domain.commands[at.index], results[at.index] if at.index < len(results) else None,
                    formula_infer.symbol_table(domain, at.index, results), f"{rel}:{at.first}")
        item = self.chosen_item
        if item is None or item >= len(self.domain.commands) or self.domain.commands[item].is_text:
            return t("fm_a_none_form")
        return (item, False, self.domain.commands[item], self.results[item] if item < len(self.results) else None, self.symbol_table(item),
                f"{rel}:{self.lines[item] if item < len(self.lines) else '?'}")

    def code_margin(self, line):
        """The margins of «Code» for line `line` (UI-019): the colour of its number, its result or its fault at its right."""
        domain = self.code_domain or self.domain
        if domain is None:
            return None, ""
        if domain.state == "unreadable":
            from domains import formula_errors
            fault = formula_errors.read_fault(self.code.text())
            if fault is not None and fault["line"] == line:
                return "danger", self.t("fm_e_read_" + fault["code"], line=fault["line"], col=fault["col"])
            return None, ""
        if domain is not self.domain:
            return None, ""
        for i, first in enumerate(self.lines):
            if first != line or self.domain.commands[i].is_text:
                continue
            r = self.results[i] if i < len(self.results) else None
            st = self.state.rows.get(i) if self.state is not None else None
            token = formula_state.COLOURS.get(st) if st in ("error", "warning") else None
            if r is None:
                return token, ""
            if r.error:
                own = self.state.of_item(i) if self.state is not None else []
                return ("danger" if r.blocked_by is None else "muted"), ("✘ " + self.say(own[0]) if own else "✘")
            c = self.domain.commands[i]
            if c.kind == "verify":
                (lv, lu), (rv, ru) = r.value
                return token, f"{'✔' if r.holds else '✘'} {units.shown(lv, lu)} {r.op} {units.shown(rv, ru)}"
            return token, "= " + units.shown(r.value, r.unit)
        return None, ""

    # --- a click writes a name into the calculation being typed (UI-011) --------------------------------

    def insert_variable(self, key):
        """A variable or a result clicked on the right: its symbol written where the cursor of the calculation being typed is -- in «Code» its key, in the buffer -- the cursor left there; said where there is none."""
        if self.view == "code":
            cursor = self.code.editor.textCursor()
            cursor.insertText(key)
            self.code.editor.setFocus()
            return True
        target = self.form.target
        item = target[0] if target else None
        table = self.symbol_table(item if isinstance(item, int) else None)
        if not self.form.insert(table.typed(key)):
            self.app.set_status(self.t("fm_insert_none"))
            return False
        return True

    def attach_completion(self, field, item):
        """The names a calculation may take, offered as they are typed (REQ-013, a): the domain's above the line by symbol or key -- the symbol written --, then the project's, whose choice writes the link above the line."""
        completer = QCompleter(field)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        completer.setWidget(field)
        model = QStringListModel(completer)
        completer.setModel(model)
        entries = {}

        def fill(prefix):
            entries.clear()
            names = []
            table = self.symbol_table(item if isinstance(item, int) else None)
            here_word, out_word = self.t("fm_ac_here"), self.t("fm_ac_out")
            for key, typed in table.pairs:
                text = f"{typed}  ·  {here_word}" if typed == key else f"{typed}  ({key})  ·  {here_word}"
                entries[text] = (typed, None)
                names.append(text)
            taken = {c.key for c in self.domain.commands if c.defines} if self.domain is not None else set()
            for cand in self.candidates():
                if cand["key"] in taken or prefix.casefold() not in (cand["key"] + " " + (cand.get("symbol") or "")).casefold():
                    continue
                value = units.shown(cand["value"], cand.get("unit", "")) if isinstance(cand.get("value"), (int, float)) else ""
                text = f"{cand.get('symbol') or cand['key']}  ·  {self.group_title(cand)}  ·  {value}  ·  {out_word}"
                entries[text] = (cand["key"], cand)
                names.append(text)
                if len(names) > 200:
                    break
            model.setStringList(names)

        def typed(_text):
            before = field.text()[:field.cursorPosition()]
            found = _WORD.search(before)
            if found is None or not found.group():
                completer.popup().hide()
                return
            prefix = found.group()
            fill(prefix)
            completer.setCompletionPrefix(prefix)
            if completer.completionCount():
                completer.complete()

        def chosen(text):
            insert, cand = entries.get(text, (None, None))
            if insert is None:
                return
            before = field.text()[:field.cursorPosition()]
            found = _WORD.search(before)
            start = found.start() if found else len(before)
            rest = field.text()[field.cursorPosition():]
            field.setText(field.text()[:start] + insert + rest)
            field.setCursorPosition(start + len(insert))
            if cand is not None:
                row = self.form.row_of(item) if isinstance(item, int) else None
                self.write_links([cand], row.index if row is not None else None)

        field.textEdited.connect(typed)
        completer.activated.connect(chosen)
        field.completer_ = completer
        field.complete_fill = fill
        field.complete_choose = chosen

    # --- the state's messages lead to their line (UI-015) ----------------------------------------------

    def go_to(self, message):
        if self.view == "code":
            line = message.line or (self.lines[message.item] if message.item is not None and message.item < len(self.lines) else None)
            if line:
                self.code.editor.select_line(line)
            return
        if message.item is not None:
            self.form.flash(message.item)

    def apply_fix(self, message):
        """The fix of a message (REQ-013, c): the link it offers written above its line; the domain's options opened in «Affichage»."""
        fix = message.fix or {}
        if fix.get("kind") == "link":
            row = self.form.row_of(message.item)
            self.write_links([fix], row.index if row is not None else None)
        elif fix.get("kind") == "options":
            self.set_view("display")
            if hasattr(self.app, "view_changed"):
                self.app.view_changed(self)

    def copy_values(self):
        """«Copier les valeurs» (UI-016): each result, symbol = value, one a line."""
        lines = []
        for c, r in zip(self.domain.commands if self.domain else (), self.results):
            if c.kind == "eq" and not r.error:
                lines.append(f"{c.symbol or c.key} = {units.shown(r.value, r.unit)}")
            elif c.kind == "verify" and not r.error:
                (lv, lu), (rv, ru) = r.value
                lines.append(f"{c.formula}: {units.shown(lv, lu)} {r.op} {units.shown(rv, ru)} {'✔' if r.holds else '✘'}")
        text = "\n".join(lines)
        copy = getattr(self.app, "copy", None)
        if callable(copy):
            copy(text)
        else:
            QApplication.clipboard().setText(text)
        self.app.set_status(self.t("fm_r_copied"))
        return text

    # --- «Lier une variable…» (UI-014) ----------------------------------------------------------------

    def open_link_dialog(self, row_index, run=True):
        """The window «Lier une variable…», its links written above the row `row_index` -- or the row chosen, or the first. `run` False builds it without waiting (the tests)."""
        from formula_link_dialog import LinkDialog
        if self.read_only_now():
            return None
        taken = {c.key for c in self.domain.commands if c.defines}
        dialog = LinkDialog(self.t, self.domain.name, self.candidates(), taken, self.group_title, self)
        self.link_dialog = dialog
        chosen_row = self.form.row_of(self.chosen_item) if self.chosen_item is not None else None
        target = row_index if row_index is not None else (chosen_row.index if chosen_row is not None else None)
        dialog.accepted.connect(lambda: self.write_links(dialog.chosen_result or [], target))
        if run:
            dialog.exec()
        return dialog

    def group_title(self, candidate):
        origin = ("export", candidate["calc"], candidate["instance"]) if candidate.get("instance") else ("domain", candidate["calc"])
        return self.origin_text(origin, None).lstrip("↗ ")

    # --- writing: each one of tab_guard.WRITERS ---------------------------------------------------------

    def read_only_now(self):
        return bool(getattr(self.app, "read_only", False)) or self.domain is None or self.domain.state == "unreadable"

    def fail(self, message):
        return autosave.refuse(self, self.t(self.KEY), message)

    def refusal(self, exc):
        """A refusal of the domain module in the window's language, by its code; its own sentence otherwise."""
        key = self.REFUSALS.get(getattr(exc, "code", ""))
        values = dict(getattr(exc, "values", {}) or {})
        if key == "fm_missing_field":
            values["field"] = self.t({"symbol": "fm_f_symbol", "formula": "fm_f_formula", "relation": "fm_f_relation"}.get(values.get("field"), "fm_f_text"))
        if key == "fm_key_taken":
            values.setdefault("name", values.get("key", ""))
        if "key" in values:
            values["var"] = values.pop("key")   # `key` is the window's own argument (MainWindow.t(key, …))
        if key == "fm_e_formula":
            values = {"text": str(exc)}
        try:
            return self.t(key, **values) if key else str(exc)
        except (KeyError, IndexError):
            return str(exc)

    def save_domain(self, items, record=None):
        """The domain written with `items` (formula_domain.save: the file, then the index), read back, computed and shown again -- the one road of every writer. `record` (name, values) keeps the step «Annuler» undoes (D-17). False where it was refused, said, nothing written."""
        domain = self.domain
        if domain is None or domain.state == "unreadable":
            return False
        before = domain.text
        previous = domain.commands
        structure = [(c.kind, c.key) for c in previous]
        domain.commands = list(items)
        try:
            saved = fd.save(project.current(), domain)
        except (fd.DomainError, ValueError, OSError) as exc:
            domain.commands = previous
            if getattr(exc, "code", "") == "changed_on_disk":
                return self.changed_on_disk(exc)
            return self.fail(self.refusal(exc))
        self.index_refused(saved)
        if record is not None and before is not None:
            self.undo.record(record[0], saved.path, before, saved.text, **record[1])
        elif record is None:
            self.undo.forget()
            self.show_undo(None)
        self.domain = saved
        self.current_id = saved.id
        self.id_typed = True
        self.dirty = False
        known = any(d.id == saved.id for d in self.domains)
        self.domains = [saved if d.id == saved.id else d for d in self.domains] if known else fd.list_domains(project.current())
        rebuild = [(c.kind, c.key) for c in saved.commands] != structure
        self.recompute(rebuild=rebuild)
        self.fill_tree()
        self.file_label.setText(project.current().rel(saved.path))
        self.update_display()
        return True

    def index_refused(self, saved):
        if saved is not None and saved.index_problem:
            notices_ui.tell(self.t("fm_index_refused", reason=saved.index_problem), notifications.WARNING, key="fm_index_refused", source="formula_tab")

    def changed_on_disk(self, exc):
        """The file changed on the disk since the tab read it: nothing written over it, said, and the domain read again as the file now is."""
        self.dirty = False
        notices_ui.tell(self.refusal(exc), notifications.WARNING, key="fm_changed_on_disk", source="formula_tab")
        self.reload()
        return False

    def save(self):
        """Ctrl+S: what «Code» holds and has not read yet, read and written; the form writes every change as it is made."""
        if self.view == "code":
            self.code.flush()
        return True

    def write_field(self, item, name, value):
        """A field of a row changed (UI-005, UI-006): written into its line -- a calculation typed with the symbols written with the keys (REQ-002), «Article» as `norm-section:` (REQ-008) --, the row updated in place."""
        if self.read_only_now() or item >= len(self.domain.commands):
            return False
        c = self.domain.commands[item]
        if name == "text":
            if value == c.raw:
                return True
            try:
                fd.check_text(value)
            except fd.DomainError as exc:
                return self.fail(self.refusal(exc))
            new = fd.replace(c, raw=value)
        else:
            try:
                new = formula_args.set_argument(c, name, value, self.symbol_table(item))
            except fd.DomainError as exc:
                return self.fail(self.refusal(exc))
            if fd.to_call(new) == fd.to_call(c):
                return True
        items = list(self.domain.commands)
        items[item] = new
        return self.save_domain(items)

    def write_new_line(self, inferred, row_index, line_widget=None):
        """A line typed and written (UI-008, UI-010): at the foot, or before the row its + was opened over; its key made from its symbol, its calculation written with the keys of the lines above it (D-11)."""
        if self.read_only_now():
            return False
        shown = formula_rows.rows(self.domain)
        at = shown[row_index].first if row_index is not None and row_index < len(shown) else len(self.domain.commands)
        taken = {c.key for c in self.domain.commands if c.defines}
        try:
            command = formula_infer.command_of(inferred, taken, self.symbol_table(at).pairs)
            if command.is_text:
                fd.check_text(command.raw)
        except fd.DomainError as exc:
            if line_widget is not None:
                line_widget.say(self.refusal(exc))
            return False
        items = list(self.domain.commands)
        items.insert(at, command)
        if not self.save_domain(items):
            return False
        if line_widget is not None:
            if line_widget.foot:
                self.form.foot.text.setFocus()
            else:
                self.form.close_insert(line_widget)
        self.form.choose(at)
        self.form.flash(at)
        self.app.set_status(self.t("fm_written_line", line=self.lines[at] if at < len(self.lines) else "?"))
        return True

    def write_delete_rows(self, row_indexes):
        """The × of a row (UI-007): the row deleted, its glued commands with it; the message offers «Annuler» (D-17); the lines that used it fail, said with their cause."""
        if self.read_only_now():
            return False
        shown = formula_rows.rows(self.domain)
        lines = [shown[r].line for r in row_indexes if r < len(shown)]
        items = formula_rows.delete(self.domain, row_indexes)
        if not self.save_domain(items, record=("delete", {"line": lines[0] if lines else "?"})):
            return False
        self.form.chosen = None
        self.show_undo(self.t("fm_deleted", line=lines[0] if lines else "?"))
        return True

    def write_undo(self):
        """«Annuler» (D-17, ARCH-015): the file of before the last deletion or gesture of several lines written back, byte for byte -- refused, said, where the file changed since."""
        try:
            path = self.undo.undo()
        except formula_undo.UndoError as exc:
            self.show_undo(None)
            if exc.code == "changed":
                self.app.set_status(self.t("fm_undo_changed", file=exc.values.get("file", "")))
            return False
        try:
            fd.export(project.current())
        except validation.ValidationError:
            pass   # another file of Domains/ unreadable: the export names it, the undo is done
        self.show_undo(None)
        self.domain = fd.read(path)
        self.domains = fd.list_domains(project.current())
        self.fill_tree()
        self.recompute(rebuild=True)
        self.update_display()
        self.app.set_status(self.t("fm_undone"))
        return True

    def show_undo(self, text):
        """The message that follows a deletion or a gesture of several lines, «Annuler» in it (UI-007); hidden with None."""
        self.undo_text.setText(text or "")
        self.undo_bar.setVisible(bool(text) and self.undo.step is not None)

    def write_move_rows(self, rows, target):
        """Rows dropped before the row `target` by their grip (UI-013): one, or the group, together in their order -- refused, the file untouched, where a line would stand above what it is computed from (REQ-003)."""
        if self.read_only_now():
            return False
        items, refusal = formula_rows.move(self.domain, self.results, rows, target)
        if refusal is not None:
            _code, user, used = refusal
            plain = lambda s: re.sub(r"_\(([^()]*)\)", r"_\1", s.replace('"', ""))   # noqa: E731 -- a symbol said in a sentence
            message = self.t("fm_move_refused", user=plain(user), used=plain(used))
            self.app.set_status(message)
            notices_ui.tell(message, notifications.WARNING, key="fm_move_refused", source="formula_tab")
            self.last_refusal = message
            return False
        if items is None:
            return True
        record = ("move", {"n": len(rows)}) if len(rows) > 1 else None
        if not self.save_domain(items, record=record):
            return False
        if len(rows) > 1:
            self.show_undo(self.t("fm_moved_n", n=len(rows)))
        self.app.set_status(self.t("fm_moved_n", n=len(rows)) if len(rows) > 1 else self.t("fm_moved"))
        return True

    def write_links(self, candidates, row_index):
        """Variables linked (REQ-013, UI-014): `#var(key, domain: …)` above the row `row_index` (the first where None), all in one write, which «Annuler» takes back (D-17); a circle of domains refused, nothing written."""
        if self.read_only_now() or not candidates:
            return False
        taken = {c.key for c in self.domain.commands if c.defines}
        commands = [formula_links.link_command(c) for c in candidates if c["key"] not in taken]
        if not commands:
            return False
        shown = formula_rows.rows(self.domain)
        at = shown[row_index].first if row_index is not None and row_index < len(shown) else (shown[0].first if shown else 0)
        items = list(self.domain.commands)
        items[at:at] = commands
        trial = fd.Domain(id=self.domain.id, name=self.domain.name, commands=items)
        circle = next((r.error for r in self.compute(trial) if r.code == "circle"), None)
        if circle:
            return self.fail(circle)
        if not self.save_domain(items, record=("link", {"n": len(commands)})):
            return False
        line = self.lines[at] if at < len(self.lines) else "?"
        if len(commands) == 1:
            said = self.t("fm_picked", var=commands[0].key, source=self.group_title(candidates[0]), line=line)
        else:
            said = self.t("fm_picked_n", n=len(commands), line=self.lines[at + len(commands)] if at + len(commands) < len(self.lines) else line)
        self.show_undo(said)
        self.app.set_status(said)
        return True

    def write_argument(self, item, name, value):
        """An argument set in the module «Arguments de la ligne» (UI-012): written into the line -- in «Code» by one edit of the buffer, the cursor and the scroll staying (ARCH-016), the buffer then read and written."""
        if self.read_only_now():
            return False
        if self.view == "code":
            domain = self.code_domain or self.domain
            if domain.state == "unreadable" or item >= len(domain.commands):
                return False
            try:
                new = formula_args.set_argument(domain.commands[item], name, value, formula_infer.symbol_table(domain, item))
            except fd.DomainError as exc:
                return self.fail(self.refusal(exc))
            first, last, text = formula_args.line_edit(domain, item, new)
            self.code.replace_lines(first, last, text)
            return self.write_code(self.code.text())
        return self.write_field(item, name, value)

    def write_code(self, text):
        """The buffer of «Code» read (ARCH-016): written to the disk only where it reads -- a fault leaves the file as it was, the state saying where, as Typst would (REQ-007, REQ-012)."""
        if self.domain is None or bool(getattr(self.app, "read_only", False)) or self.domain.path is None:
            return False
        old = self.domain.text.replace("\r\n", "\n") if self.domain.text else None
        if text == old:
            self.code_domain = None
            return True
        path = self.domain.path
        parsed = fd.parse_text(text, path)
        if parsed.state == "unreadable":
            self.code_domain = parsed
            self.app.set_status(self.t("fm_code_unread"))
            self.state = formula_state.state(parsed, [], [])
            self.refresh_modules()
            self.code.editor.refresh_margins()
            return False
        try:
            fd.check_unchanged(self.domain)
        except fd.DomainError as exc:
            return self.changed_on_disk(exc)
        newline = "\r\n" if self.domain.text and "\r\n" in self.domain.text else "\n"
        with open(path, "w", encoding="utf-8", newline="") as file:
            file.write(text.replace("\n", newline))
        try:
            fd.export(project.current())
        except validation.ValidationError as exc:
            notices_ui.tell(self.t("fm_index_refused", reason=str(exc)), notifications.WARNING, key="fm_index_refused", source="formula_tab")
        self.code_domain = None
        self.undo.forget()
        self.domain = fd.read(path)
        self.domains = [self.domain if d.id == self.domain.id else d for d in self.domains]
        self.recompute(rebuild=True)
        self.fill_tree()
        return True

    def write_domain_option(self, name, value):
        """An option of the domain ticked or not in «Affichage» (UI-021, REQ-004): written on its one `#calc-defaults(…, scope: "domain")` line, the page compiled again."""
        if self.read_only_now():
            return False
        try:
            items = formula_defaults.set_option(self.domain, name, value)
        except fd.DomainError as exc:
            return self.fail(self.refusal(exc))
        ok = self.save_domain(items)
        self.display.rebuild()
        self.display.refresh()
        return ok

    def write_domain_level(self, level):
        """The domain's level, auto, 1, 2 or 3 (`#domain(…, level:)`, UI-021)."""
        if self.read_only_now():
            return False
        try:
            text = formula_args.with_domain_level(self.domain, level)
            fd.check_unchanged(self.domain)
        except fd.DomainError as exc:
            return self.fail(self.refusal(exc))
        with open(self.domain.path, "w", encoding="utf-8", newline="") as file:
            file.write(text)
        self.domain = fd.read(self.domain.path)
        self.recompute()
        self.display.rebuild()
        self.display.refresh()
        return True

    def write_line_display(self, line_id, values):
        """A line's own level, or an argument of its display, set in «Affichage» (UI-021): written into the line -- its level given back to the domain by a second click (`level` None)."""
        if self.read_only_now():
            return False
        index = int(line_id.partition(":")[2])
        command = self.domain.commands[index]
        try:
            for name, value in values.items():
                command = formula_args.set_argument(command, name, "" if value is None else value)
        except fd.DomainError as exc:
            return self.fail(self.refusal(exc))
        items = list(self.domain.commands)
        items[index] = command
        ok = self.save_domain(items)
        self.display.rebuild()
        self.display.refresh()
        return ok

    def write_reset_line(self, index):
        """«Rétablir la ligne» (UI-021): every argument of the line's display taken out of it."""
        if self.read_only_now():
            return False
        import line_display
        c = self.domain.commands[index]
        names = set(line_display.display_args(c.kind))
        items = list(self.domain.commands)
        items[index] = fd.replace(c, options={k: v for k, v in c.options.items() if k not in names})
        ok = self.save_domain(items)
        self.display.rebuild()
        self.display.refresh()
        return ok

    def delete(self):
        """«Supprimer le domaine…»: a domain not yet written given up; one written into «Archives» (source_archive.Actions), never deleted."""
        if self.domain is not None and self.current_id is None:
            self.domain = None
            self.dirty = False
            self.show_domain()
            return True
        return self.archive.delete()

    def forget_current(self):
        self.domain = None
        self.current_id = None
        self.dirty = False
        self.reload()

    def confirm_leave(self):
        """Another domain, or another tab: what «Code» holds read and written where it reads (autosave.leave for a new domain not yet named)."""
        if self.view == "code":
            self.code.flush()
        if self.dirty and self.current_id is None and not autosave.leave(self.app, self, "leave"):
            return not self.dirty
        return True

    def update_list_marker(self):
        """The mark of unsaved work before the domain open, and the tab's own, as the editor tabs mark the object they edit."""
        for item, entry_id in self.list.rows():
            item.setIcon(0, self.app.dirty_mark(self.dirty and entry_id == self.current_id))
        update = getattr(self.app, "update_tab_marks", None)
        if update is not None:
            update()

    # --- the window's hooks -------------------------------------------------------------------------

    def on_shown(self):
        """The tab brought to the front: the domains read again -- a domain VS Code changed is shown as it is now; one that did not keeps its rows and the row chosen."""
        self._candidates = None
        if self.domain is not None and self.domain.path is not None and self.domain.path.is_file() and self.current_id is not None:
            try:
                fd.check_unchanged(self.domain)
            except fd.DomainError:
                self.reload()
                return
            self.domains = fd.list_domains(project.current())
            self.fill_tree()
            return
        self.reload()

    def on_mode(self, _mode):
        self.update_display()

    def lists_object(self, ident):
        """Whether the graph's node `formula:<ident>` is a domain of this tab (MainWindow.open_object, REQ-018)."""
        return any(d.id == ident for d in (self.domains or fd.list_domains(project.current())))

    def open_object(self, ident):
        found = next((d for d in self.domains if d.id == ident), None)
        if found is not None and (found.id == self.current_id or self.confirm_leave()):
            self.open_domain(found)

    def set_language(self, _lang=None):
        pass

    def view_state(self):
        return {"domain": self.current_id}

    def restore(self, state):
        if isinstance(state, dict) and state.get("domain"):
            found = next((d for d in self.domains if d.id == state["domain"]), None)
            if found is not None:
                self.open_domain(found)
