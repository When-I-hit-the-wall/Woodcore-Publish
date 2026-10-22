"""What every tab of plans drawn on imported documents has in common (v0.115): the base of Woodcore's «Plan de positions» tab (plan_tab.py, docs/domain/position-plans.md §3.3sexies, docs/ui/window.md §10quater), written so that a second kind of plan -- the fire protection plan -- is a second subclass of it rather than a copy of the first.

**What lives here** is everything the position plan's tab did that is not about position plans: the left pane's documents, plans in their folders, export sheets and «Commande Typst» entry; the centre's and the right pane's stacks switching on what is chosen; a document imported, shown every page of it (document_view.py), cut into plans by ticking its pages, a crop and a calibration drawn on a page written into that page's plan, a page turned and its layers switched; the export sheets listed, made, archived and edited (sheet_editor.py); the undo history; the selected entry's own size factors (stylefactors.py); a plan saved when it is left (autosave), listed, filed in folders, archived, duplicated; and what a rebuild of the window carries over (view_state, restore).

**The documents since v0.116**: each tab lists the documents it imported (`DOC_OWNER`, plan_documents' `owner`); a page carries several frames, each a plan -- the tick makes the first, of the whole page, the first frame drawn crops it, every further frame is a new plan (`on_doc_crop`); a frame chosen with the view's «Sélection» makes its plan the plan open and shows the plan's own «Plan» module in the document's right pane (`show_frame_module`), written as a field is left; Suppr archives the plans of the frames chosen; and a layer switched is written at once and exported in a thread `LAYER_EXPORT_MS` later (`on_layers_changed`, `finish_layer_export`).

**What a subclass says** is in class attributes and in hook methods, each documented below where it is declared: `KIND`, `KEY`, `STYLE_KIND`, `STYLE_PREFIX`, `ID_PREFIX`, `WORD_MAP` and `domain`; and, among the hooks, `sources_dir`, `list_sources`, `sources_on`, `has_drawing`, `source_for_page`, `document_crops`, `other_crops`, `current_page`, `turn_page_drawings`, `selected_entry`, `build_drawing_center`, `build_drawing_properties`, `make_builder`, `builder_records`, `export`, `export_listed`, `save`, `fill`, `on_changed`, `on_selection`, `choose_tool`.

**The words**: every key the base says is looked up through `self.w(key, **values)`, which reads `WORD_MAP` first -- `{"plan_list": "fp_list"}` sends a key of the position plan's to one of the subclass's own -- and the window's `t` after. The position plan's tab maps nothing.

⚠️ **The read-only guard** of woodcore_gui.py (`WRITERS`) wraps methods by name on the classes it lists, reading each class's own `vars()` and those of the mixins it is composed of (`woodcore_gui.own_classes`, issue #30): a writing method defined here or in DrawingTab's mixins is guarded only because woodcore_gui lists `DrawingTab` beside `PlanTab` (tests/test_plan_tab_rework.py holds it).
"""

import copy
import json
import threading
from pathlib import Path

from PySide6.QtCore import QModelIndex, QObject, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QFileDialog, QHBoxLayout, QInputDialog, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMessageBox, QPushButton,
    QScrollArea, QSlider, QSplitter, QStackedWidget, QToolButton, QVBoxLayout, QWidget,
)

