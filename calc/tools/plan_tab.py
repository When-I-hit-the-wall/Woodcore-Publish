"""Woodcore's «Plan de positions» tab (docs/domain/position-plans.md §3.3sexies, docs/ui/window.md §10quater): where a position plan is drawn -- the structure's STE symbols, their position numbers and the axes, over the architect's plan -- and saved; where the architect's documents are imported and cut into plans; where the export sheets are listed; and where the `#show-plan` command is built.

**The left pane, top to bottom** (v0.114): the **documents** imported into the project (calc/domains/plan_documents.py: a PDF, an image, an SVG, a DXF or DWG drawing, never copied), the **plans** in their folders, the **elements and axes** of the plan open, the **export sheets** (calc/sheets.py) and the **«Commande Typst»** entry (plan_command_builder.py). What is chosen there decides what the centre and the right pane show: a plan its drawing and its properties, a document every page of it (document_view.py) and its own card, a sheet its editor, the entry the builder and the page its command prints.

**A document is cut into plans on its pages, with no dialog**: ticking «Dans les plans» under a page makes a plan of it -- the next free id, the page's size as its sheet, the document named in its background -- saved and exported at once; unticking takes that page's plans away into the archives, asking first where something is drawn on them. A crop drawn on a page is that page's plan's crop, a calibration its scale, and turning a page turns what is drawn on it (plan.rotate_source), so the drawing stays on the architecture.

A plan is saved as its source, plans/<id>.json, and exported at once by calc/domains/plan.py, the module export_all.py runs: data/plans.json, the symbols' SVG, the legend and the background's page under data/plans/. **Leaving a plan saves it** -- choosing another entry, another tab, closing the window, a language switch: the engineer is asked only where the plan cannot be saved as it is.

A position appears on a plan by its number, a position of the project (calc/positions_store.py, Woodcore's own since v0.114). A tool whose letter the project has no position of **creates a blank one** at its first click -- the next free id of that letter on the plan's floor, its type and nothing else -- which the engineer completes in the Positions tab; a number the project no longer has is shown for what it is and offered back with «Ajouter aux positions».

The tab lives in its own module rather than in woodcore_gui.py, which lists it in its TABS and merges STRINGS below -- with document_view's `dv_` and plan_command_builder's `pcb_` -- into its own: the window's language, shortcuts and closing rules are woodcore_gui's, the tab's texts and behaviour are here. Since v0.115 what any tab of plans drawn on imported documents does -- the documents, the plans' list, the export sheets, the builder, the history, saving on leaving -- is drawing_tab.DrawingTab's, which this tab subclasses: what is left here is what a position plan is, said through the base's hooks, and its drawing.

«Taille des symboles» holds the plan's own three factors; since v0.99 the selection's card carries the factors the element or the axis chosen states **over** them, shown as an overridden b/h is (build_entry_style, calc/tools/stylefactors.py).
"""

import copy
import json
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QButtonGroup, QCheckBox, QComboBox, QDoubleSpinBox, QHBoxLayout, QInputDialog, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QMessageBox, QPlainTextEdit, QPushButton, QSizePolicy, QSpinBox, QVBoxLayout, QWidget,
)

