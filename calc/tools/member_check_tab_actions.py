"""MemberCheckTab's list of checks on the left, what is calculated and shown with its command, and its buttons -- new, duplicate, revert, delete, save, export -- a mixin of methods moved verbatim out of calc/tools/member_check_tab.py (issue #30). MemberCheckTab names it among its bases.
"""

import json
import re
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDoubleSpinBox, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton,
    QSplitter, QVBoxLayout, QWidget,
)
import build_reference as ref
import cards  # the form and what is read off it in cards, after the website (cards.py)
import autosave  # saving without a question, and what is never saved without the engineer (autosave.py, v0.117)
import grouped_list
import project  # where the project this tab works on is (calc/project.py)
import richtext  # the call coloured as the site's code, «Copié ✓» once copied (richtext.py)
import source_archive  # «Supprimer» archives (source_archive.py)
import structure_preview  # the lines every snippet starts with: the project's conf, the engine, the language
import validation
import engine
from domains import connector, member_check
import display_options  # the level -1 «Sélection manuelle» (issue #20)
from member_check_tab_words import STRINGS, _check_strings  # split out of this module (issue #30): every name it had is still importable from it


from source_editor import NEW_ROW, next_free_id  # the one constant of the draft's row (spec 2026-10-19-base-saine-nettoyage, ARCH-001)


ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.+-]*$")


class MemberCheckActionsMixin:
    """Methods of member_check_tab.MemberCheckTab, moved verbatim (issue #30): the class names this mixin among its bases."""

    def command_text(self):
        """Its domain, where a section prints it: `#include domain-file("check", id)` (spec 2026-10-21-commandes-typst-refonte, ARCH-008, UI-002) -- no path written by hand."""
        return ref.call_include_domain("check", self.draft()["id"])

    def open_in_formulas(self):
        """«Ouvrir dans Formules» (UI-003): the «Formules» tab brought forward on this check's domain -- written there at its first save (unfold.unfold_checks)."""
        import formula_tab
        tab = next((t for t in getattr(self.app, "tabs", ()) if isinstance(t, formula_tab.FormulaTab)), None)
        if tab is None or self.current_id is None:
            return False
        if not tab.confirm_leave():
            return False
        self.app.tab_widget.setCurrentWidget(tab)
        tab.reload(keep=self.current_id)
        tab.list.select(self.current_id)
        return True

    def refresh(self, preview=True):
        """The draft read: resolved against the positions, its warnings said, the results and the command written -- and the page asked for again (`preview`), which is nothing while the preview is closed."""
        source = self.draft()
        self.record, self.reason = None, ""
        warnings = []
        try:
            self.DOMAIN.check_source(source)
            self.record = self.resolve_draft(source)
            for note in self.record.get("warnings") or []:
                warnings.append(self.app.note_text(note))   # the record's own words, in the window's language: «ne peut pas être vérifiée — …»
            if not self.record.get("calculable", True):
                self.reason = self.t("mc_no_calc", reason=self.tl(self.record.get("reason") or ""))
        except (validation.ValidationError, ValueError, KeyError, TypeError) as exc:
            self.reason = self.t("mc_invalid", error=str(exc))
            warnings.append(self.reason)
        self.message.setText("<br>".join(richtext.prose_html(w) for w in warnings))
        self.message.setVisible(bool(warnings))
        self.fill_results()
        self.fill_command()
        self.update_list_marker()
        if preview:
            self.request_preview()

    def fill_command(self):
        """The «Affichage» view told what the check is now: its call, whether it is saved, why it cannot be computed -- and the page asked for again, which is nothing outside «Affichage»."""
        self.display.set_project(project.current(), self.app.current_document())
        self.display.set_entries(self.display_entries())

    def preview_source(self):
        """The Typst the pane compiles: the lines every snippet starts with -- the project's `conf`, the engine, the document and its language -- and the draft's own call, its values written into it, so nothing needs saving first. None where there is nothing to compile."""
        if self.record is None or not self.record.get("calculable"):
            return None      # nothing to print: the pane says why instead (request_preview)
        if not member_check.is_unfolded(self.record):
            return None
        # the page of the draft is its domain as it would be written (spec 2026-10-15, UI-003), its literals unchecked -- a draft is in no export yet
        from domains import unfold
        body = unfold.preview_body(self.record, self.app.lang if self.app.lang in ("de", "fr", "en") else "de")
        if not body:
            return None
        here = project.current()
        return "\n".join(structure_preview.header(here, self.app.current_document())) + "\n\n" + body + "\n"

    def request_preview(self):
        """Asks for the page of the draft -- compiled a moment from now, the newest request winning, in «Affichage» alone (display_view.DisplayView.refresh); Typst's own message stays in the pane's banner. Nothing is asked before the tab has been shown."""
        if not self.live or self.view != "display":
            return
        try:
            if not self.display.active:
                self.display.activate(True)     # shown in «Affichage»: the page is asked for from now on
            else:
                self.display.refresh()
        except Exception as exc:  # broad: a draft the engine cannot write out is said, never raised through a slot
            self.message.setText(richtext.prose_html(self.t("mc_invalid", error=str(exc))))
            self.message.setVisible(True)

    def on_shown(self):
        """The tab brought to the front: the positions are read again -- one added or changed in «Positions» is offered at once --, and the page is compiled for the first time."""
        self.live = True
        self._positions_key = None             # the positions are read again
        dirty = self.dirty
        self.source = self.draft()
        self.reload_list(self.current_id)      # a check made, moved or archived in another tab of the same folder
        self.fill_form()
        self.dirty = dirty
        self.refresh()

    def stop(self):
        self.pane.stop()

    def save(self):
        source = self.draft()
        cid = source["id"]
        if not ID_PATTERN.match(cid or ""):
            return self.fail(self.t("mc_taken", id=cid))
        taken = {t.lower() for t in self._taken()} - ({self.current_id.lower()} if self.current_id else set())
        if cid.lower() in taken:
            return self.fail(self.t("mc_taken", id=cid))
        if self.current_id and self.current_id != cid:
            if not autosave.ask_rename(self, self.t("mc_rename_title"), self.t("mc_rename", old=self.current_id, new=cid)):
                return False
        try:
            self.DOMAIN.check_source(source)
        except (validation.ValidationError, ValueError) as exc:
            return self.fail(self.t("mc_invalid", error=str(exc)))
        folder = self.sources_dir()
        folder.mkdir(parents=True, exist_ok=True)
        if self.current_id and self.current_id != cid:
            (folder / ("%s.json" % self.current_id)).unlink(missing_ok=True)
        if hasattr(self.DOMAIN, "write_source"):
            # the domain's one writer of a source, checked and moved into place (spec 2026-10-15, ARCH-RISK-206): «Importer» in the «Formules» tab writes through it too
            self.DOMAIN.write_source(project.current(), source)
        else:
            engine.write_json(folder / ("%s.json" % cid), source)
        self.source = source
        self.current_id = cid
        self.dirty = False
        self.export(self.t("mc_saved", id=cid))
        self.reload_list(select=cid)
        self.fill_command()
        return True