import busy  # a long operation behind the loading card (busy.py)
import cards  # the properties in cards, after the website (cards.py)
import tasks  # what runs in the background, said by the chip at the top right (tasks.activity, v0.117)
import woodcore_start  # the start screen, painted between the panes built (v0.117)
import chrome  # the fold button of the left pane, the navigation's own (chrome.py, v0.117)
import autosave  # the one question where a draft cannot be saved (autosave.py, v0.117)
import views  # the four views the top bar's switch chooses between (views.py, v0.117)
import engine
import grouped_list
import project  # where the project this tab works on is (calc/project.py)
import sheets  # the export sheets, Plans/<id>.typ (calc/sheets.py, v0.114)
import source_archive  # «Supprimer» archives (source_archive.py)
import stylefactors  # an entry's own size factors, shown as an overridden b/h is (stylefactors.py, v0.99)
import validation
import linkable_spin  # the export's values, which a text's variables print (issue #43)
import text_pane  # a text's pane, the four drawing engines' one (issue #43)
from domains import figure_style  # which of the three factors an entry may state (figure_style.py)
from domains import plan as plan_model  # the documents' machinery and the pages' sizes are the position plan's (plan.py, plan_documents.py)
from domains import plan_documents  # the documents a plan is drawn on (v0.114)
from domains import plan_pages  # the plans of both kinds drawn on one page: turned together, exported together (v0.115)
import document_view  # every page of a document, ticked into the plans (v0.114)
import plan_command_builder  # the «Commande Typst» entry (v0.114)
import plan_superposition  # another plan of the tab shown over the plan open (v0.116)
import sheet_editor  # the export sheets' editor (v0.114)
import sheet_list  # the export sheets' list, the PDF bundles as folders (v0.116)
import bundle_view  # an export document's pages and its fields, its folder chosen (v0.117)
import notifications  # every error, warning and information, gathered in one place (calc/notifications.py, v0.117)
import notices_ui  # what was a message box is a notice since v0.117 (notices_ui.tell)
from drawing_tab_panes import CurrentStack, KINDS, KIND_VIEW, LIST_MIN_HEIGHT, MODULE_WHEN, NEW_ROW, VIEW_BOXES, VIEW_KIND, plain_label, DrawingPanesMixin  # split out of this module (issue #30): every name it had is still importable from it
from drawing_tab_documents import Blank, _Background, _export_layers, _run_layer_export, document_text, DrawingDocumentsMixin  # split out of this module (issue #30): every name it had is still importable from it
from drawing_tab_clip import DrawingClipMixin  # Ctrl+A, Ctrl+C and Ctrl+V between plans (issue #61)
from canvas_editor import CanvasEditorTab  # «Annuler» and «Rétablir», once for every tab with a canvas
from drawing_tab_sheets import HISTORY, DrawingSheetsMixin  # split out of this module (issue #30): every name it had is still importable from it
import svg_icons


# A layer switched in the document view is exported this long after the last switch, in a thread of its own (v0.116): an export flattens every page drawn on with the layers taken out (plan_documents.flatten_page), seconds on an architect's plan set, which the window must not stop for -- and a run of switches is one export.
LAYER_EXPORT_MS = 1200


class _ExportNotice(QObject):
    """Says, in the window's thread, that the export of a layer switched is done: its error, or None."""

    done = Signal(object)


def number_text(value, digits=2):
    text = f"{value:.{digits}f}".rstrip("0").rstrip(".")
    return "0" if text in ("-0", "") else text


def list_sources(domain, folder):
    """(id, source, folder) of every saved source of `domain` in `folder`, in file-name order -- the source read from its file, or None for one that cannot be read, which is listed by its name. The folder is the source's own `group` field (grouped_list.py)."""
    out = []
    for path in domain.source_paths(folder):
        group = grouped_list.ROOT_GROUP
        try:
            source = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(source, dict):
                raise ValueError("not a JSON object")
            group = grouped_list.group_of(source)
        except (OSError, ValueError, AttributeError, TypeError):
            source = None
        out.append((path.stem, source, group))
    return out


def plan_text(pid, source):
    """A plan as the left pane lists it: «P01 – Hauptgebäude – EG», its id, its name (else its description) and its storey, a part left out where it is empty."""
    source = source or {}
    parts = [pid, source.get("name") or source.get("label") or "", source.get("storey") or ""]
    return " – ".join(part for part in parts if part)


def next_free_id(taken, prefix="P"):
    lowered = {t.lower() for t in taken}
    for n in range(1, 1000):
        pid = f"{prefix}{n:02d}"
        if pid.lower() not in lowered:
            return pid
    return prefix


def svg_icon(svg, size=QSize(26, 18)):
    """A plan tool's icon, `size` logical pixels (svg_icons.svg_icon)."""
    return svg_icons.svg_icon(svg, size)


