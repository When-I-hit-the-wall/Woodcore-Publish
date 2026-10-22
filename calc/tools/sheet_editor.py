"""The export sheet editor (v0.114): an export sheet -- `Plans/<id>.typ`, calc/sheets.py -- shown as Typst compiles it, its objects framed over the page to be chosen, dragged and resized, and their options in cards beside it. Three parts the plan tab places in its three panes: `SheetCanvas` (the centre), `SheetOptions` (the right pane) and `SheetEditor`, the controller that owns both and the sheet they show.

**The .typ is the source of truth.** Every change -- a frame dragged, a scale chosen, a cell of the title block typed -- is written between the object's two tags through calc/typst_objects.py's canonical form (calc/sheets.py), and nothing else of the file moves; an object written by hand in another form is rewritten only once the caller's `ask(question)` has said yes. What the engineer writes in VS Code is read back: the file is watched while the editor is shown (`start` / `stop`) and read again where its signature -- size, time written and SHA-256 -- is not the one this editor last wrote or read.

**The page is the compiled sheet.** A change asks for a compile 300 ms later (three changes in a row are one compile, the newest wins): `typst compile` into Woodcore's cache (`usersettings.cache_dir("sheets")`, never `Plans/<id>.pdf`, which is the deliverable and only `export_pdf` writes) and, beside it, `typst eval` of the boxes every command of lib/sheet.typ emits as metadata (`<woodcore-sheet-box>`: its kind and the box it takes on the paper in millimetres) -- which is what the frames over the page are drawn from, exactly where Typst put the object. Both run off the main thread, through calc/proc.py (no console window). The PDF is read into memory and shown from a buffer, never opened as a file, so nothing holds a handle the next compile would trip on. A sheet that does not compile says Typst's own words in a banner and the last page stays shown; where the boxes cannot be queried they are estimated from the file (`estimate_boxes`).

**The right pane follows what is chosen** (v0.116): nothing chosen, the sheet's own modules -- «Feuille» and «Options», which put the title block and the legend on and off and add a plan view, a section, a text or the list of the positions --; an object chosen, its own module alone. **A sheet is of one kind**, position plans or fire-protection plans (calc/sheets.py), and the editor offers the objects of that kind alone.

**Resizing a plan or a section changes its scale** where its plan is calibrated -- continuously while the frame is dragged, rounded to a whole 1:n when it is let go -- and its width otherwise.

The window's words are this module's STRINGS, keys `se_`, in French, German and English.
"""

import hashlib
import json
import math
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

import shiboken6

from PySide6.QtCore import QBuffer, QByteArray, QFileSystemWatcher, QIODevice, QObject, QPointF, QRect, QRectF, QSize, QThread, QTimer, Qt, Signal
from PySide6.QtGui import QColor, QImage, QPainter, QPen
from PySide6.QtPdf import QPdfDocument, QPdfDocumentRenderOptions, QPdfPageRenderer
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDoubleSpinBox, QHBoxLayout, QInputDialog, QLabel, QLineEdit, QMessageBox,
                               QPlainTextEdit, QPushButton, QScrollArea, QToolButton, QVBoxLayout, QWidget)

import cards
import flowbar
import proc
import project
import sheets
import theme
import typst_objects as to
import usersettings
import tasks  # what runs in the background, said by the chip at the top right (tasks.activity, v0.117)
from sheet_editor_words import BUNDLE_KEYS, STRINGS, bundle_words, words  # split out of this module (issue #30): every name it had is still importable from it
from sheet_editor_render import (  # split out of this module (issue #30): every name it had is still importable from it
    BOX_LABEL,
    BOX_QUERY,
    Box,
    COMPILE_TIMEOUT_S,
    Compiler,
    DEBOUNCE_MS,
    DRAWING_KINDS,
    LEGEND_KINDS,
    RESIZABLE_KINDS,
    SNAP_MM,
    TITLE_MM,
    _Job,
    _RUNNING,
    _count_positions,
    _objects,
    _position,
    cache_target,
    drawing_width,
    estimate_boxes,
    file_signature,
    markup_of,
    match_boxes,
    parse_boxes,
    parse_scale,
    query_args,
    read_fire_plans,
    read_plans,
    render,
    scale_for,
    snap,
    units_per_m,
)
from sheet_editor_canvas import HANDLE, PAD, RENDER_MARGIN, RENDER_MAX_PX, RENDER_SETTLE_MS, SheetCanvas, ZOOM_MAX, ZOOM_MIN, ZOOM_STEP, _Page  # split out of this module (issue #30): every name it had is still importable from it
from sheet_editor_options import AUTO_CELLS, CELLS, PHASES, SCALES, SheetOptions, TYPING_MS, _Blocked, _spin  # split out of this module (issue #30): every name it had is still importable from it


