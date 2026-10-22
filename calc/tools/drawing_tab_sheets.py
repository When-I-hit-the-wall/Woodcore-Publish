"""DrawingTab's export sheets and PDF bundles, the list of the positions, the «Commande Typst» entry, the history and the size of the entry selected -- a mixin of methods moved verbatim out of calc/tools/drawing_tab.py (issue #30). DrawingTab names it among its bases.
"""

import copy
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QFileDialog, QHBoxLayout, QInputDialog, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMessageBox, QPushButton,
    QScrollArea, QSlider, QSplitter, QStackedWidget, QToolButton, QVBoxLayout, QWidget,
)
import busy  # a long operation behind the loading card (busy.py)
import cards  # the properties in cards, after the website (cards.py)
import grouped_list
import project  # where the project this tab works on is (calc/project.py)
import sheets  # the export sheets, Plans/<id>.typ (calc/sheets.py, v0.114)
import stylefactors  # an entry's own size factors, shown as an overridden b/h is (stylefactors.py, v0.99)
from domains import figure_style  # which of the three factors an entry may state (figure_style.py)
import sheet_editor  # the export sheets' editor (v0.114)
import bundle_view  # an export document's pages and its fields, its folder chosen (v0.117)
import notifications  # every error, warning and information, gathered in one place (calc/notifications.py, v0.117)
import notices_ui  # what was a message box is a notice since v0.117 (notices_ui.tell)
from drawing_tab_panes import CurrentStack, KINDS, KIND_VIEW, LIST_MIN_HEIGHT, MODULE_WHEN, NEW_ROW, VIEW_BOXES, VIEW_KIND, plain_label, DrawingPanesMixin  # split out of this module (issue #30): every name it had is still importable from it
from drawing_tab_documents import Blank, _Background, _export_layers, _run_layer_export, document_text, DrawingDocumentsMixin  # split out of this module (issue #30): every name it had is still importable from it


# How many steps «Annuler» can go back.
from canvas_editor import HISTORY  # «Annuler» and «Rétablir», once for every tab with a canvas (spec 2026-10-19-base-saine-nettoyage, ARCH-001)