import engine
import identity
import positions_store  # the project's positions, Woodcore's own file (calc/positions_store.py, v0.114)
import renumber_dialog  # deleting a position no plan draws any more, the ones after it numbered again (issue #9)
import plan_properties  # the pane of a drawing tool, and the *Section* of a position (issue #9)
import plan_canvas_tools  # the dimension tools (issue #9)
import plan_canvas_edit  # «Déplacer», «Copier» and the construction aids (issue #18)
import dimension_icons  # the dimension tools' symbols, the static models' and the schemas' own (issue #9)
import sharing  # the plan and the positions it makes written together, or neither (sharing.commit)
import project  # where the project this tab works on is (calc/project.py)
import theme  # the colours this tab states itself (theme.py, v0.90)
import cards  # the properties in cards, after the website (cards.py)
import usersettings  # the engineer's own settings: what a view shows (issue #9)
import validation
from domains import connector  # position_dimension: a position's dimension and unit, or nothing where it states none
from domains import fire  # the fire protection plans, which may follow a position plan (v0.115)
from domains import plan as model
from domains import plan_documents  # the documents a plan is drawn on (v0.114)
from domains import plan_pages  # the plans of both kinds drawn on one page (v0.115)
from domains import plan_svg
from flowbar import FlowLayout, FlowWidget
from plan_canvas import PlanCanvas
import drawing_tab  # what every tab of plans drawn on imported documents shares (v0.115)
from drawing_tab import (  # noqa: F401 -- names the tab's own code uses, and names other modules and the tests read here
    Blank, CurrentStack, DrawingTab, HISTORY, KINDS, NEW_ROW, document_text, next_free_id, number_text, plain_label, plan_text, svg_icon,
)
import document_view  # noqa: F401 -- every page of a document, ticked into the plans (v0.114); woodcore_gui reads its STRINGS here
import plan_command_builder  # noqa: F401 -- the «Commande Typst» entry (v0.114); woodcore_gui reads its STRINGS here
import sheet_editor  # noqa: F401 -- the export sheets' editor (v0.114); woodcore_gui reads its STRINGS here
import notifications  # every error, warning and information, gathered in one place (calc/notifications.py, v0.117)
import notices_ui  # what was a message box is a notice since v0.117 (notices_ui.tell)
from plan_tab_words import STRINGS  # split out of this module (issue #30): every name it had is still importable from it
from plan_tab_build import DRAW_DIMENSIONS, LEVEL_TOOL, SECTION_TOOLS, STOREY_BOX_ICON, STOREY_TOOLS, SUBTYPE_TOOLS, TOOLS, UNITS, list_plans, PlanBuildMixin  # split out of this module (issue #30): every name it had is still importable from it
from plan_tab_selection import PANE_TOOLS, PENDING, PlanSelectionMixin  # split out of this module (issue #30): every name it had is still importable from it

# Every path is the current project's, asked of project.current() when it is needed (v0.81, docs/architecture/layout.md §11): the plans' sources -- one file per plan, written by this tab and nothing else (section 3.3sexies) -- are its `plans_dir`, the documents a subfolder of it, the positions its positions.json.


def read_positions(here=None):
    """Every position of the project, in its order -- the numbers an element may be given: Woodcore's own positions.json (calc/positions_store.py, v0.114), read directly rather than from the export, so that a position just written -- a blank one this tab created, one the Positions tab added -- is known at once. None where the file cannot be read: the Positions tab says why."""
    try:
        return positions_store.read(here or project.current())
    except (validation.ValidationError, OSError):
        return []