# The sentence each refusal is said with, by its code (calc/sheets.py's, typst_objects' ObjectError and ModelError codes): what has none is said with `se_why_other`.
WHY = {
    "bad_id": "se_why_bad_id", "exists": "se_why_exists", "no_sheet": "se_why_no_sheet", "no_page": "se_why_no_page",
    "bad_format": "se_why_bad_format", "bad_object": "se_why_bad_object", "no_such_object": "se_why_bad_object",
    "write_failed": "se_why_write_failed", "changed": "se_why_changed", "tags": "se_why_tags", "bad_value": "se_why_bad_value",
    "not_editable": "se_why_not_editable", "unreadable": "se_why_unreadable",
    # v0.116: a sheet's kind, and the PDF bundles
    "bad_kind": "se_why_bad_kind", "wrong_kind": "se_why_wrong_kind", "bad_bundles": "se_why_bad_bundles", "bad_bundle_name": "se_why_bad_bundle_name",
    "bundle_exists": "se_why_bundle_exists", "no_bundle": "se_why_no_bundle", "missing_sheet": "se_why_missing_sheet",
}


# --- the boxes of a sheet's objects (Qt-free) ------------------------------------------------------


# --- running the compile off the main thread ---------------------------------------------------


# --- the canvas ----------------------------------------------------------------------------------


# --- the options -----------------------------------------------------------------------------------


# --- the controller --------------------------------------------------------------------------------

