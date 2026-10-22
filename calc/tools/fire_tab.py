"""Woodcore's «Plan de protection incendie» tab (docs/domain/position-plans.md §3.3sexies, docs/ui/window.md §10quater; ported from origin/Gian's v0.112 in v0.115): where a fire-protection plan is drawn -- the surfaces, walls, doors and escape routes of a floor, by hand over the architect's plan -- and saved as its source, fire/<id>.json (calc/domains/fire.py).

**It is the position plan's tab a second time** (the engineer's requirement: «extrêmement similaire»), built on the same base, drawing_tab.DrawingTab: the documents the project imported -- **the same documents** the «Plan de positions» tab lists, imported once --, each shown every page of it (document_view.py) with a tick under each page that makes a fire plan of it here, as it makes a position plan there; a crop and a calibration drawn on a page; a page turned and its layers switched -- **turning a page turns the plans of both kinds drawn on it** (plan_pages.rotate_page); unticking archives, never deletes; the plans in folders; the export sheets; the «Commande Typst» builder; a plan saved when it is left; a history of 200 steps. The position plans' crops are drawn muted on the pages for reference, as this tab's are in theirs.

**A fire plan has two kinds of frame** (domains/fire.py, schema 2.0): it FOLLOWS a position plan -- whose background, sheet, crop and scale it then reads afresh, a crop of its own allowed over it, taken back with «Reprendre» -- or it carries a frame of its own, on a page of an imported document (or, for a plan of Gian's 1.0, on a file named directly, which is read as it is and written as 2.0 only when it is saved). Ticking a page that carries exactly one position plan makes a plan that follows it; any other page, a plan with a frame of its own on that page. Following is chosen in the right pane too. A calibration drawn on the page of a plan that follows is refused with a word: the scale is the position plan's.

Everything is drawn by hand; the program delimits nothing (the engineer's decision of 05.10.2026). The plan draws what the top of the AEAI's sample legend lists: surfaces of three kinds, walls of a fire resistance, doors, the escape routes' length, the emergency exits and the escape routes' width, and a legend box placed on the plan that lists them. The bar's combos choose what the next entry is drawn as; an entry already drawn is changed in the selection's card, for every entry selected at once and in one step of the history. How large and how opaque an entry is drawn is the position plan's own logic (stylefactors.py, figure_style.py): orange, with «Reprendre», once stated.

The tab lives in its own module, which woodcore_gui.py lists in its TABS and whose STRINGS (`fp_`, and the warnings of calc/domains/fire.py, `warn_fire_`) it merges into its own.
"""

import copy
import json
from pathlib import Path

from PySide6.QtCore import QItemSelectionModel, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (
    QButtonGroup, QCheckBox, QComboBox, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPlainTextEdit, QPushButton,
    QSizePolicy, QSpinBox, QTabWidget, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)

import cards  # the properties in cards, after the website (cards.py)
import engine
import identity
import project  # where the project this tab works on is (calc/project.py)
import stylefactors  # the entries' own size factors, shown as an overridden b/h is (stylefactors.py)
import theme  # the colours this tab states itself (theme.py)
import validation
import drawing_tab  # what every tab of plans drawn on imported documents shares (v0.115)
from drawing_tab import DrawingTab, number_text, plain_label
import plan_command_builder  # the «Commande Typst» entry, for #show-fire-plan (v0.115)
import notifications  # every error, warning and information, gathered in one place (calc/notifications.py, v0.117)
import notices_ui  # what was a message box is a notice since v0.117 (notices_ui.tell)
from domains import figure_style  # which of the factors each kind of entry may state
from domains import fire
from domains import plan as model
from domains import plan_pages  # the plans of both kinds on one page (v0.115)
from fire_canvas import FireCanvas
from flowbar import FlowLayout, FlowWidget, tool_group
from i18n import strings  # the German name of a fire resistance or of a kind of surface, in the window's language
from norms import vkf  # the fire resistances, the escape routes and the doors of the VKF sheet of symbols, and their colours
from fire_tab_words import STRINGS, _french_spaces  # split out of this module (issue #30): every name it had is still importable from it
from fire_tab_build import DEFAULT_DOOR_CLASS, DEFAULT_DOOR_KIND, DEFAULT_SURFACE_KIND, DEFAULT_WALL_CLASS, HINTS, NAMES, TOOLS, FireTabBuildMixin  # split out of this module (issue #30): every name it had is still importable from it
from fire_tab_form import OWN_FRAME_TOOLS, PANE_TOOLS, UNITS, FireTabFormMixin  # split out of this module (issue #30): every name it had is still importable from it
from fire_tab_selection import COLLECTION_ORDER, FireTabSelectionMixin  # split out of this module (issue #30): every name it had is still importable from it