class PlanTab(PlanSelectionMixin, PlanBuildMixin, DrawingTab):
    """The position plans (docs/domain/position-plans.md §3.3sexies, docs/ui/window.md §10quater): the documents, the saved plans, the elements of the one open, the export sheets and the command builder on the left; what is chosen there in the middle; its properties on the right.

    Everything drawn or checked here is calc/domains/plan.py's and plan_svg.py's -- the modules export_all.py exports the plans with -- so what this tab shows is what the report will. Saving writes the source, plans/<id>.json, and exports the plans at once. Leaving a plan saves it (autosave); the draft being edited survives a language switch or a reload all the same (it travels in view_state()).

    What every tab of plans drawn on imported documents does -- the documents, the plans' list, the export sheets, the builder, the history, saving on leaving -- is drawing_tab.DrawingTab's (v0.115); this class says what a position plan is, through its hooks, and draws one.
    """

    KIND = "position"
    KEY = "tab_plan"
    GRAPH_KIND = "plan"   # issue #71
    STYLE_KIND = "plan"
    STYLE_PREFIX = "plan"
    ID_PREFIX = "P"
    PENDING_KEY = PENDING
    WORD_MAP = {}
    domain = model

    # -- what DrawingTab asks of a position plan --

    def init_state(self):
        self.reread_positions()
        self.notes = []  # the last export's warnings for this plan
        self.created_positions = False  # a position written since the last save: the export follows at the next save
        self.floor_typed = False  # the engineer typed the numbering character himself: a storey chosen no longer proposes one

    def init_shortcuts(self):
        # a tool by its letter, as long as the plan has the focus -- typing a V into a field must stay a V
        for letter in model.TYPE_ORDER + ("O",):
            tool = "Ö" if letter == "O" else letter
            shortcut = QShortcut(QKeySequence(letter), self.canvas)
            shortcut.setContext(Qt.ShortcutContext.WidgetShortcut)
            shortcut.activated.connect(lambda tool=tool: self.choose_tool(tool))
        # R turns the column selected by a quarter (v0.117) -- no tool has the letter
        turn = QShortcut(QKeySequence("R"), self.canvas)
        turn.setContext(Qt.ShortcutContext.WidgetShortcut)
        turn.activated.connect(self.turn_quarter)

    def list_strings(self):
        return STRINGS.get(self.app.lang, STRINGS["fr"])

    def sources_dir(self):
        return project.current().plans_dir

    def list_sources(self):
        return list_plans()


    def has_drawing(self, source):
        return bool(source.get("elements") or source.get("axes"))

    def source_for_page(self, pid, docid, page, doc, width, height):
        """A plan of page `page` of document `docid`: the page's size as its sheet, the storey and the numbering character of the plan open."""
        source = model.new_source(pid, floor=self.source.get("floor", "0") or "0")
        source["storey"] = self.source.get("storey", "") or ""
        source["sheet"] = {"width": round(width, 2), "height": round(height, 2)}
        source["background"] = {"document": docid, "file": doc["file"], "page": page, "opacity": model.DEFAULT_OPACITY, "sha256": doc["sha256"]}
        return source

    def other_crops(self, docid):
        """The fire protection plans on document `docid`, for reference in the document view (v0.115): the pages they are drawn on, and the crops of those that state one of their own -- a fire plan that follows a position plan and states none shows that plan's crop, drawn already."""
        try:
            plans = plan_pages.fire_plans_on(project.current(), docid)
        except (OSError, ValueError):
            return [], {}
        pages, crops = set(), {}
        kind = self.t("plan_other_kind_fire")
        for fid, source, frame in plans:
            page = int((frame.get("background") or {}).get("page", 1))
            pages.add(page)
            if fire.own_crop(source) and frame.get("crop"):
                crop = frame["crop"]
                label = " – ".join(part for part in (fid, source.get("name") or source.get("label") or "") if part)
                crops.setdefault(page, []).append({"plan": fid, "rect": (crop["x"], crop["y"], crop["w"], crop["h"]), "label": label, "kind": kind})
        return sorted(pages), crops

    def followers_of(self, pids):
        """The fire protection plans that follow the position plans `pids` (v0.115): archiving these leaves them nothing to be drawn over, so they are detached first (detach_followers)."""
        wanted = set(pids)
        out = []
        for path in fire.source_paths(project.current().fire_dir):
            try:
                source = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if isinstance(source, dict) and fire.follows(source) in wanted:
                out.append((path.stem, source))
        return out

    def followers_note(self, pids):
        followers = self.followers_of(pids)
        if not followers:
            return ""
        return self.t("plan_followers_detached", fire=", ".join(fid for fid, _source in followers), plans=", ".join(pids))

    def detach_followers(self, pids):
        """Every fire protection plan that follows one of `pids` given the frame it followed -- its background, sheet, crop and scale copied in (fire.detach) -- and written, before the position plans are archived: none is left over a frame that is gone (the engineer's decision of 06.10.2026)."""
        followers = self.followers_of(pids)
        if not followers:
            return []
        here = project.current()
        frames = fire.plan_frames(here.plans_dir)
        done = []
        for fid, source in followers:
            frame, problem = fire.frame_of(fire.upgrade(source), frames)
            if problem is not None:
                continue
            detached = fire.detach(source, frame)
            detached["schema_version"] = fire.version_of(detached)
            target = here.fire_dir / f"{fid}.json"
            try:
                fire.check_source(detached, target.name)
                engine.write_json(target, detached)
            except (validation.ValidationError, OSError) as exc:
                notices_ui.tell(str(exc), notifications.CRITICAL, exc=exc, source="plan_tab")
                continue
            done.append(fid)
        if done:
            self.app.set_status(self.t("plan_followers_done", fire=", ".join(done)))
        return done

    def plan_records(self):
        """The plans of the export, data/plans.json's `plans` -- what the builder offers; none where nothing was exported."""
        try:
            return json.loads((project.current().data_dir / "plans.json").read_text(encoding="utf-8")).get("plans", {})
        except (OSError, ValueError, AttributeError):
            return {}

    def builder_records(self):
        return self.plan_records()

    def build_entries(self, v):
        """The elements and axes of the plan open, and the numbers the project has no position of."""
        v.addWidget(self.heading(self.t("plan_elements")))
        self.element_list = QListWidget()
        self.element_list.currentItemChanged.connect(self.on_element_row)
        v.addWidget(self.element_list, 2)
        self.missing = plain_label("", wrap=True)
        self.missing.setStyleSheet(f"color: {theme.colour('warning')};")
        v.addWidget(self.missing)
        self.missing_button = QPushButton(self.t("plan_add_missing"))
        self.missing_button.clicked.connect(lambda: self.add_missing_positions())
        v.addWidget(self.missing_button)
        v.addSpacing(6)

    def build_drawing_center(self):
        return self.build_plan_center()

    def build_drawing_properties(self):
        return self.build_plan_properties()

    def new_drawing_source(self, pid):
        """A new plan, on an empty sheet, of the storey and the numbering character of the plan open."""
        source = model.new_source(pid, floor=self.source.get("floor", "0") or "0")
        source["storey"] = self.source.get("storey", "") or ""
        return source

    def prepare_duplicate(self, source):
        # the copy is another plan: its numbers would all be drawn twice
        for element in source.get("elements", []):
            if element.get("label"):
                element["label"] = ""

    def reset_drawing_state(self):
        """Another plan shown: its numbering character is its own."""
        self.floor_typed = False

    def drawing_view_state(self):
        return {
            "subtypes": dict(self.canvas.subtypes),
            "tool_defaults": copy.deepcopy(self.canvas.tool_defaults),   # a tool's defaults survive a language switch (issue #9, REQ-015)
            "snap": [self.snap_axes.isChecked(), self.snap_elements.isChecked()],
        }

    def restore_drawing_before(self, state):
        self.canvas.subtypes.update(state.get("subtypes", {}))
        self.canvas.tool_defaults.update(copy.deepcopy(state.get("tool_defaults", {})))
        snap = state.get("snap", [True, True])
        self.snap_axes.setChecked(snap[0])
        self.snap_elements.setChecked(snap[1])

    def restore_drawing_after(self, state):
        pass

    def on_shown(self):
        """The tab brought to the front: the positions, the documents and the sheets read again -- the Positions tab may have added one, VS Code written a sheet."""
        self.reread_positions()
        super().on_shown()

    # -- building and drawing a position plan --


    def reread_positions(self):
        """The project's positions read again (read_positions): the numbers the elements may be given."""
        self.positions = read_positions()
        self.position_ids = [p["position"] for p in self.positions]
        self.position_by_id = {p["position"]: p for p in self.positions}

    def export_listed(self, text):
        """The plans exported without naming one -- what a drop into a folder or an archive needs, which changes a field and no drawing."""
        self.finish_layer_export()   # a layer switched being exported in its thread: finished first (drawing_tab, v0.116)
        try:
            model.export(project.current().plans_dir, project.current().root, project.current().data_dir, self.position_ids, self.text_values(), positions_store.section_types(self.positions))
        except (validation.ValidationError, engine.EngineError, OSError) as exc:
            notices_ui.tell(self.t("plan_move_failed", error=exc), notifications.CRITICAL, exc=exc, key="plan_move_failed", args=dict(error=exc), source="plan_tab")
            return False
        self.app.set_status(text)
        return True

    def save(self, quiet=False):
        """Writes plans/<id>.json and exports the plans -- the draft checked first by the same rules export_all.py applies, so a plan that saves is one the report can build. True when saved. `quiet` is the autosave's: a refusal is said in the status line rather than in a box, and a rename -- which asks -- is not made."""
        fail = (lambda text: self.app.set_status(text) or False) if quiet else self.fail
        source = copy.deepcopy(self.source)
        pending = source.pop(PENDING, {})  # the draft's own, never the file's
        # written by this version, whatever version the file was read as -- 1.7 where it holds a text (issue #43), its variables' last values refreshed (D-14)
        model.figure_text.refresh_all(source, self.text_values())
        if not source.get("texts"):
            source.pop("texts", None)   # the last text deleted: written as before one was placed
        if not source.get("outlines"):
            source.pop("outlines", None)   # and so for the building's outline (issue #54): an empty list is no field of a plan's file
        source["schema_version"] = model.version_of(source)
        pid = source.get("id", "")
        if not model.ID_PATTERN.match(pid):
            return fail(self.t("plan_id_invalid", id=pid))
        old = self.current_id
        renaming = old is not None and pid != old
        # the file system ignores case, the report does not: EG and eg are one file, and two ids
        clash = any(t.lower() == pid.lower() for t in self.taken_ids()) and (old is None or pid.lower() != old.lower())
        if clash:
            return fail(self.t("plan_id_exists", id=pid))
        if renaming and (quiet or QMessageBox.question(self, "Woodcore", self.t("plan_rename", old=old, new=pid)) != QMessageBox.StandardButton.Yes):
            return False
        background = source.get("background")
        if background:
            path = model.background_path(project.current().root, background["file"])
            if path is not None and path.is_file():
                background["sha256"] = model.file_hash(path)
        target = project.current().plans_dir / f"{pid}.json"
        try:
            model.check_source(source, target.name)
        except validation.ValidationError as exc:
            return fail(str(exc))
        self.reread_positions()
        # the positions the plan draws and the project has not got: made now, with the plan, in one write (issue #9) -- a number taken meanwhile by another tab is refused rather than given two elements
        made = []
        for label in model.unknown_labels(source, self.position_ids):
            element = next(e for e in source["elements"] if e.get("label") == label)
            made.append({"position": label, "type": positions_store.type_for(element["type"]),
                         **{key: value for key, value in pending.get(label, {}).items() if key in positions_store.SECTION_KEYS}})
        orphans = [] if quiet else self.orphaned(target if not renaming else project.current().plans_dir / f"{old}.json", source)
        try:
            project.current().plans_dir.mkdir(parents=True, exist_ok=True)
            writes = [(target, engine.source_bytes(source),  # LF on every platform (spec 2026-10-19-base-saine-nettoyage, G1)
                       target.read_bytes() if target.is_file() else None)]
            store = positions_store.path(project.current())
            rows = positions_store.read(project.current())
            # a section chosen in the pane for a position the project has: its three cells written with the plan (D-011)
            changed = False
            for row in rows:
                chosen = pending.get(row["position"])
                if chosen and row["position"] in model.plan_labels(source):
                    for key in positions_store.SECTION_KEYS:
                        if key in chosen and chosen[key] != row.get(key, ""):
                            row[key] = chosen[key]
                            changed = True
            if made or changed:
                for row in made:
                    positions_store.check_row(row)
                writes.append((store, positions_store.encode([positions_store.check_row(row) for row in rows] + made), store.read_bytes() if store.is_file() else None))
            sharing.commit(writes)
            if made or changed:
                positions_store.write_workbook(project.current())   # the workbook beside positions.json, never read, follows it (issue #64, D-24)
            if renaming:
                (project.current().plans_dir / f"{old}.json").unlink(missing_ok=True)
        except (OSError, validation.ValidationError) as exc:
            return fail(str(exc))
        if made:
            self.created_positions = True
            self.reread_positions()
            self.app.set_status(self.t("plan_positions_made", ids=", ".join(row["position"] for row in made)))
        if changed and not made:
            self.created_positions = True
            self.reread_positions()
        for label in list(self.source.get(PENDING, {})):
            if label in self.position_ids:
                self.source[PENDING].pop(label, None)
        if not self.source.get(PENDING, True):
            self.source.pop(PENDING, None)
        if background and "sha256" in background:
            self.source["background"]["sha256"] = background["sha256"]
        self.source["schema_version"] = source["schema_version"]
        self.current_id = pid
        self.dirty = False
        self.export(pid, self.t("plan_saved", id=pid), quiet=quiet)
        self.reload_list(select=pid)
        self.on_changed()
        self.dirty = False
        self.revert_button.setEnabled(False)
        self.update_list_marker()
        self.follow_positions()
        if orphans:
            self.offer_deletion(orphans)
        return True

    def orphaned(self, saved_file, source):
        """The positions this plan drew when it was last saved and draws no more, that no other plan draws either: the positions whose last element was just taken off (issue #9: a number is one object, and an object deleted takes its position with it -- once the engineer confirms)."""
        try:
            before = model.plan_labels(json.loads(saved_file.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            return []
        gone = [label for label in before if label not in set(model.plan_labels(source)) and label in self.position_ids]
        if not gone:
            return []
        for other in project.current().plans_dir.glob("*.json"):
            if other.resolve() == saved_file.resolve():
                continue
            try:
                drawn = set(model.plan_labels(json.loads(other.read_text(encoding="utf-8"))))
            except (OSError, ValueError):
                continue
            gone = [label for label in gone if label not in drawn]
        return gone

    def offer_deletion(self, orphans):
        """Asks whether the positions no plan draws any more are deleted, the ones after them numbered again everywhere (calc/renumbering.py, renumber_dialog) -- and, where that was done, reads the plan again from its file, its numbers changed, with an empty history: what was written is no step of «Annuler»."""
        done = renumber_dialog.ask(self, self.app, orphans)
        if not done:
            return
        self.reread_positions()
        self.dirty = False
        self.load(self.current_id)   # its numbers changed on disk; an empty history (open_source)
        self.created_positions = True
        self.follow_positions()

    def follow_positions(self):
        """The blank positions this tab created exported with the rest, as the Positions tab's writes are (the window's own `reexport`) -- once the plan naming them is saved. While another export runs, the next one carries them."""
        if not self.created_positions or getattr(self.app, "process", None) is not None:
            return
        reexport = getattr(self.app, "reexport", None)
        if reexport is not None:
            self.created_positions = False
            reexport()

    def export(self, pid, done_text, quiet=False):
        """The plans' part of the export, run here and now: data/plans.json and data/plans/, from every saved source. A failure -- another plan's file that no longer validates, a background that was moved -- leaves data/ as it was and says why."""
        self.finish_layer_export()   # a layer switched being exported in its thread: finished first (drawing_tab, v0.116)
        try:
            # with the positions' section types, which a bracing wall's construction mode is held against (issue #54)
            notes = model.export(project.current().plans_dir, project.current().root, project.current().data_dir, self.position_ids, self.text_values(), positions_store.section_types(self.positions))
        except (validation.ValidationError, engine.EngineError, OSError) as exc:
            if quiet:
                self.app.set_status(self.t("plan_export_failed", id=pid, error=exc))
            else:
                notices_ui.tell(self.t("plan_export_failed", id=pid, error=exc), notifications.CRITICAL, exc=exc, key="plan_export_failed", args=dict(id=pid, error=exc), source="plan_tab")
            return False
        mine = [n for n in notes if pid and str(n).startswith(f"plan {pid}:")]
        self.app.set_status(self.t("plan_saved_warnings", id=pid, n=len(mine)) if mine else done_text)
        self.builder.set_plans(self.plan_records())
        self.export_followers(pid)
        return True

    def export_followers(self, pid):
        """The fire protection plans exported after the position plans (v0.115): a fire plan that follows a position plan is drawn over that plan's export, so a position plan saved, cropped or calibrated changes it too. Only where the project has fire plans; a failure is said in the status line, the position plan being saved all the same."""
        here = project.current()
        if not fire.source_paths(here.fire_dir):
            return
        try:
            fire.export(here.fire_dir, here.plans_dir, here.root, here.data_dir, values=self.text_values())
        except (validation.ValidationError, engine.EngineError, OSError) as exc:
            self.app.set_status(self.t("plan_export_failed", id=pid, error=exc))