class DrawingTab(DrawingClipMixin, DrawingSheetsMixin, DrawingDocumentsMixin, DrawingPanesMixin, CanvasEditorTab, QWidget):
    """A tab of plans drawn on imported documents: the documents, the saved plans, what the subclass lists of the plan open, the export sheets and the command builder on the left; what is chosen there in the middle; its properties on the right.

    A subclass builds the drawing's own centre and properties (`build_drawing_center`, which makes `self.canvas`; `build_drawing_properties`, which makes `self.id_edit`, `self.show_outside_box` and `self.revert_button`) and says what its plans are through the hooks below; the rest is here.
    """

    # The kind of plan this tab draws: "position" for the position plans, "fire" for the fire protection plans -- the word a page shared between the two kinds is told apart by.
    KIND = "position"
    # The key the window keeps this tab's view and empty folders under (app.views, app.folder_settings): the tab's own entry of woodcore_gui.TABS.
    KEY = "tab_plan"
    # Which row of figure_style.ENTRY_KEYS the selected entry's own factors are read from, and the key prefix of their words (stylefactors.EntryRows).
    STYLE_KIND = "plan"
    STYLE_PREFIX = "plan"
    # What a new plan's id is made of: P01, P02, …
    ID_PREFIX = "P"
    # The base says the position plan's words; a subclass sends a key to one of its own here ({"plan_list": "fp_list"}).
    WORD_MAP = {}
    # The domain module of the plans: new_source, check_source, source_paths, SOURCE_SCHEMA_VERSION.
    domain = plan_model
    # Which documents the tab lists and imports (plan_documents.OWNERS, v0.116): each tab its own.
    DOC_OWNER = "plan"
    # Which kind of export sheet the tab makes, lists and bundles (calc/sheets.py KINDS, v0.116): each tab its own.
    SHEET_KIND = "position"
    # The views the top bar's switch offers (views.py, v0.117): «Dessin» the default.
    VIEWS = views.PLAN_VIEWS

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.t = app.t
        self.loading = False  # set while the form is being filled, so filling it is not taken for an edit
        self.dirty = False
        self.current_id = None  # the saved plan the tab holds; None for one not saved yet
        self.source = self.blank_source(self.free_id([]))
        self.init_history()
        self.slider_down = False
        self.entry_style = None      # the rows of the selected entry's own factors, built with the selection panel and gone with it (build_entry_style)
        self.empty_folders = list(app.folder_settings(self.KEY))   # folders holding nothing: a view preference, kept by the window (grouped_list.py, v0.75)
        self.modules = []  # (card, when) of the right pane's plan page, in the order they stand: shown or hidden by the selection (add_module, update_modules)
        self.init_state()
        self.view_kind = "plan"  # what the left pane has chosen (KINDS)
        self.view = "draw"  # the view the top bar's switch shows (VIEW_KIND), always the one of view_kind (show_kind)
        self.view_pending = False  # a view set while the tab was hidden, opened -- compiled -- when it is shown (review A10)
        self.doc_id = None  # the document shown, where one is
        self.doc_page = None  # the page of it last clicked
        self.sheet_id = None  # the export sheet shown, where one is
        self.documents = {}  # every document of the tab, by id, as last read (None for one that cannot be read)
        self.filling = False  # set while a list is filled, so filling it is not taken for a choice
        self.frame_module_at = None  # where the plan's module stood in its column while it is shown for a frame chosen in the document view (show_frame_module); None while it stands there
        self.layer_export_here = None  # the project a layer was switched in, to be exported (on_layers_changed)
        self.layer_timer = QTimer(self)
        self.layer_timer.setSingleShot(True)
        self.layer_timer.setInterval(LAYER_EXPORT_MS)
        self.layer_timer.timeout.connect(self.start_layer_export)
        self.layer_notice = _ExportNotice(self)
        self.layer_notice.done.connect(self.on_layer_export_done)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        # the heaviest tabs of the window: the start screen painted between their three panes, so it never stands still for the whole tab (woodcore_start.pump, v0.117)
        self.splitter.addWidget(self.build_list())
        woodcore_start.pump()
        self.splitter.addWidget(self.build_center())
        woodcore_start.pump()
        self.splitter.addWidget(self.build_properties())
        woodcore_start.pump()
        for index, stretch in enumerate((1, 6, 2)):
            self.splitter.setStretchFactor(index, stretch)
        layout.addWidget(self.splitter, 1)

        for sequence, slot in ((QKeySequence.StandardKey.Save, self.save), (QKeySequence.StandardKey.Undo, self.undo),
                               (QKeySequence.StandardKey.Redo, self.redo), (QKeySequence("Ctrl+Y"), self.redo)):
            shortcut = QShortcut(QKeySequence(sequence), self)
            shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
            shortcut.activated.connect(lambda slot=slot: slot())
        self.init_shortcuts()
        self.init_clip_shortcuts()
        self.watch_frame_fields()
        fit = QShortcut(QKeySequence("F"), self.canvas)
        fit.setContext(Qt.ShortcutContext.WidgetShortcut)
        fit.activated.connect(self.canvas.fit)

        # pypdf reads a page's size when a page is turned or a background chosen: imported now, beside the window, rather than then
        threading.Thread(target=plan_model.preload, daemon=True).start()
        self.reload_documents()
        self.reload_sheets()
        self.restore(app.views.get(self.KEY))
        # the builder's command filled from the export at once -- the page it prints is compiled only once the entry is chosen (open_builder)
        self.builder.set_plans(self.builder_records())
        if self.current_id:
            self.builder.set_plan(self.current_id)

    # -- what a subclass says: its words, its plans, its drawing --

    def w(self, key, **values):
        """A word of the tab, in the window's language: `key`, or the subclass's own key `WORDS` sends it to."""
        return self.t(self.WORD_MAP.get(key, key), **values)

    def word(self, suffix, **values):
        """A word of the list the base names by its suffix (source_editor.WORD_SUFFIXES): the position plan's `plan_<suffix>`, or the key WORD_MAP sends it to."""
        return self.w(f"plan_{suffix}", **values)

    def init_state(self):
        """The subclass's own attributes, set before anything is built."""

    def init_shortcuts(self):
        """The subclass's own shortcuts, after «Enregistrer», «Annuler» and «Rétablir» (the canvas exists by then)."""

    def list_strings(self):
        """The words the plans' list (grouped_list.GroupedList) is built with, in the window's language."""
        return {}

    def sources_dir(self):
        """The folder the plans' sources are written in, one file per plan."""
        raise NotImplementedError

    def list_sources(self):
        """(id, source, folder) of every saved plan, in file-name order (list_sources)."""
        return list_sources(self.domain, self.sources_dir())

    def entry_text(self, pid, source):
        """A plan as the list and the document view's crops name it."""
        return plan_text(pid, source)

    def free_id(self, taken):
        """The next id not in `taken`: ID_PREFIX and two digits."""
        return next_free_id(taken, self.ID_PREFIX)

    def blank_source(self, pid):
        """A plan of nothing, of id `pid`: what a plan no file is read for starts from, and what a source read is completed with."""
        return self.domain.new_source(pid)

    def new_drawing_source(self, pid):
        """The plan «Nouveau» makes, of id `pid`."""
        return self.blank_source(pid)

    def prepare_duplicate(self, source):
        """`source`, a copy of the plan open given its new id, made ready to be another plan («Dupliquer»)."""

    def reset_drawing_state(self):
        """What the subclass forgets when another plan is shown (open_source)."""

    def sources_on(self, docid, page=None):
        """[(id, source)] of this tab's plans drawn on document `docid` -- on its page `page` where one is named --, in id order."""
        out = []
        for pid, source, _group in self.list_sources():
            if self.source_document(source) == docid and (page is None or self.source_page(source) == page):
                out.append((pid, source))
        return out

    def source_document(self, source):
        """The document a plan is drawn on, or None."""
        return ((source or {}).get("background") or {}).get("document")

    def source_page(self, source):
        """The page of its document a plan is drawn on."""
        return int(((source or {}).get("background") or {}).get("page", 1))

    def has_drawing(self, source):
        """True where something is drawn on the plan -- what unticking its page asks about first."""
        raise NotImplementedError

    def source_for_page(self, pid, docid, page, doc, width, height):
        """The plan of id `pid` ticking page `page` of document `doc` (`docid`), of `width` × `height` sheet units, makes."""
        raise NotImplementedError

    def document_crops(self, docid):
        """(pages, crops) of this tab's plans on document `docid`: the pages ticked, and {page: [{"plan", "rect", "label"}]} their crops."""
        plans = self.sources_on(docid)
        pages = sorted({self.source_page(s) for _pid, s in plans})
        crops = {}
        for pid, source in plans:
            crop = source.get("crop")
            sheet = source.get("sheet") or {}
            if crop:
                rect, whole = (crop["x"], crop["y"], crop["w"], crop["h"]), False
            elif sheet.get("width") and sheet.get("height"):
                rect, whole = (0.0, 0.0, float(sheet["width"]), float(sheet["height"])), True   # a plan of the whole page: framed by the page, and chosen by a click on it (v0.116)
            else:
                continue
            crops.setdefault(self.source_page(source), []).append({"plan": pid, "rect": rect, "label": self.entry_text(pid, source), "whole": whole})
        return pages, crops

    def other_crops(self, docid):
        """(pages, crops) of the other kind's plans on document `docid`, drawn muted and never hit (document_view's `"other"` crops and set_other_pages); none by default."""
        return [], {}

    def uncropped_on(self, docid, page):
        """The ids of this tab's plans on page `page` of document `docid` that show the whole page -- no crop of their own (v0.116): the first frame drawn on the page is theirs, every further frame a new plan."""
        return [pid for pid, source in self.sources_on(docid, page) if not source.get("crop")]

    def source_for_frame(self, pid, docid, page, doc, width, height):
        """The plan of id `pid` a frame drawn on page `page` of document `doc` makes, its crop set by the caller (v0.116) -- what ticking the page makes, by default."""
        return self.source_for_page(pid, docid, page, doc, width, height)

    def current_page(self):
        """(document, page) the plan open is drawn on, or None: what the «Fond» card's rotation buttons turn, and what tells whether a layer switched concerns it."""
        background = self.source.get("background") or {}
        if background.get("document"):
            return background["document"], int(background.get("page", 1))
        return None

    def turn_page_drawings(self, here, docid, page, delta):
        """Page `page` of document `docid` turned by `delta` degrees, and every plan drawn on it -- of BOTH kinds, position and fire protection plans alike -- turned with it (plan_pages.rotate_page). {"position": [ids], "fire": [ids]}; raises what plan_pages raises, nothing written then."""
        return plan_pages.rotate_page(here, docid, page, delta)

    def complete_source(self, source, pid):
        """A source read from its file completed with what a plan of nothing has (blank_source) -- a key added since it was written. A subclass whose plans may carry no frame of their own completes less."""
        for key, value in self.blank_source(pid).items():
            source.setdefault(key, copy.deepcopy(value))
        return source

    def followers_of(self, pids):
        """[(id, source)] of the plans of the other kind that depend on the plans `pids` of this tab -- the fire plans that follow a position plan. None by default."""
        return []

    def detach_followers(self, pids):
        """What depends on the plans `pids`, made to depend on them no more, before they are archived (a fire plan given the frame it followed, fire.detach). Nothing by default."""

    def followers_note(self, pids):
        """The sentence a question about archiving `pids` adds where other plans depend on them; "" where none does."""
        return ""

    def calibration_refused(self, pid):
        """Why a calibration drawn on the page of plan `pid` is not this plan's to take, or None where it is: a fire plan that follows a position plan takes that plan's scale."""
        return None

    def builder_records(self):
        """The plans of the export the «Commande Typst» builder offers."""
        return {}

    def make_builder(self):
        """The «Commande Typst» builder (plan_command_builder.CommandBuilder, its options and its command the subclass's own)."""
        return plan_command_builder.CommandBuilder(lang=self.app.lang, mono_font=self.app.mono_font, copy=self.app.copy, cache_key=self.KEY)

    def build_entries(self, layout):
        """What the left pane lists of the plan open, between the plans and the export sheets -- added to `layout`."""

    def build_drawing_center(self):
        """The centre's first page: the plan's drawing with its tools. Makes `self.canvas`."""
        raise NotImplementedError

    def build_drawing_properties(self):
        """The right pane's first page: the plan's properties. Makes `self.id_edit`, `self.show_outside_box` and `self.revert_button`."""
        raise NotImplementedError

    def drawing_view_state(self):
        """What the subclass carries over a rebuild, beside the base's."""
        return {}

    def restore_drawing_before(self, state):
        """What the subclass takes back from `state` before the plan is shown again."""

    def restore_drawing_after(self, state):
        """What the subclass takes back from `state` once the plan is shown again."""

    def fill(self):
        """The form from the source -- a plan loaded, restored or undone."""

    def on_changed(self):
        """After every change of the source."""

    def on_selection(self):
        """After the canvas's selection changed."""

    def choose_tool(self, tool):
        """The canvas's tool chosen."""

    def selected_entry(self):
        """The entry whose own size factors the panel shows, and the collection it belongs to; `(None, None)` with nothing selected. Which collection it is decides which of the three factors it may state (`figure_style.ENTRY_KEYS`)."""
        return None, None

    def export(self, pid, done_text, quiet=False):
        """The plans' part of the export, run here and now. True where it ran."""
        raise NotImplementedError


    def save(self, quiet=False):
        """Writes the plan open's source and exports the plans. True when saved."""
        raise NotImplementedError

    # -- building --


    # -- the right pane's modules, by what is selected (v0.116) --


    # -- what the left pane has chosen --


    # -- the views (views.py, v0.117) --


    # -- the source and the form --

    def document(self, docid):
        """The document `docid` as last read, else read now; None where it is not there or cannot be read."""
        doc = self.documents.get(docid)
        if doc is None and docid:
            try:
                doc = plan_documents.read(project.current(), docid)
            except validation.ValidationError:
                return None
            self.documents[docid] = doc
        return doc

    def edit(self, apply, history=True):
        """An edit of the source made through the form: kept for «Annuler», applied, drawn. One that changes nothing leaves no step in the history -- choosing «calibrée» before the two points are clicked, say."""
        if self.loading:
            return
        before = copy.deepcopy(self.source)
        pushed = history and not self.slider_down
        if pushed:
            self.push_history()
        apply()
        if self.source == before:
            if pushed:
                self.undo_stack.pop()
            return
        self.canvas.invalidate()
        self.on_changed()

    def ask_choice(self, title, text, choices, index):
        """The index of the choice taken, or None -- a dialog, replaced in a test (a modal off-screen never returns)."""
        item, ok = QInputDialog.getItem(self, title, text, choices, index, False)
        return choices.index(item) if ok and item in choices else None

    def ask_length(self):
        """The real length between two calibration points, in m, or None -- a dialog, replaced in a test."""
        length, ok = QInputDialog.getDouble(self, self.w("plan_calibrate_title"), self.w("plan_calibrate_ask"), 1.0, 0.001, 100000.0, 3)
        return length if ok else None

    def on_slider_pressed(self):
        if not self.loading:
            self.push_history()
        self.slider_down = True

    def on_slider_released(self):
        self.slider_down = False

    def on_opacity(self, value):
        if self.source.get("background"):
            self.edit(lambda: self.source["background"].__setitem__("opacity", round(value / 100, 2)))

    def on_style(self, key, value):
        self.edit(lambda: self.source.setdefault("style", {}).__setitem__(key, round(value / 100, 2)))

    def on_show_outside(self, checked):
        """«Afficher toute la page»: the page around the crop, under a veil -- a view, saved in no file."""
        self.canvas.set_show_outside(bool(checked))

    def reset_crop(self):
        self.edit(lambda: self.source.pop("crop", None))
        self.canvas.fit()

    # -- the documents (v0.114) --


    # -- the export sheets (v0.114) --


    # -- the PDF bundles of the export list, and the list of the positions (v0.116) --


    # -- the «Commande Typst» entry (v0.114) --


    # -- history --


    # -- the size of the entry selected (v0.99) --


    # -- the plans --

    def lists_object(self, ident):
        """Whether the plan `ident` of the graph of dependencies is one this tab draws (issue #71)."""
        return ident in self.taken_ids()

    def open_object(self, ident):
        """A plan of the graph opened here, as a crop clicked in the document view opens one (`open_plan`)."""
        self.open_plan(ident)

    def listed(self):
        """The plans of the kind the tab draws, «P01 – Hauptgebäude – EG» (entry_text), in the folder each names."""
        return [(pid, self.entry_text(pid, source), group) for pid, source, group in self.list_sources()]

    def list_selection(self, select):
        """The plan open is chosen only while its view is shown: a document or a sheet chosen leaves no plan highlighted."""
        return super().list_selection(select) if self.view_kind == "plan" else None

    def show_empty_hint(self):
        self.empty_hint.setVisible(not self.ids and self.current_id is None and not self.dirty)

    def on_row_again(self, pid):
        """The plan open chosen again: the «Typst» view shows its command, any other view shows the plan."""
        if self.view_kind == "command":
            if pid != NEW_ROW:
                self.builder.set_plan(pid)
            return
        self.show_plan_view()

    def after_row_loaded(self, pid):
        """A plan chosen in the list: the «Typst» view's command is the plan's (load sets it), any other view goes to the drawing."""
        if self.view_kind != "command":
            self.show_plan_view()

    def open_plan(self, pid):
        """Plan `pid` open and shown -- a crop clicked in the document view (`planActivated`)."""
        if pid != self.current_id:
            if not self.leave_plan_for(pid):
                return
            self.load(pid)
        self.show_plan_view()

    def leave_plan_for(self, _pid):
        return self.confirm_leave()

    def text_properties(self, entry):
        """A text's pane (issue #43, UI-004): text_pane's, the four engines' one -- its content, «Insérer une variable», a card per variable. A change is one `edit`, one step of «Annuler»."""
        self.text_pane = text_pane.TextPane(entry, lambda: self.app, self.app.lang, self.edit, self.refresh_selection, self.text_values(),
                                            bool(getattr(self.app, "read_only", False)))
        self.selection_layout.addWidget(self.text_pane)

    def text_values(self):
        """The export's values a text of this drawing prints (issue #43): those read as it opened."""
        return getattr(self, "values", None) or {}

    def open_source(self, source, current_id, dirty):
        """Shows `source` -- read from its file, restored, or new -- with an empty undo history."""
        self.source = source
        self.current_id = current_id
        self.init_history()
        self.reset_drawing_state()
        # the export's values, which a text placed with the Text tool prints (issue #43): read as the drawing opens, as a linked field's are
        self.values = linkable_spin.current_values()
        self.canvas.values = self.values
        self.canvas.set_source(self.source, project.current().root, project.current())
        self.canvas.set_show_outside(self.show_outside_box.isChecked())
        self.fill()
        self.dirty = dirty
        self.loading = True
        self.on_changed()
        self.loading = False
        self.dirty = dirty
        self.revert_button.setEnabled(dirty)
        self.on_selection()

    def load(self, pid):
        path = self.sources_dir() / f"{pid}.json"
        try:
            source = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(source, dict):
                raise ValueError("not a JSON object")
            self.complete_source(source, pid)
        except (OSError, ValueError) as exc:
            notices_ui.tell(self.w("plan_unreadable", name=path.name, error=exc), notifications.CRITICAL, exc=exc, source="drawing_tab")
            source = self.blank_source(pid)
        self.open_source(source, pid, False)
        self.reload_list(select=pid)
        self.builder.set_plan(pid)

    def autosave(self, ask=True):
        """Leaving the plan open saves it, without a question (v0.114, the engineer's request): True where nothing is unsaved, or it was saved. Where it cannot be saved as it is -- a check of the domain refuses it, a rename to confirm -- the old question is asked (`ask`): save, discard or stay. A tab switch cannot be stayed in: there (`ask` False) the plan keeps its dot, and the status line says why."""
        if not self.dirty:
            return True
        if not getattr(self.app, "read_only", False) and self.save(quiet=True):
            return True
        if not ask:
            return False
        return self.ask_unsaved()

    def ask_unsaved(self):
        """The one question every editor asks where a draft cannot be saved as it is (autosave.confirm, v0.117): save, discard or stay."""
        return autosave.confirm(self.app, self, self.w("plan_unsaved_title"), self.w("plan_unsaved", id=self.id_edit.text().strip() or "?"),
                                discard=self._discard_draft)

    def _discard_draft(self):
        self.dirty = False
        if self.current_id is None:
            self.load_first()

    def confirm_leave(self):
        """True when the plan may be replaced: nothing unsaved, saved now (autosave), or the engineer saved or discarded it. The export of a layer switched is finished first -- the window closing asks this of every tab."""
        self.finish_layer_export()
        return self.autosave(ask=True)

    def load_first(self):
        listed = self.list_sources()
        if listed:
            self.load(listed[0][0])
        else:
            self.open_source(self.blank_source(self.free_id([])), None, False)
            self.reload_list(select=None)

    def taken_ids(self):
        return [pid for pid, _source, _group in self.list_sources()]

    def new(self):
        """A new plan, on an empty sheet (new_drawing_source) -- a plan on a document's page is made by ticking that page (on_page_toggled)."""
        if not self.confirm_leave():
            return
        source = self.new_drawing_source(self.free_id(self.taken_ids()))
        self.open_source(source, None, True)
        self.show_kind("plan")
        self.reload_list(select=NEW_ROW)

    def duplicate(self):
        if not self.confirm_leave():
            return
        source = copy.deepcopy(self.source)
        source["id"] = self.free_id(self.taken_ids())
        self.prepare_duplicate(source)
        self.open_source(source, None, True)
        self.show_kind("plan")
        self.reload_list(select=NEW_ROW)

    def revert(self):
        self.dirty = False
        if self.current_id is not None:
            self.load(self.current_id)
        else:
            self.load_first()

    # -- saving --

    def fail(self, text):
        notices_ui.tell(text, notifications.WARNING, title_key="plan_save_failed_title", source="drawing_tab")
        return False

    # -- surviving a rebuild --

    def view_state(self):
        """What a rebuild carries over -- after the plan open was saved, a language switch being a way of leaving it (autosave); a plan that cannot be saved travels as its draft, as before."""
        self.autosave(ask=False)
        state = {
            "draft": copy.deepcopy(self.source),
            "current_id": self.current_id,
            "dirty": self.dirty,
            "tool": self.canvas.tool,
            "splitter": self.splitter.sizes(),
            "left_boxes": {name: box.height_set for name, box in self.left_boxes.items()},
            "left_folded": self.left_folded,
            "left_sizes": self.left_sizes,
            "kind": self.view_kind,
            "document": self.doc_id,
            "sheet": self.sheet_id,
            "show_outside": self.show_outside_box.isChecked(),
        }
        state.update(self.drawing_view_state())
        return state

    def restore(self, state):
        if state:
            self.restore_drawing_before(state)
            self.show_outside_box.blockSignals(True)
            self.show_outside_box.setChecked(bool(state.get("show_outside")))
            self.show_outside_box.blockSignals(False)
            self.open_source(state["draft"], state.get("current_id"), state.get("dirty", False))
            self.restore_drawing_after(state)
            self.reload_list(select=self.current_id)
            if state.get("splitter"):
                self.splitter.setSizes(state["splitter"])
            for name, height in (state.get("left_boxes") or {}).items():   # absent from a state older than v0.117
                if name in self.left_boxes:
                    self.left_boxes[name].set_height(height)
            if state.get("left_folded"):
                self.set_left_folded(True)
                self.left_pane.sizes = state.get("left_sizes") or self.left_pane.sizes
            self.choose_tool(state.get("tool", "select"))
            kind = state.get("kind", "plan")
            if kind == "document" and state.get("document") in self.documents:
                self.open_document(state["document"])
            elif kind == "sheet" and state.get("sheet") in sheets.list_sheets(project.current(), kind=self.SHEET_KIND):
                self.open_sheet(state["sheet"])
            elif kind == "command":
                self.open_builder()
            else:
                self.show_plan_view()
        else:
            self.splitter.setSizes([1600, 7000, 3000])
            self.load_first()
            self.choose_tool("select")
            self.show_plan_view()