# The lists under the plans, by the key of each one's name, and which of them holds what: the escape routes' three marks are one list.
LISTS = (("zones", "fp_zones"), ("walls", "fp_walls"), ("doors", "fp_doors"), ("escape", "fp_escape"))
LIST_OF = {"zones": "zones", "walls": "walls", "doors": "doors", "routes": "escape", "exits": "escape", "widths": "escape"}


def list_fire_plans(folder=None):
    """(id, source, folder) of every saved fire protection plan, in file-name order -- the source as it is read, nothing upgraded or written (DrawingTab.list_sources)."""
    return drawing_tab.list_sources(fire, folder or project.current().fire_dir)


class FireTab(FireTabSelectionMixin, FireTabFormMixin, FireTabBuildMixin, DrawingTab):
    """The fire protection plans (docs/domain/position-plans.md §3.3sexies, docs/ui/window.md §10quater): the documents, the saved plans, what the plan open holds, the export sheets and the command builder on the left; what is chosen there in the middle; its properties on the right -- the position plan tab's arrangement, from the same base (drawing_tab.DrawingTab, v0.115).

    Everything drawn or checked here is calc/domains/fire.py's and fire_svg.py's. Saving writes the source, fire/<id>.json, and exports the fire protection plans at once (`export`). Leaving a plan saves it (autosave); the draft survives a language switch or a reload all the same (view_state).
    """

    KIND = "fire"
    KEY = "tab_fire"
    GRAPH_KIND = "fire"   # issue #71
    STYLE_KIND = "fire"
    STYLE_PREFIX = "plan"
    ID_PREFIX = "B"
    # The base says the position plan's words; these are said of fire plans instead.
    WORD_MAP = {
        "plan_list": "fp_list",
        "plan_empty": "fp_empty",
        "plan_page_plan_created": "fp_page_plan_created",
        "plan_page_untick_ask": "fp_page_untick_ask",
        "plan_page_plans_removed": "fp_page_plans_removed",
        "plan_doc_no_plan_on_page": "fp_doc_no_plan_on_page",
        "plan_doc_hint": "fp_doc_hint",
        "plan_doc_imported": "fp_doc_imported",
        "plan_unsaved": "fp_unsaved",
        "plan_export_failed": "fp_export_failed",
        "dv_in_plans": "fp_dv_in_plans",
        "dv_in_plans_use": "fp_dv_in_plans_use",
        "dv_crop_use": "fp_dv_crop_use",
    }
    domain = fire
    # the documents of the fire protection plans: those this tab imported (v0.116)
    DOC_OWNER = "fire"
    # the export sheets of the fire-protection plans (calc/sheets.py, v0.116): its own list, its own bundles, no list of positions
    SHEET_KIND = "fire"

    # -- what DrawingTab asks of a fire protection plan --

    def init_state(self):
        self.plan_frames = fire.plan_frames(project.current().plans_dir)   # every position plan's frame, by id: what a plan may follow
        self.syncing = False  # set while the canvas and the lists are put in step, which would otherwise answer each other for ever
        self.label_typing = False  # a surface's name or an escape route's text being typed: the whole of it is one step of «Annuler», not one a letter
        self.own_widgets = []  # the controls of the plan's own frame, greyed while it follows a position plan's
        self.class_icons = {}  # a fire resistance's colour square, by the colour it is drawn in
        self.own_filling = False  # set while the opacity row is put in step with the selection, which would otherwise be taken for an edit
        self.export_notes = []  # what the last export said of this plan, shown under the plan beside what it says itself

    def list_strings(self):
        return STRINGS.get(self.app.lang, STRINGS["fr"])

    def sources_dir(self):
        return project.current().fire_dir

    def list_sources(self):
        return list_fire_plans()

    def entry_text(self, pid, source):
        """A plan as the left pane lists it: «B01 – Name – suit P01», its id, its name (else its description) and the position plan it follows, a part left out where it is empty."""
        source = source or {}
        followed = fire.follows(source)
        parts = [pid, source.get("name") or source.get("label") or "", self.t("fp_list_follows", plan=followed) if followed else ""]
        return " – ".join(part for part in parts if part)

    def blank_source(self, pid):
        return fire.new_source(pid)

    def complete_source(self, source, pid):
        """A source read from its file completed with what every plan has -- but never with a frame: a plan that follows a position plan must not be given a sheet of its own. Nothing is upgraded here: a 1.0 plan of Gian's is shown as it is read, and written as 2.0 only when it is saved."""
        source.setdefault("id", pid)
        source.setdefault("label", "")
        source.setdefault("zones", [])
        if fire.follows(source) is None:
            source.setdefault("sheet", dict(model.BLANK_SHEET))
        return source

    def sources_on(self, docid, page=None):
        """[(id, source)] of the fire protection plans on document `docid` -- on its page `page` where one is named: those drawn on it themselves, and those that follow a position plan that is (plan_pages.fire_plans_on)."""
        try:
            return [(fid, source) for fid, source, _frame in plan_pages.fire_plans_on(project.current(), docid, page)]
        except (OSError, ValueError):
            return []

    def has_drawing(self, source):
        return any(source.get(collection) for collection in fire.COLLECTIONS) or "legend" in source

    def source_for_page(self, pid, docid, page, doc, width, height):
        """A fire protection plan of page `page` of document `docid`: it FOLLOWS the page's position plan where the page carries exactly one (the engineer's decision of 06.10.2026), else it has a frame of its own on the page -- the page's size as its sheet, the document named in its background."""
        positions = plan_pages.position_plans_on(project.current(), docid, page)
        if len(positions) == 1:
            return fire.new_source(pid, positions[0][0])
        source = fire.new_source(pid)
        source["sheet"] = {"width": round(width, 2), "height": round(height, 2)}
        source["background"] = {"document": docid, "file": doc["file"], "page": page, "opacity": model.DEFAULT_OPACITY, "sha256": doc["sha256"]}
        return source

    def document_crops(self, docid):
        """The fire plans on document `docid`: the pages they are drawn on, and the crop each shows -- its own, or the position plan's it follows where it states none; one that shows the whole page framed by the page (v0.116), so that a click chooses it."""
        try:
            plans = plan_pages.fire_plans_on(project.current(), docid)
        except (OSError, ValueError):
            return [], {}
        pages, crops = set(), {}
        for fid, source, frame in plans:
            page = int((frame.get("background") or {}).get("page", 1))
            pages.add(page)
            crop = frame.get("crop")
            sheet = frame.get("sheet") or {}
            if crop:
                rect, whole = (crop["x"], crop["y"], crop["w"], crop["h"]), False
            elif sheet.get("width") and sheet.get("height"):
                rect, whole = (0.0, 0.0, float(sheet["width"]), float(sheet["height"])), True
            else:
                continue
            crops.setdefault(page, []).append({"plan": fid, "rect": rect, "label": self.entry_text(fid, source), "whole": whole})
        return sorted(pages), crops

    def uncropped_on(self, docid, page):
        """The fire plans on page `page` of document `docid` that show the whole page -- no crop of their own, nor one of the position plan they follow (v0.116)."""
        try:
            plans = plan_pages.fire_plans_on(project.current(), docid, page)
        except (OSError, ValueError):
            return []
        return [fid for fid, _source, frame in plans if not frame.get("crop")]

    def source_for_frame(self, pid, docid, page, doc, width, height):
        """A fire plan of a frame drawn on page `page` (v0.116): the first plan of the page as ticking would make it -- following the page's one position plan where there is one --, and a plan of a frame of its own on the page where the page carries fire plans already."""
        if self.sources_on(docid, page):
            source = fire.new_source(pid)
            source["sheet"] = {"width": round(width, 2), "height": round(height, 2)}
            source["background"] = {"document": docid, "file": doc["file"], "page": page, "opacity": model.DEFAULT_OPACITY, "sha256": doc["sha256"]}
            return source
        return self.source_for_page(pid, docid, page, doc, width, height)

    def other_crops(self, docid):
        """The position plans on document `docid`, for reference: muted, dotted and never hit in the document view."""
        try:
            plans = plan_pages.position_plans_on(project.current(), docid)
        except (OSError, ValueError):
            return [], {}
        pages, crops = set(), {}
        kind = self.t("fp_other_kind_position")
        for pid, source in plans:
            page = int((source.get("background") or {}).get("page", 1))
            pages.add(page)
            crop = source.get("crop")
            if crop:
                label = drawing_tab.plan_text(pid, source)
                crops.setdefault(page, []).append({"plan": pid, "rect": (crop["x"], crop["y"], crop["w"], crop["h"]), "label": label, "kind": kind})
        return sorted(pages), crops

    def current_page(self):
        """(document, page) the plan open is drawn on -- its own, or the one of the position plan it follows --, or None."""
        background = self.frame().get("background") or {}
        if background.get("document"):
            return background["document"], int(background.get("page", 1))
        return None

    def calibration_refused(self, pid):
        """A plan that follows a position plan takes that plan's scale: a calibration drawn on its page is refused, with a word saying where to calibrate."""
        try:
            source = json.loads((self.sources_dir() / f"{pid}.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        followed = fire.follows(source) if isinstance(source, dict) else None
        return self.t("fp_calibrate_follows", fire=pid, plan=followed) if followed else None

    def fire_records(self):
        """The plans of the export, data/fire.json's `plans` -- what the builder offers; none where nothing was exported."""
        try:
            return json.loads((project.current().data_dir / fire.EXPORT_FILE).read_text(encoding="utf-8")).get("plans", {})
        except (OSError, ValueError, AttributeError):
            return {}

    def builder_records(self):
        return self.fire_records()

    def make_builder(self):
        """The «Commande Typst» builder for `#show-fire-plan` (plan_command_builder's FireCommandOptions and fire_command_text)."""
        return plan_command_builder.CommandBuilder(lang=self.app.lang, mono_font=self.app.mono_font, copy=self.app.copy,
                                                   options_factory=plan_command_builder.FireCommandOptions, command_fn=plan_command_builder.fire_command_text,
                                                   cache_key=self.KEY)

    def build_entries(self, v):
        """What the plan open holds, one list per kind: the surfaces, the walls with their fire resistance, the doors, and the escape routes' three marks (their length, the emergency exits, their width) in one. Each is kept in step with the canvas's selection, both ways (on_rows, sync_rows)."""
        v.addWidget(self.heading(self.t("fp_elements")))
        self.zone_tree = self.entry_tree(("fp_col_id", "fp_col_kind", "fp_col_name", "fp_col_area"))
        self.wall_tree = self.entry_tree(("fp_col_id", "fp_col_class", "fp_col_length"))
        self.door_tree = self.entry_tree(("fp_col_id", "fp_col_kind", "fp_col_class", "fp_col_width"))
        self.escape_tree = self.entry_tree(("fp_col_id", "fp_col_symbol", "fp_col_value", "fp_col_text"))
        self.tree_by_list = {"zones": self.zone_tree, "walls": self.wall_tree, "doors": self.door_tree, "escape": self.escape_tree}
        self.tree_list = list(self.tree_by_list.values())
        self.trees = {collection: self.tree_by_list[LIST_OF[collection]] for collection in fire.COLLECTIONS}
        self.entry_tabs = QTabWidget()
        for name, key in LISTS:
            self.entry_tabs.addTab(self.tree_by_list[name], self.t(key))
        v.addWidget(self.entry_tabs, 3)
        v.addSpacing(6)

    def build_drawing_center(self):
        return self.build_fire_center()

    def build_drawing_properties(self):
        return self.build_fire_properties()

    def reset_drawing_state(self):
        self.export_notes = []

    def drawing_view_state(self):
        return {
            "wall_class": self.canvas.wall_class,
            "zone_kind": self.canvas.zone_kind,
            "door_kind": self.canvas.door_kind,
            "door_class": self.canvas.door_class,
        }

    def restore_drawing_after(self, state):
        # what the bar's combos choose survives a rebuild of the window, as the tool does; a door's class is None for a door without a fire resistance
        for combo, key in ((self.wall_combo, "wall_class"), (self.surface_combo, "zone_kind"), (self.door_kind_combo, "door_kind"), (self.door_class_combo, "door_class")):
            if key in state:
                index = combo.findData(state[key] or "" if key == "door_class" else state[key])
                if index >= 0:
                    combo.setCurrentIndex(index)

    def on_shown(self):
        """The tab brought to the front: a position plan may have been changed, turned or archived in its own tab since -- a plan that follows it shows what it now is."""
        frames = fire.plan_frames(project.current().plans_dir)
        if frames != self.plan_frames:
            self.plan_frames = frames
            self.refresh_follow_items()
            if not self.own_frame():
                self.refresh_frame(reload=True)
            self.fill()
        super().on_shown()

    # -- building --


    # -- the frame --


    # -- the source and the form --


    # -- tools --


    # -- what is selected, and the lists --


    # -- the size and the opacity of the selection, and where its text stands --


    # -- after every change --

    def on_changed(self):
        if not self.loading:
            self.dirty = True
        self.update_crop_text()
        self.update_widgets()
        self.update_legend_size()
        self.refresh_lists()
        self.update_area()
        self.refresh_own()
        self.refresh_messages()
        self.revert_button.setEnabled(self.dirty)
        self.update_list_marker()

    def refresh_messages(self):
        messages = []
        try:
            fire.check_source(self.source, f"{self.source.get('id') or '?'}.json")
        except validation.ValidationError as exc:
            messages.append(str(exc))
        background = self.frame().get("background")
        if background and not background.get("document"):
            path = model.background_path(project.current().root, background["file"])
            if path is None or not path.is_file():
                messages.append(self.t("plan_background_missing", file=background["file"]))
        problem = getattr(self.canvas, "background_problem", None)
        if problem is not None:
            messages.append(self.document_error_text(problem))
        warnings = [self.app.note_text(n) for n in fire.warnings(self.source, self.plan_frames)]
        messages += warnings
        messages += [text for text in (self.app.note_text(n) for n in self.export_notes) if text not in warnings]
        text = "\n".join(messages)
        if text != self.message.toPlainText():
            self.message.setPlainText(text)

    # -- saving --

    def save(self, quiet=False):
        """Writes fire/<id>.json -- the draft checked first by the very rules the reader applies, written as 2.0 whatever it was read as -- and exports the fire protection plans. True when saved. `quiet` is the autosave's: a refusal is said in the status line, and a rename -- which asks -- is not made."""
        fail = (lambda text: self.app.set_status(text) or False) if quiet else self.fail
        source = copy.deepcopy(self.source)
        # 2.1 where it holds a text (issue #43), its variables' last values refreshed (D-14); 2.0 otherwise, as before
        fire.figure_text.refresh_all(source, self.text_values())
        if not source.get("texts"):
            source.pop("texts", None)
        source["schema_version"] = fire.version_of(source)
        fid = source.get("id", "")
        if not fire.ID_PATTERN.match(fid):
            return fail(self.t("plan_id_invalid", id=fid))
        old = self.current_id
        renaming = old is not None and fid != old
        clash = any(t.lower() == fid.lower() for t in self.taken_ids()) and (old is None or fid.lower() != old.lower())
        if clash:
            return fail(self.t("fp_id_exists", id=fid))
        if renaming and (quiet or QMessageBox.question(self, "Woodcore", self.t("fp_rename", old=old, new=fid)) != QMessageBox.StandardButton.Yes):
            return False
        background = source.get("background")
        if background and not background.get("document"):
            path = model.background_path(project.current().root, background["file"])
            if path is not None and path.is_file():
                background["sha256"] = model.file_hash(path)
        target = self.sources_dir() / f"{fid}.json"
        try:
            fire.check_source(source, target.name)
        except validation.ValidationError as exc:
            return fail(str(exc))
        try:
            self.sources_dir().mkdir(parents=True, exist_ok=True)
            if renaming:
                (self.sources_dir() / f"{old}.json").unlink(missing_ok=True)
            engine.write_json(target, source)
        except OSError as exc:
            return fail(str(exc))
        if background and "sha256" in background and self.source.get("background"):
            self.source["background"]["sha256"] = background["sha256"]
        self.source["schema_version"] = source["schema_version"]
        self.current_id = fid
        self.dirty = False
        self.export(fid, self.t("fp_saved", id=fid), quiet=quiet)
        self.reload_list(select=fid)
        self.on_changed()
        self.dirty = False
        self.revert_button.setEnabled(False)
        self.update_list_marker()
        return True

    def export(self, pid, done_text, quiet=False):
        """The fire protection plans' part of the export, run here and now: data/fire.json and data/fire/, from every saved source (calc/domains/fire.py). A failure leaves data/ as it was and says why, the plan staying saved. What the export says of this plan is kept (`export_notes`) and shown under the plan."""
        self.finish_layer_export()   # a layer switched being exported in its thread: finished first (drawing_tab, v0.116)
        here = project.current()
        try:
            notes = fire.export(here.fire_dir, here.plans_dir, here.root, here.data_dir, values=self.text_values())
        except (validation.ValidationError, engine.EngineError, OSError) as exc:
            if quiet:
                self.app.set_status(self.t("fp_export_failed", id=pid, error=exc))
            else:
                notices_ui.tell(self.t("fp_export_failed", id=pid, error=exc), notifications.CRITICAL, exc=exc, key="fp_export_failed", args=dict(id=pid, error=exc), source="fire_tab")
            return False
        self.export_notes = [n for n in notes if pid and str(n).startswith(f"fire-protection plan {pid}:")]
        self.app.set_status(self.t("fp_saved_warnings", id=pid, n=len(self.export_notes)) if self.export_notes else done_text)
        self.builder.set_plans(self.fire_records())
        return True