class DrawingSheetsMixin:
    """Methods of drawing_tab.DrawingTab, moved verbatim (issue #30): the class names this mixin among its bases."""

    def sheet_error_text(self, exc):
        """A refusal of calc/sheets.py in the window's language, by its code -- the sheet editor's own sentences (sheet_editor.WHY)."""
        key = sheet_editor.WHY.get(getattr(exc, "code", None))
        if key is None:
            return self.w("plan_sheet_err_other", error=exc)
        return self.t(key).format_map(Blank(getattr(exc, "values", {}) or {}))

    def ask_rewrite(self, question):
        """The sheet editor's question before it rewrites an object written by hand -- a message box, replaced in a test."""
        return QMessageBox.question(self, "Woodcore", question) == QMessageBox.StandardButton.Yes

    def reload_sheets(self, select=None):
        try:
            ids = sheets.list_sheets(project.current(), kind=self.SHEET_KIND)
        except OSError:
            ids = []
        try:
            bundles = sheets.list_bundles(project.current(), kind=self.SHEET_KIND)
        except (sheets.SheetError, OSError):      # Plans/bundles.json written by hand and unreadable: the sheets are listed all the same, the file is left to the engineer
            bundles = []
        self.filling = True
        self.sheet_list.blockSignals(True)
        try:
            self.sheet_list.set_sheets(ids, bundles, select=select)
        finally:
            self.sheet_list.blockSignals(False)
            self.filling = False

    def new_sheet(self):
        """«Nouveau» under the export sheets: an A3 landscape sheet, Plans/B01.typ (calc/sheets.py), listed and opened."""
        if getattr(self.app, "read_only", False):
            self.app.refuse_read_only()
            return None
        try:
            sid = sheets.new_sheet(project.current(), format="A3", landscape=True, kind=self.SHEET_KIND).stem
        except (sheets.SheetError, OSError) as exc:
            notices_ui.tell(self.sheet_error_text(exc), notifications.CRITICAL, exc=exc, source="drawing_tab")
            return None
        if not self.leave_plan():
            self.reload_sheets()
            return sid
        self.reload_sheets(select=sid)
        self.open_sheet(sid)
        self.app.set_status(self.w("plan_sheet_created", id=sid))
        return sid

    def delete_sheet(self):
        """«Supprimer» under the export sheets: the sheet chosen moved into Plans/archives, never deleted, after a question."""
        sid = self.sheet_list.current_id() or self.sheet_id
        if not sid or getattr(self.app, "read_only", False):
            return False
        if QMessageBox.question(self, "Woodcore", self.w("plan_sheet_delete_ask", id=sid)) != QMessageBox.StandardButton.Yes:
            return False
        if sid == self.sheet_id:
            self.sheet_editor.stop()
            self.sheet_editor.close_sheet()
        try:
            sheets.archive(project.current(), sid)
        except (sheets.SheetError, OSError) as exc:
            notices_ui.tell(self.sheet_error_text(exc), notifications.CRITICAL, exc=exc, source="drawing_tab")
            return False
        self.sheet_id = None
        self.reload_sheets()
        self.show_kind("plan")
        self.show_plan_view()
        self.app.set_status(self.w("plan_sheet_deleted", id=sid))
        return True

    def open_sheet(self, sid):
        """Export sheet `sid` in the middle, compiled with its frames, and its options on the right (sheet_editor.py), the file watched while it is shown."""
        self.sheet_id = sid
        self.show_kind("sheet")
        self.sheet_editor.set_project(project.current())
        self.sheet_editor.open(sid)
        self.sheet_editor.start()
        self.sheet_list.blockSignals(True)
        self.sheet_list.select(sid)
        self.sheet_list.blockSignals(False)

    def bundle_row(self, layout, words):
        """The buttons under the export sheets that act on a bundle: «Nouveau PDF groupé», «Exporter le PDF groupé» and, on the position plans' tab, «Créer une liste des positions». Their words are the sheet editor's (sheet_editor.bundle_words). One under the other (v0.116, WP-K): three long labels side by side made the left pane as wide as the three together, which left the splitter's handles no room to move (tests/test_panes.py)."""
        row = QVBoxLayout()
        row.setSpacing(2)
        made = {}
        spec = [("new", words["se_bundle_new"], None, self.sheet_list.new_folder), ("export", words["se_bundle_export"], words["se_bundle_export_usage"], self.export_bundle)]
        if self.SHEET_KIND == "position":
            spec.append(("list", words["se_create_position_list"], words["se_create_position_list_usage"], self.create_position_list))
        for key, text, tip, slot in spec:
            button = QPushButton(text)
            if tip:
                button.setToolTip(tip.replace("{name}", "…"))
            button.clicked.connect(lambda _checked=False, slot=slot: slot())
            row.addWidget(button)
            made[key] = button
        layout.addLayout(row)
        return made

    def bundle_text(self, key, **values):
        """A word of the bundles in the window's language (sheet_editor.words)."""
        return sheet_editor.words(self.app.lang, key, **values)

    def new_bundle(self, name):
        """A new PDF bundle `name`, empty, of the tab's kind -- a folder of the export list the sheets are dragged into."""
        try:
            sheets.create_bundle(project.current(), name, kind=self.SHEET_KIND)
        except (sheets.SheetError, OSError) as exc:
            notices_ui.tell(self.sheet_error_text(exc), notifications.CRITICAL, exc=exc, source="drawing_tab")
            return False
        self.reload_sheets(select=self.sheet_id if self.view_kind == "sheet" else None)
        self.app.set_status(self.bundle_text("se_bundle_created", name=name))
        return True

    def rename_bundle(self, old, new):
        try:
            sheets.rename_bundle(project.current(), old, new)
        except (sheets.SheetError, OSError) as exc:
            notices_ui.tell(self.sheet_error_text(exc), notifications.CRITICAL, exc=exc, source="drawing_tab")
            return False
        self.reload_sheets(select=self.sheet_id if self.view_kind == "sheet" else None)
        return True

    def delete_bundle(self, name):
        """A PDF bundle taken away, after a question: its sheets stay, its PDF goes to Plans/archives."""
        if QMessageBox.question(self, "Woodcore", self.bundle_text("se_bundle_delete_ask", name=name)) != QMessageBox.StandardButton.Yes:
            return False
        try:
            sheets.delete_bundle(project.current(), name)
        except (sheets.SheetError, OSError) as exc:
            notices_ui.tell(self.sheet_error_text(exc), notifications.CRITICAL, exc=exc, source="drawing_tab")
            return False
        self.reload_sheets(select=self.sheet_id if self.view_kind == "sheet" else None)
        self.app.set_status(self.bundle_text("se_bundle_deleted", name=name))
        return True

    def on_sheets_moved(self, moves, target, before):
        """Sheets dragged in the export list (sheet_list.SheetList.sheetsMoved): into a bundle -- at the place dropped, a sheet dragged from another bundle leaving it --, within a bundle to put its pages in another order, or out of every bundle to the root."""
        here = project.current()
        ids = [sid for sid, _src in moves]
        try:
            for sid, source in moves:
                if source and source != target:
                    sheets.remove_from_bundle(here, source, [sid])
            if target:
                current = next((b for b in sheets.list_bundles(here) if b["name"] == target), None)
                kept = [s for s in (current["sheets"] if current else []) if s not in ids]
                index = kept.index(before) if before in kept else None
                sheets.add_to_bundle(here, target, ids, index)
        except (sheets.SheetError, OSError) as exc:
            notices_ui.tell(self.sheet_error_text(exc), notifications.CRITICAL, exc=exc, source="drawing_tab")
            self.reload_sheets(select=self.sheet_id if self.view_kind == "sheet" else None)
            return False
        self.reload_sheets(select=self.sheet_id if self.view_kind == "sheet" else None)
        return True

    def open_bundle(self, name):
        """An export document chosen (its folder): every page of its sheets in the centre, prepared in a task, and its fields on the right -- each its own or its first plan's (bundle_view, REQ-016)."""
        if not self.leave_plan():
            return
        here = project.current()
        try:
            entry = sheets.bundle(here, name)
            fields = sheets.bundle_fields(here, entry)
        except (sheets.SheetError, OSError) as exc:
            notices_ui.tell(self.sheet_error_text(exc), notifications.CRITICAL, exc=exc, source="drawing_tab")
            return
        self.bundle_name = entry["name"]
        self.show_kind("bundle")
        self.bundle_card.load(fields)
        key = (entry["name"], tuple(entry["sheets"]))
        if not entry["sheets"]:
            self.bundle_pages.say(self.t("bv_empty"))
            return
        if self.bundle_pages.shown != key:
            self.bundle_pages.say(self.t("bv_loading"))
        sheet_ids = list(entry["sheets"])
        self.tasks.run(self.t("activity_bundle"), lambda: bundle_view.pages_pdf(here, sheet_ids),
                       done=lambda data, key=key: self.bundle_pages.show_pdf(data, key),
                       failed=lambda exc: self.bundle_pages.say(self.t("bv_failed", error=exc)), key="bundle-pages")

    def on_bundle_field(self, field, value):
        """A field of the export document written: its name renames its folder, its id names its PDF, an empty field gives the first plan's back."""
        name = getattr(self, "bundle_name", None)
        if not name:
            return
        if getattr(self.app, "read_only", False):
            self.app.refuse_read_only()
            return
        here = project.current()
        try:
            if field == "name":
                self.rename_bundle(name, value)
                name = value if any(b["name"] == value for b in sheets.list_bundles(here)) else name
            else:
                sheets.set_bundle_field(here, name, field, value)
        except (sheets.SheetError, OSError) as exc:
            notices_ui.tell(self.sheet_error_text(exc), notifications.CRITICAL, exc=exc, source="drawing_tab")
        self.reload_sheets(select=None)
        self.sheet_list.blockSignals(True)
        self.sheet_list.select_folder(name)
        self.bundle_name = name
        self.sheet_list.blockSignals(False)
        try:
            self.bundle_card.load(sheets.bundle_fields(here, sheets.bundle(here, name)))
        except (sheets.SheetError, OSError):
            pass

    def export_bundle(self):
        """«Exporter le PDF groupé»: every sheet of the bundle chosen compiled, then Plans/<name>.pdf written, their pages in the list's order (sheets.export_bundle). A bundle is chosen by clicking it or one of its sheets."""
        name = self.sheet_list.chosen_bundle()
        if not name:
            self.app.set_status(self.bundle_text("se_bundle_choose"))
            return False
        here = project.current()
        try:
            count = len(sheets.bundle(here, name)["sheets"])
            if self.view_kind == "sheet":
                self.sheet_editor.stop()
            ok, message = busy.run_in_thread(self.app, self.bundle_text("se_bundle_export"), lambda: sheets.export_bundle(here, name))
        except (sheets.SheetError, OSError) as exc:
            notices_ui.tell(self.sheet_error_text(exc), notifications.CRITICAL, exc=exc, source="drawing_tab")
            return False
        finally:
            if self.view_kind == "sheet":
                self.sheet_editor.start()
        if not ok:
            notices_ui.tell(message, notifications.CRITICAL, source="drawing_tab")
            return False
        self.app.set_status(self.bundle_text("se_bundle_exported", file=f"{name}.pdf", count=count))
        return True

    def create_position_list(self):
        """«Créer une liste des positions»: an A4 portrait sheet holding the list of the positions alone -- the project's, every position (spec 2026-10-21-commandes-typst-refonte, Q-015) --, listed and opened."""
        here = project.current()
        try:
            sid = sheets.new_position_list_sheet(here).stem
        except (sheets.SheetError, OSError) as exc:
            notices_ui.tell(self.sheet_error_text(exc), notifications.CRITICAL, exc=exc, source="drawing_tab")
            return None
        if not self.leave_plan():
            self.reload_sheets()
            return sid
        self.reload_sheets(select=sid)
        self.open_sheet(sid)
        self.app.set_status(self.bundle_text("se_position_list_made", id=sid))
        return sid

    def open_builder(self):
        """The builder in the middle and its options on the right, on the project's export and the plan open."""
        self.show_kind("command")
        self.list.blockSignals(True)
        self.list.select(self.current_id if self.current_id is not None else NEW_ROW)
        self.list.blockSignals(False)
        mode = self.app.current_document() if hasattr(self.app, "current_document") else None
        self.builder.set_project(project.current(), mode)
        self.builder.set_plans(self.builder_records())
        if self.current_id:
            self.builder.set_plan(self.current_id)

    def replace_source(self, state):
        """The source replaced by `state` -- a step of «Annuler» or «Rétablir». An undo helper and never a writer: it must not be in woodcore_gui.WRITERS."""
        background_before = copy.deepcopy(self.source.get("background")), copy.deepcopy(self.source.get("sheet"))
        self.source.clear()
        self.source.update(state)
        self.canvas.selection = None
        if (self.source.get("background"), self.source.get("sheet")) != background_before:
            self.canvas.load_background()
        self.canvas.invalidate()
        self.fill()
        self.on_changed()
        self.on_selection()

    def build_entry_style(self):
        """The card of the selected entry's own factors, one per factor it may state: at 100 % while it follows the plan, and in orange with «Reprendre» beside it once it states one -- an overridden b/h's own form (v0.75, stylefactors.py).

        A card inside the selection's card, as a static model's selection sets a support or a load (v0.95), and built anew with the panel: it belongs to the entry selected, not to the plan.
        """
        entry, collection = self.selected_entry()
        card = cards.card(self.w(f"{self.STYLE_PREFIX}_style_own"))
        v = QVBoxLayout(card)
        v.addWidget(self.note(self.w(f"{self.STYLE_PREFIX}_style_own_note")))
        form = cards.form()
        self.entry_style = stylefactors.EntryRows(
            form, self.t, self.STYLE_PREFIX, self.set_entry_style, self.take_back_entry_style,
            pressed=self.on_slider_pressed, released=self.on_slider_released)
        v.addLayout(form)
        self.entry_style.fill(entry, figure_style.allowed(self.STYLE_KIND, collection))
        return card

    def show_entry_style(self):
        """The rows filled from the entry again, without rebuilding the panel: the orange and «Reprendre» appear while the slider is still held, where a rebuild would delete the very slider under the pointer."""
        entry, collection = self.selected_entry()
        if self.entry_style is not None and entry is not None:
            self.entry_style.fill(entry, figure_style.allowed(self.STYLE_KIND, collection))

    def set_entry_style(self, key, factor):
        """A factor the entry selected states over the plan's three. One step of «Annuler» per drag, like the plan's own sliders (on_slider_pressed), and it stays written over at 100 %: the b/h rule of v0.75 -- typing the very value the plan holds is still writing it over -- so «Reprendre» is the one way back."""
        entry, _collection = self.selected_entry()
        if entry is None:
            return
        self.edit(lambda: entry.setdefault("style", {}).__setitem__(key, round(factor, 2)))
        self.show_entry_style()

    def take_back_entry_style(self, key):
        """«Reprendre»: that factor follows the plan's own again. The `style` goes with its last factor, so an entry that states none is written exactly as it was before v0.99 and its drawing does not move."""
        entry, _collection = self.selected_entry()
        if entry is None or key not in figure_style.stated(entry):
            return

        def apply():
            entry.get("style", {}).pop(key, None)
            if not entry.get("style"):
                entry.pop("style", None)
        self.edit(apply)
        self.show_entry_style()