class SheetEditor(QObject):
    """The sheet editor: owns the canvas (`canvas`) and the options (`options`) of the sheet open, writes every change into its .typ through calc/sheets.py, compiles what is shown and watches the file while it is shown (`start` / `stop`). `changed(sheet_id)` after every change it writes and every change read back from disk; `exportRequested` when the options' «Exporter le PDF» is clicked -- answered by `export_pdf` unless `auto_export` is false, the caller then answering it. `ask(question) -> bool` is asked before an object written by hand is rewritten (a message box where none is given)."""

    changed = Signal(str)
    exportRequested = Signal()

    def __init__(self, parent=None, lang="en", ask=None, auto_export=True, kind=None, choose=None):
        super().__init__(parent)
        self.lang = lang
        # the kind of sheet the tab makes ("position", "fire"), what a sheet of no readable kind is taken for -- an open sheet's own kind is read off its file (sheets.kind_of_text)
        self.kind = kind
        # choose(question, [(label, value)]) -> value or None: which plan to add (a list in a dialog where none is given; a test answers it)
        self.choose = choose or self._choose_dialog
        self.here = None
        self.sheet_id = None
        self.signature = None
        self.selected = ""
        self.watcher = None
        self.watching = False
        self.ask = ask or self._ask_box
        self.last_result = None
        self.preview_folder = None      # where the previews are compiled, Woodcore's cache where None -- a test's own folder
        self.compiler = Compiler(self, self._shown)
        self.external_timer = QTimer(self)
        self.external_timer.setSingleShot(True)
        self.external_timer.setInterval(250)
        self.external_timer.timeout.connect(self.reload_external)
        self.canvas = SheetCanvas(lang=lang)
        self.canvas.scale_label = self._scale_label
        self.options = SheetOptions(self, lang=lang)
        self.canvas.selectionChanged.connect(self._canvas_selected)
        self.canvas.moveRequested.connect(self.move)
        self.canvas.resizeRequested.connect(self.resize_object)
        if auto_export:
            self.exportRequested.connect(self._export_clicked)
        self.options.load()

    def t(self, key, **values):
        return words(self.lang, key, **values)

    def set_language(self, lang):
        self.lang = lang
        self.canvas.set_language(lang)
        self.options.set_language(lang)

    def _ask_box(self, question):
        answer = QMessageBox.question(self.canvas.window(), "Woodcore", question)
        return answer == QMessageBox.StandardButton.Yes

    def _choose_dialog(self, question, items):
        labels = [label for label, _value in items]
        label, ok = QInputDialog.getItem(self.canvas.window(), "Woodcore", question, labels, 0, False)
        if not ok or label not in labels:
            return None
        return items[labels.index(label)][1]

    def sheet_kind(self):
        """The kind of the sheet open -- what its page says, else what its objects say (calc/sheets.declared_kind) --, the tab's own where none is open or the sheet says nothing yet."""
        text = self.text()
        if text is not None:
            try:
                found = sheets.declared_kind(text)
            except ValueError:       # a file whose tags cannot be read (typst_objects.ParseError): the tab's kind
                found = None
            if found is not None:
                return found
        return self.kind or "position"

    def sheet_lang(self):
        """The language the sheet's words are printed in (the project's documents'), the window's where there is no project."""
        return sheets.language(self.here) if self.here is not None else self.lang

    # -- the sheet open ----------------------------------------------------------------------

    def set_project(self, here):
        """Works on project `here` (a project.Project); the sheet open, if any, is closed."""
        self.here = here
        self.close_sheet()

    def close_sheet(self):
        self.stop_watching_file()
        self.sheet_id = None
        self.selected = ""
        self.signature = None
        self.canvas.set_boxes([])
        self.canvas.clear_page()
        self.canvas.say("")
        self.options.load()

    def open(self, sheet_id):
        """Opens sheet `sheet_id` of the project: its page shown (estimated at once, compiled a moment later) and its options filled."""
        self.options.flush()
        sheets.read(self.here, sheet_id)        # a SheetError where there is none
        self.sheet_id = sheet_id
        self.selected = ""
        self.signature = file_signature(sheets.path(self.here, sheet_id))
        self.last_result = None
        self.canvas.clear_page()
        self.canvas.select("")
        self.canvas.say("")
        self._refresh(compile_now=True)
        if self.watching:
            self._watch_paths()

    def _refresh(self, compile_now=False):
        """The page size and the estimated boxes from the file at once, the options filled, and a compile asked for."""
        text = self.text()
        if text is None:
            return
        page = self.page_model(text)
        if page is not None:
            self.canvas.set_page_size(*page.size())
        if not self.canvas.has_page() or self.last_result is None:
            self.canvas.set_boxes(estimate_boxes(self.here, text))
        self.options.load()
        self.compiler.request(self.here, self.sheet_id, now=compile_now)

    def text(self):
        if self.here is None or self.sheet_id is None:
            return None
        try:
            return sheets.read(self.here, self.sheet_id)
        except sheets.SheetError:
            return None

    def objects(self):
        text = self.text()
        return _objects(text) if text is not None else []

    def page_model(self, text=None):
        text = self.text() if text is None else text
        if text is None:
            return None
        obj = next((o for o in to.objects(text) if o.type == "sheet-page"), None)
        try:
            return obj.model() if obj is not None else None
        except to.ModelError:
            return None

    def selected_object(self):
        if not self.selected:
            return None, None
        return next(((o, m) for o, m in self.objects() if o.id == self.selected), (None, None))

    def plans(self):
        return read_plans(self.here) if self.here is not None else {}

    def plans_for(self, kind):
        """The plans an object of `kind` is drawn from: the fire-protection plans for a fire viewport, the position plans for the others."""
        if kind == "sheet-fire-viewport":
            return read_fire_plans(self.here) if self.here is not None else {}
        return self.plans()

    def positions_of_plan(self, plan):
        """The positions plan `plan` shows, by their numbers (data/plans.json's `labels`): what its viewport may highlight."""
        record = self.plans().get(plan or "", {})
        labels = record.get("labels") if isinstance(record, dict) else None
        return [label for label in labels if isinstance(label, str)] if isinstance(labels, list) else []

    def storeys(self):
        """The storeys' numbering characters the project's positions carry -- the id's second letter, «0» for T001 --, in order: what a position list may be limited to."""
        try:
            found = json.loads((Path(self.here.data_dir) / "positions-index.json").read_text(encoding="utf-8")).get("positions")
        except (OSError, ValueError, AttributeError):
            return []
        out = []
        for pid in found if isinstance(found, list) else []:
            if isinstance(pid, str) and len(pid) > 1 and pid[1] not in out:
                out.append(pid[1])
        return out

    def select(self, object_id):
        self.canvas.select(object_id)
        if self.selected != (object_id or ""):
            self._canvas_selected(object_id or "")

    def _canvas_selected(self, object_id):
        self.options.flush()
        self.selected = object_id or ""
        self.options.load()

    # -- the compile ---------------------------------------------------------------------------

    def _shown(self, result):
        if self.here is None or self.sheet_id is None:
            return
        self.last_result = result
        text = result.get("text") or self.text() or ""
        if result.get("ok") and result.get("pdf"):
            self.canvas.load_pdf(result["pdf"])
            self.canvas.say("")
        elif result.get("message"):
            self.canvas.say(self.t("se_typst_failed", message=result["message"]))
        raw = result.get("boxes")
        if raw is not None:
            self.canvas.set_boxes(match_boxes(text, raw))
        elif result.get("ok") or not self.canvas.boxes:
            self.canvas.set_boxes(estimate_boxes(self.here, text))
        self._load_options_when_no_list_is_open()

    def _load_options_when_no_list_is_open(self):
        """The right pane made again once none of its lists is open: a compile that ends while the scale's list is open made the pane again under it and closed it at once -- the engineer's «s'ouvre et se ferme instantanément» of 07.10.2026 reached another way than by `edit` (issue #24)."""
        if not shiboken6.isValid(self.options):
            return
        popup = QApplication.activePopupWidget()
        while popup is not None and popup is not self.options:
            popup = popup.parentWidget()
        if popup is self.options:
            QTimer.singleShot(200, self, self._load_options_when_no_list_is_open)
            return
        self.options.load()

    def wait(self, timeout=60):
        """Holds until the compile asked for has been shown -- for a test; the window never waits."""
        import time
        from PySide6.QtCore import QEventLoop
        from PySide6.QtWidgets import QApplication
        end = time.monotonic() + timeout
        app = QApplication.instance()
        while self.compiler.busy():
            if time.monotonic() > end:
                raise TimeoutError("the sheet was not compiled in time")
            app.processEvents(QEventLoop.ProcessEventsFlag.AllEvents, 50)
            time.sleep(0.01)

    def export_pdf(self):
        """Compiles the sheet into `Plans/<id>.pdf`, beside its .typ (calc/sheets.py). Gives back (ok, message): Typst's own words where it does not compile."""
        if self.here is None or self.sheet_id is None or self.refused_read_only():
            return False, ""
        self.options.flush()
        return sheets.compile(self.here, self.sheet_id)

    def _export_clicked(self):
        ok, message = self.export_pdf()
        if ok:
            self.canvas.say(self.t("se_exported", file=sheets.pdf(self.here, self.sheet_id).name), "info")
        elif message:
            self.canvas.say(self.t("se_typst_failed", message=message))

    # -- writing -----------------------------------------------------------------------------

    def refused_read_only(self):
        """True, and said, where the window holds its project read-only (project_lock.py): nothing of the sheet is written and its PDF is not compiled. Asked here and not through woodcore_gui.WRITERS, which wraps methods by name on the tabs -- `edit` is also the tabs' own edit of a draft, which a read-only project keeps (v0.116, WP-K). What the canvas or a switch already shows is put back: the options read again and the page compiled again from the file."""
        app = getattr(self.parent(), "app", None)
        if not getattr(app, "read_only", False):
            return False
        app.refuse_read_only()
        if self.here is not None and self.sheet_id is not None:
            QTimer.singleShot(0, lambda: self.options.load() if shiboken6.isValid(self.options) else None)
            self.compiler.request(self.here, self.sheet_id)
        return True

    def refuse(self, exc):
        """A refusal said in the banner, in the window's words by its code."""
        code = getattr(exc, "code", "")
        values = dict(getattr(exc, "values", {}) or {})
        values.setdefault("id", self.sheet_id or "")
        values["message"] = str(exc)
        key = WHY.get(code, "se_why_other")
        try:
            text = self.t(key, **values)
        except (KeyError, IndexError):
            text = self.t("se_why_other", message=str(exc))
        self.canvas.say(text)

    def _wrote(self, reload_options=True):
        self.signature = file_signature(sheets.path(self.here, self.sheet_id))
        if reload_options:
            # after the signal that asked for the change has returned: the card may be made again under the widget that sent it
            QTimer.singleShot(0, lambda: self.options.load() if shiboken6.isValid(self.options) else None)
        self.compiler.request(self.here, self.sheet_id)
        self.changed.emit(self.sheet_id)

    def edit(self, object_id, change, reload_options=True):
        """One object's model read from the file, `change(model)` applied and written back between its tags -- an object written by hand in another form rewritten only once `ask` says yes. True where the change was taken, written or already in the file.

        A change that leaves the file as it is writes nothing and rebuilds nothing (v0.117): a field's `editingFinished` fires whenever it loses the focus -- the scale's own list opening takes it -- and the right pane made again under an open list closed it at once (the engineer, 07.10.2026: «le menu déroulant s'ouvre et se ferme instantanément»)."""
        if self.here is None or self.sheet_id is None or self.refused_read_only():
            return False
        try:
            text = sheets.read(self.here, self.sheet_id)
            obj = to.find(text, object_id)
            if obj is None:
                raise sheets.SheetError("bad_object", f"sheet {self.sheet_id!r} holds no object {object_id!r}", id=self.sheet_id, object=object_id)
            model = obj.model()
            change(model)
            try:
                new = to.write_object(text, object_id, model.to_call())
            except to.ObjectError as exc:
                if exc.code not in ("hand_edited", "unreadable"):
                    raise
                if not self.ask(self.t("se_ask_rewrite", object=object_id, diff=obj.diff())):
                    return False
                new = to.write_object(text, object_id, model.to_call(), force=True)
            if new == text:
                return True
            sheets.write(self.here, self.sheet_id, new)
        except (sheets.SheetError, to.ObjectError, to.ModelError) as exc:
            self.refuse(exc)
            return False
        self._wrote(reload_options)
        return True

    def _call(self, action, *args, **kwargs):
        """A function of calc/sheets.py run on the sheet open, its refusal said; what it gave back, or None where it refused."""
        if self.here is None or self.sheet_id is None or self.refused_read_only():
            return None
        try:
            result = action(self.here, self.sheet_id, *args, **kwargs)
        except (sheets.SheetError, to.ObjectError, to.ModelError) as exc:
            self.refuse(exc)
            return None
        self._wrote()
        return result

    def move(self, object_id, x, y):
        """Moves an object's top-left corner to (x, y) millimetres -- what dragging its frame writes."""
        box = self.canvas.box(object_id)
        if box is not None:
            box.x, box.y = x, y
        return self.edit(object_id, lambda m: m.move_to(x, y))

    def resize_object(self, object_id, factor):
        """A plan or a section made `factor` times as large: its scale where its plan is calibrated, rounded to a whole 1:n, its width otherwise."""
        box = self.canvas.box(object_id)
        obj, model = next(((o, m) for o, m in self.objects() if o.id == object_id), (None, None))
        if obj is not None and obj.type in LEGEND_KINDS + ("sheet-position-list", "sheet-quantities"):
            # a legend or a list of the positions: its width, in millimetres, its height following its lines at the next compile
            width = to.mm_of(model.get("width")) or (box.w if box is not None else None)
            if not width:
                return False
            if box is not None:
                box.w, box.h = box.w * factor, box.h * factor
            return self.edit(object_id, lambda m: m.set_width(round(max(10.0, width * factor), 1)))
        if obj is None or not isinstance(model, to._Drawing):
            return False
        plan = self.plans_for(model.type).get(model.get("plan") or "", {})
        width = drawing_width(plan, model) or (box.dw if box is not None else None) or (box.w if box is not None else None)
        if not width:
            return False
        new_width = width * factor
        n = scale_for(plan, new_width)
        if box is not None:     # the frame stays where it was let go until the compile says where Typst put it
            box.w, box.h = box.w * factor, box.h * factor
            box.dw = new_width
        if n is not None:
            return self.edit(object_id, lambda m: m.set_scale(max(1, int(round(n)))))
        return self.edit(object_id, lambda m: m.set_width(round(new_width, 1)))

    def _scale_label(self, box, factor):
        obj, model = next(((o, m) for o, m in self.objects() if o.id == box.id), (None, None))
        if not isinstance(model, to._Drawing):
            return ""
        plan = self.plans_for(model.type).get(model.get("plan") or "", {})
        width = (box.dw or drawing_width(plan, model) or box.w) * factor
        n = scale_for(plan, width)
        return f"1:{n:.0f}" if n is not None else f"{width:.0f} mm"

    def set_page(self, format=None, landscape=None, margin=None):
        text = self.text()
        page = next((o for o in to.objects(text) if o.type == "sheet-page"), None) if text is not None else None
        if page is None:
            return self.refuse(sheets.SheetError("no_page", "the sheet has no page", id=self.sheet_id))

        def change(m):
            if format is not None:
                m.set_format(format)
            if landscape is not None:
                m.set_landscape(bool(landscape))
            if margin is not None:
                m.set_margin(margin)
        if self.edit(page.id, change):
            model = self.page_model()
            if model is not None:
                self.canvas.set_page_size(*model.size())

    def set_plan(self, object_id, plan):
        return self.edit(object_id, lambda m: m.set_plan(plan))

    def set_storey(self, object_id, storey):
        return self.edit(object_id, lambda m: m.set_storey(storey))

    def set_scale(self, object_id, n):
        if n is None:
            return False
        return self.edit(object_id, lambda m: m.set_scale(n))

    def set_width(self, object_id, width):
        if not width or width <= 0:
            return False
        return self.edit(object_id, lambda m: m.set_width(round(width, 1)))

    def set_viewport_title(self, object_id, on):
        """The line above a plan on or off: on, «Nom — description, étage (éch. 1:n)» from the plan (auto); off, none."""
        return self.edit(object_id, lambda m: m.set_title(to.AUTO if on else None))

    def set_highlight(self, object_id, text):
        found = [part.strip() for part in (text or "").split(",") if part.strip()]
        value = None if not found else found[0] if len(found) == 1 else found
        return self.edit(object_id, lambda m: m.set_highlight(value))

    def set_flag(self, object_id, argument, on):
        def change(m):
            if argument == "axes":
                m.set_axes(on)
            elif argument == "dimensions":
                m.set_dimensions(on)
            elif argument == "lengths":
                m.set_lengths(on)
            elif argument == "centres":
                m.set_centres(on)   # the stiffness centre, the mass centre and the outline (issue #54)
            elif argument == "legend":
                m.set_legend(on)
            else:
                m.set_scale_bar(on)
        return self.edit(object_id, change)

    def set_body(self, object_id, markup):
        try:
            body = to.Content(markup)
        except ValueError as exc:
            return self.refuse(to.ModelError("bad_value", str(exc)))
        return self.edit(object_id, lambda m: m.set_body(body), reload_options=False)

    def set_text_size(self, object_id, size):
        return self.edit(object_id, lambda m: m.set_size(to.Length(round(float(size), 1), "pt")), reload_options=False)

    def set_bold(self, object_id, on):
        return self.edit(object_id, lambda m: m.set_weight("bold" if on else "regular"), reload_options=False)

    def set_legend_width(self, object_id, width):
        return self.edit(object_id, lambda m: m.set_width(round(width, 1)))

    def set_legend_title(self, object_id, title):
        return self.edit(object_id, lambda m: m.set_title(to.AUTO if not title.strip() else to.Content(title)))

    def titleblock_to_corner(self, object_id):
        return self.edit(object_id, lambda m: m.move_to(to.AUTO, to.AUTO))

    def set_cell(self, name, text):
        """One cell of the title block: empty is the project's value where the cell has one (auto) and an empty cell otherwise; anything else the engineer's words, as markup."""
        block = next((o for o, _m in self.objects() if o.type == "sheet-titleblock"), None)
        if block is None:
            return False
        text = (text or "").strip()
        current = next((m for o, m in self.objects() if o.id == block.id), None)
        if current is not None and markup_of(current.get(name)) == text:
            return False        # nothing changed: a field left is no edit
        if not text:
            value = to.AUTO if name in AUTO_CELLS else None
        else:
            try:
                value = to.Content(text)
            except ValueError as exc:
                return self.refuse(to.ModelError("bad_value", str(exc)))
        return self.edit(block.id, lambda m: m.set_cell(name, value), reload_options=False)

    # -- objects added and taken away --------------------------------------------------------

    def _free_spot(self):
        page = self.page_model()
        width, height = page.size() if page is not None else (420, 297)
        return width, height

    def add_viewport(self, plan=None):
        """A plan of the project put on the sheet: the first that is not a section where none is named, at 1:100 where it is calibrated and 150 mm wide otherwise."""
        plans = self.plans()
        if plan is None:
            plan = next((pid for pid, p in plans.items() if not isinstance(p, dict) or p.get("role", "plan") != "section"), None)
        calibrated = units_per_m(plans.get(plan or "", {})) is not None
        width, _height = self._free_spot()
        new = self._call(sheets.add_viewport, plan, 20, 30, scale=100 if calibrated else None,
                         width=None if calibrated else min(150, width - 40)) if plan else None
        if new is None and not plan:
            new = self._call(sheets.add_object, "sheet-viewport", to.Call("sheet-viewport", {"x": to.Length(20, "mm"), "y": to.Length(30, "mm")}), base="viewport")
        return new

    def add_fire_viewport(self, plan=None):
        """A fire-protection plan of the project put on the sheet: the first there is where none is named, at 1:100 where it is calibrated and 150 mm wide otherwise."""
        plans = read_fire_plans(self.here) if self.here is not None else {}
        if plan is None:
            plan = next(iter(plans), None)
        calibrated = units_per_m(plans.get(plan or "", {})) is not None
        width, _height = self._free_spot()
        new = self._call(sheets.add_fire_viewport, plan, 20, 30, scale=100 if calibrated else None,
                         width=None if calibrated else min(150, width - 40)) if plan else None
        if new is None and not plan:
            new = self._call(sheets.add_object, "sheet-fire-viewport", to.Call("sheet-fire-viewport", {"x": to.Length(20, "mm"), "y": to.Length(30, "mm")}), base="fire")
        return new

    def add_section(self, plan=None):
        """A section plan put on the sheet, top right, its first storey highlighted."""
        plans = self.plans()
        if plan is None:
            plan = next((pid for pid, p in plans.items() if isinstance(p, dict) and p.get("role") == "section"), None)
        width, _height = self._free_spot()
        x = max(20, width - 20 - 80)
        if plan:
            record = plans.get(plan, {})
            boxes = record.get("storey_boxes") or []
            storey = next((b.get("storey") for b in boxes if isinstance(b, dict) and isinstance(b.get("storey"), str)), None)
            calibrated = units_per_m(record) is not None
            new = self._call(sheets.add_section, plan, storey, x, 30, scale=200 if calibrated else None, width=None if calibrated else 60)
        else:
            new = self._call(sheets.add_object, "sheet-section", to.Call("sheet-section", {"x": to.Length(x, "mm"), "y": to.Length(30, "mm"), "width": to.Length(60, "mm")}), base="section")
        return new

    def add_text(self):
        """A text put on the sheet, still to be written -- not chosen: its options show once it is clicked."""
        return self._call(sheets.add_text, 20, 40, to.PLACEHOLDER)

    def add_quantities(self):
        """The quantities put on the sheet, top right, those of the sheet's plans (issue #9)."""
        width, _height = self._free_spot()
        table_width = min(150, width - 40)
        return self._call(sheets.add_quantities, max(20, width - 20 - table_width), 30, width=table_width)

    def add_position_list(self):
        """The list of the positions put on the sheet, top right, listing the positions of the sheet's plans (v0.116)."""
        width, _height = self._free_spot()
        list_width = min(180, width - 40)
        return self._call(sheets.add_position_list, max(20, width - 20 - list_width), 30, width=list_width)

    def _chosen(self, question, plans, keep):
        """A plan of `plans` (those `keep(record)` keeps) chosen with `choose`; None where there is none or nothing was chosen -- said in the banner where there is none."""
        items = [(f"{pid} — {p.get('label')}" if isinstance(p, dict) and p.get("label") else pid, pid)
                 for pid, p in plans.items() if keep(p if isinstance(p, dict) else {})]
        if not items:
            self.canvas.say(self.t("se_no_plans"), "info")
            return None
        return self.choose(self.t(question), items)

    def add_viewport_chosen(self):
        """«Ajouter une vue en plan»: the position plan chosen in a list -- every one but the sections -- put on the sheet."""
        plan = self._chosen("se_choose_plan", self.plans(), lambda p: p.get("role", "plan") != "section")
        return self.add_viewport(plan) if plan else None

    def add_fire_viewport_chosen(self):
        """«Ajouter un plan de protection incendie»: the fire-protection plan chosen in a list put on a fire sheet."""
        plan = self._chosen("se_choose_fire", self.plans_for("sheet-fire-viewport"), lambda p: True)
        return self.add_fire_viewport(plan) if plan else None

    def add_section_chosen(self):
        """«Ajouter une coupe schématique»: the section plan chosen in a list put on the sheet."""
        plan = self._chosen("se_choose_section", self.plans(), lambda p: p.get("role") == "section")
        return self.add_section(plan) if plan else None

    def remove_selected(self):
        if not self.selected:
            return False
        object_id = self.selected
        self.select("")
        self._call(sheets.remove, object_id)
        text = self.text()
        return text is not None and to.find(text, object_id) is None

    def set_titleblock(self, on):
        """The title block put on the sheet, bottom right, or taken off."""
        found = [o for o, _m in self.objects() if o.type == "sheet-titleblock"]
        if on and not found:
            self._call(sheets.add_object, "sheet-titleblock", to.Call("sheet-titleblock", {"plan-number": self.sheet_id}), object_id=None, base="titleblock")
        elif not on:
            for obj in found:
                if self.selected == obj.id:
                    self.select("")
                self._call(sheets.remove, obj.id)

    def set_legend(self, on):
        """The legend of the sheet's plans put on it, top right, or taken off."""
        found = [o for o, _m in self.objects() if o.type == "sheet-legend"]
        if on and not found:
            width, _height = self._free_spot()
            legend_width = min(120, width - 40)
            self._call(sheets.add_legend, max(20, width - 20 - legend_width), 30, width=legend_width)
        elif not on:
            for obj in found:
                if self.selected == obj.id:
                    self.select("")
                self._call(sheets.remove, obj.id)

    def set_sheet_legend(self, on):
        """The switch «Afficher la légende»: the legend of the sheet's kind -- the position plans', or the fire plans' on a fire sheet."""
        return self.set_fire_legend(on) if self.sheet_kind() == "fire" else self.set_legend(on)

    def set_fire_legend(self, on):
        """The legend of the sheet's fire-protection plans put on it, a block of its own beside the plans' legend, or taken off."""
        found = [o for o, _m in self.objects() if o.type == "sheet-fire-legend"]
        if on and not found:
            width, _height = self._free_spot()
            legend_width = min(120, width - 40)
            self._call(sheets.add_fire_legend, max(20, width - 20 - legend_width), 80, width=legend_width)
        elif not on:
            for obj in found:
                if self.selected == obj.id:
                    self.select("")
                self._call(sheets.remove, obj.id)

    # -- the file watched -------------------------------------------------------------------

    def start(self):
        """Watches the open sheet's file from now until `stop`: a change made elsewhere -- VS Code -- is read back. Made when the editor is shown and not before: a watch holds the folder on Windows."""
        self.watching = True
        if self.watcher is None:
            self.watcher = QFileSystemWatcher(self)
            self.watcher.fileChanged.connect(self._files_changed)
            self.watcher.directoryChanged.connect(self._files_changed)
        self._watch_paths()

    def stop(self):
        """Nothing watched any more."""
        self.watching = False
        self.stop_watching_file()
        self.options.flush()

    def stop_watching_file(self):
        if self.watcher is not None:
            held = self.watcher.files() + self.watcher.directories()
            if held:
                self.watcher.removePaths(held)
        self.external_timer.stop()

    def _watch_paths(self):
        if self.watcher is None or self.here is None or self.sheet_id is None:
            return
        wanted = [str(sheets.path(self.here, self.sheet_id)), str(sheets.path(self.here, self.sheet_id).parent)]
        have = set(self.watcher.files()) | set(self.watcher.directories())
        missing = [p for p in wanted if p not in have and Path(p).exists()]
        if missing:
            self.watcher.addPaths(missing)

    def _files_changed(self, _path=""):
        if shiboken6.isValid(self):
            self.external_timer.start()

    def reload_external(self):
        """The sheet read again where its file is not what this editor last wrote or read -- True where it was."""
        if self.here is None or self.sheet_id is None:
            return False
        self._watch_paths()
        signature = file_signature(sheets.path(self.here, self.sheet_id))
        if signature is None or signature == self.signature:
            return False
        self.signature = signature
        if self.selected and not any(o.id == self.selected for o, _m in self.objects()):
            self.select("")
        self._refresh()
        self.canvas.say(self.t("se_reloaded"), "info")
        self.changed.emit(self.sheet_id)
        return True
