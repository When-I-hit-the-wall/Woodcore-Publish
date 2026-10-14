"""An export sheet compiled and measured -- the boxes Typst reports for its objects, matched to them and estimated before it answers, the plans and their scales, the compiler that runs Typst in the background -- split out of calc/tools/sheet_editor.py (issue #30), moved verbatim. sheet_editor.py imports every name back.
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
import proc
import project
import sheets
import typst_objects as to
import usersettings
import tasks  # what runs in the background, said by the chip at the top right (tasks.activity, v0.117)


# How long a change waits for the next before the sheet is compiled: three edits in a row are one compile.
DEBOUNCE_MS = 300


# A compile still running after this long is given up: Typst caught in a loop must not leave the canvas waiting for ever.
COMPILE_TIMEOUT_S = 300


# The query that gives back every box lib/sheet.typ's commands emit, in document order.
BOX_LABEL = "woodcore-sheet-box"


BOX_QUERY = f"query(<{BOX_LABEL}>).map(it => it.value)"


# Where a frame dropped or resized lands: the nearest half millimetre.
SNAP_MM = 0.5


# The objects that print a plan at a scale -- a position plan, a section, a fire-protection plan (v0.115) -- and the legends.
DRAWING_KINDS = ("sheet-viewport", "sheet-section", "sheet-fire-viewport")


LEGEND_KINDS = ("sheet-legend", "sheet-fire-legend")


# What a handle resizes on the sheet: a drawing (its scale, or its width), and since v0.117 a legend and a list of the positions -- their width, their height following their lines (the engineer, 07.10.2026: «il faut pouvoir redimensionner les liste de positions à l'aide de la souris»).
RESIZABLE_KINDS = DRAWING_KINDS + LEGEND_KINDS + ("sheet-position-list", "sheet-quantities")


# The height a plan's title takes above it, in millimetres (lib/sheet.typ's sheet-plan-title, 10pt, and the stack's 2 mm): what an estimated box adds.
TITLE_MM = 6.5


@dataclass
class Box:
    """Where one object of the sheet stands on the paper, in millimetres from its top-left corner: its id and kind (the tag's), the box (`x`, `y`, `w`, `h`), and for a plan or a section `dw`, the width its drawing is printed at, and `n`, its scale 1:n where it has one. `estimated` where the box was worked out in Python rather than read from what Typst laid out."""
    id: str
    kind: str
    x: float
    y: float
    w: float
    h: float
    dw: float = None
    n: float = None
    estimated: bool = False

    def contains(self, x, y):
        return self.x <= x <= self.x + self.w and self.y <= y <= self.y + self.h

    @property
    def resizable(self):
        return self.kind in RESIZABLE_KINDS


def query_args(here, sheet_id):
    """`typst eval`'s arguments that give back the boxes of sheet `sheet_id`, the executable left out."""
    return ["eval", BOX_QUERY, "--in", str(sheets.path(here, sheet_id)), "--root", str(Path(here.typst_root))]


def parse_boxes(output):
    """The boxes `typst eval` printed: a list of dictionaries, each with at least a kind and four numbers; None where the output is not that."""
    try:
        found = json.loads(output)
    except (TypeError, ValueError):
        return None
    if not isinstance(found, list):
        return None
    out = []
    for item in found:
        if not isinstance(item, dict) or not isinstance(item.get("kind"), str):
            return None
        try:
            values = [float(item[k]) for k in ("x", "y", "w", "h")]
        except (KeyError, TypeError, ValueError):
            return None
        if not all(math.isfinite(v) for v in values):
            return None
        out.append(item)
    return out


def _objects(text):
    """The placed objects of a sheet's text -- every object but the page -- with their models where they can be read."""
    out = []
    for obj in to.objects(text):
        if obj.type == "sheet-page" or obj.type not in to.SHEET_TYPES:
            continue
        try:
            model = obj.model()
        except to.ModelError:
            model = None
        out.append((obj, model))
    return out


def _position(model):
    if model is None:
        return None, None
    try:
        return to.mm_of(model.get("x")), to.mm_of(model.get("y"))
    except to.ModelError:
        return None, None


def match_boxes(text, raw):
    """The boxes `raw` (as `parse_boxes` gives them) given to the objects of the sheet's `text`: each object takes the first box not yet taken of its kind standing where its call says it stands, else the first of its kind in order -- so a call written by hand outside any tag, which emits a box too, is passed over rather than shifting every box after it."""
    used = [False] * len(raw)
    out = []
    for obj, model in _objects(text):
        x, y = _position(model)
        pick = None
        if x is not None and y is not None:
            pick = next((i for i, b in enumerate(raw) if not used[i] and b["kind"] == obj.type
                         and abs(float(b["x"]) - x) < 0.05 and abs(float(b["y"]) - y) < 0.05), None)
        if pick is None:
            pick = next((i for i, b in enumerate(raw) if not used[i] and b["kind"] == obj.type), None)
        if pick is None:
            continue
        used[pick] = True
        b = raw[pick]
        out.append(Box(obj.id, obj.type, float(b["x"]), float(b["y"]), float(b["w"]), float(b["h"]),
                       None if b.get("dw") is None else float(b["dw"]), None if b.get("n") is None else float(b["n"])))
    return out


def read_plans(here):
    """The plans of the project's export (data/plans.json's `plans`), {} where there is no export yet."""
    try:
        data = json.loads((Path(here.data_dir) / "plans.json").read_text(encoding="utf-8"))
    except (OSError, ValueError, AttributeError):
        return {}
    plans = data.get("plans") if isinstance(data, dict) else None
    return plans if isinstance(plans, dict) else {}


def read_fire_plans(here):
    """The fire-protection plans of the project's export (data/fire.json's `plans`), {} where there is no export yet -- or none was ever saved: what a `sheet-fire-viewport` is drawn from."""
    try:
        data = json.loads((Path(here.data_dir) / "fire.json").read_text(encoding="utf-8"))
    except (OSError, ValueError, AttributeError):
        return {}
    plans = data.get("plans") if isinstance(data, dict) else None
    return plans if isinstance(plans, dict) else {}


def units_per_m(plan):
    """A plan's calibration -- how many of its sheet units are a metre of the building -- or None where it has none."""
    calibration = plan.get("scale") if isinstance(plan, dict) else None
    value = calibration.get("units_per_m") if isinstance(calibration, dict) else None
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0 else None


def scale_for(plan, drawing_mm):
    """The n of 1:n a calibrated plan is printed at when its drawing is `drawing_mm` wide (lib/sheet.typ's rule: crop.w / units_per_m / n · 1000 mm), unrounded; None for a plan with no calibration."""
    per_m = units_per_m(plan)
    crop = plan.get("crop") if isinstance(plan, dict) else None
    if per_m is None or not isinstance(crop, dict) or not drawing_mm or drawing_mm <= 0:
        return None
    return float(crop["w"]) / per_m * 1000.0 / drawing_mm


def drawing_width(plan, model):
    """The width a plan or a section is printed at, in millimetres, from its call: its width, or its scale and the plan's calibration; None where neither can be read."""
    width = to.mm_of(model.get("width"))
    if width is not None:
        return width
    n = model.get("scale")
    per_m = units_per_m(plan)
    crop = plan.get("crop") if isinstance(plan, dict) else None
    if isinstance(n, (int, float)) and not isinstance(n, bool) and n > 0 and per_m and isinstance(crop, dict):
        return float(crop["w"]) / per_m / n * 1000.0
    return None


def estimate_boxes(here, text, plans=None):
    """The boxes of the sheet's objects worked out in Python, where Typst could not be asked: a plan from its width or scale and its crop's proportions, a text from its words, the legend and the title block from their sizes. Rough, and only where nothing better is to be had."""
    plans = read_plans(here) if plans is None else plans
    fire_plans = read_fire_plans(here)
    page = next((o.model() for o in to.objects(text) if o.type == "sheet-page" and o.state != "unreadable"), None)
    width, height = page.size() if page is not None else (420, 297)
    margin = to.mm_of(page.get("margin")) if page is not None else 10.0
    margin = 10.0 if margin is None else margin
    out = []
    for obj, model in _objects(text):
        x, y = _position(model)
        if model is None:
            continue
        kind = obj.type
        if kind == "sheet-titleblock":
            w = to.mm_of(model.get("width")) or min(200.0, width - 2 * margin)
            x = width - margin - w if x is None else x
            y = height - margin - 43.0 if y is None else y
            out.append(Box(obj.id, kind, x, y, w, 43.0, estimated=True))
            continue
        x, y = x or 0.0, y or 0.0
        if kind in DRAWING_KINDS:
            plan = (fire_plans if kind == "sheet-fire-viewport" else plans).get(model.get("plan") or "", {})
            dw = drawing_width(plan, model) or 80.0
            crop = plan.get("crop") if isinstance(plan, dict) else None
            ratio = float(crop["h"]) / float(crop["w"]) if isinstance(crop, dict) and crop.get("w") else 0.75
            extra = 8.0 if kind == "sheet-section" else 0.0
            if kind != "sheet-section" and model.get("plan") and model.get("title") not in (None, False):
                extra += TITLE_MM
            n = model.get("scale")
            out.append(Box(obj.id, kind, x, y, dw, dw * ratio + extra, dw, n if isinstance(n, (int, float)) else scale_for(plan, dw), estimated=True))
        elif kind == "sheet-text":
            body = model.get("body")
            markup = body.markup if isinstance(body, to.Content) else (body if isinstance(body, str) else "")
            size = to.mm_of(model.get("size")) or 3.5
            lines = markup.split("\\") if markup else [""]
            w = to.mm_of(model.get("width")) or max(5.0, max(len(line.strip()) for line in lines) * size * 0.55)
            out.append(Box(obj.id, kind, x, y, w, len(lines) * size * 1.3, estimated=True))
        elif kind in LEGEND_KINDS:
            out.append(Box(obj.id, kind, x, y, to.mm_of(model.get("width")) or 120.0, 40.0, estimated=True))
        elif kind == "sheet-quantities":
            # a title, the heading's line and a few lines of materials, at the sheet's 8pt: estimated until the next compile measures it
            out.append(Box(obj.id, kind, x, y, to.mm_of(model.get("width")) or 150.0, 8.0 + 5.5 + 5.5 * 6, estimated=True))
        elif kind == "sheet-position-list":
            # a title, the heading's two lines and one line a position, at the sheet list's 8pt
            out.append(Box(obj.id, kind, x, y, to.mm_of(model.get("width")) or 180.0, 8.0 + 9.0 + 5.5 * max(1, _count_positions(here)), estimated=True))
    return out


def _count_positions(here):
    try:
        found = json.loads((Path(here.data_dir) / "positions-index.json").read_text(encoding="utf-8")).get("positions")
    except (OSError, ValueError, AttributeError):
        return 1
    return len(found) if isinstance(found, list) else 1


def render(here, sheet_id, target):
    """Compiles sheet `sheet_id` into `target` and asks Typst for its boxes, the two side by side -- what the canvas shows. Gives back a dictionary: `text` (the sheet as it was compiled), `ok`, `message` (Typst's own words where it failed), `pdf` (the bytes, None where it failed) and `boxes` (as `parse_boxes`, None where the query failed). Qt-free; run off the main thread."""
    text = sheets.read(here, sheet_id)
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    exe = project.typst_executable()
    common = dict(stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.DEVNULL, text=True, encoding="utf-8", errors="replace",
                  cwd=str(Path(here.typst_root)))
    try:
        compiling = proc.popen([exe, *sheets.compile_args(here, sheet_id, target)], **common)
        querying = proc.popen([exe, *query_args(here, sheet_id)], **common)
    except OSError as exc:
        return {"text": text, "ok": False, "message": f"Typst cannot be started -- {exc}", "pdf": None, "boxes": None}
    try:
        out, err = compiling.communicate(timeout=COMPILE_TIMEOUT_S)
        qout, _qerr = querying.communicate(timeout=COMPILE_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        compiling.kill()
        querying.kill()
        return {"text": text, "ok": False, "message": f"typst took more than {COMPILE_TIMEOUT_S} s", "pdf": None, "boxes": None}
    if compiling.returncode != 0:
        return {"text": text, "ok": False, "message": (err or out or "").strip() or f"typst exited with {compiling.returncode}", "pdf": None,
                "boxes": parse_boxes(qout) if querying.returncode == 0 else None}
    try:
        data = target.read_bytes()
    except OSError as exc:
        return {"text": text, "ok": False, "message": str(exc), "pdf": None, "boxes": None}
    return {"text": text, "ok": True, "message": "", "pdf": data, "boxes": parse_boxes(qout) if querying.returncode == 0 else None}


def cache_target(here, sheet_id):
    """Where a sheet's preview is compiled: Woodcore's cache, named after the project's file and the sheet -- never `Plans/<id>.pdf`."""
    key = hashlib.sha256(str(Path(here.file).resolve()).encode("utf-8")).hexdigest()[:16]
    return usersettings.cache_dir("sheets") / f"{key}-{sheet_id}.pdf"


def file_signature(path):
    """What the file says now: its size, the time it was written and its SHA-256 -- None where it cannot be read. A change by any editor, VS Code or this one, is a signature that differs."""
    try:
        found = Path(path).stat()
        digest = hashlib.sha256(Path(path).read_bytes()).hexdigest()
    except OSError:
        return None
    return (found.st_size, found.st_mtime_ns, digest)


def parse_scale(text):
    """The n of «1:n» or of «n», a positive number; None where the text is not one."""
    found = re.fullmatch(r"\s*(?:1\s*:\s*)?(\d+(?:[.,]\d+)?)\s*", text or "")
    if not found:
        return None
    n = float(found.group(1).replace(",", "."))
    if n <= 0:
        return None
    return int(n) if n == int(n) else n


def snap(value):
    return round(round(value / SNAP_MM) * SNAP_MM, 2)


def markup_of(value):
    """A text argument as the engineer's markup in a field: Content's markup, a string as it is, "" for none and auto."""
    if isinstance(value, to.Content):
        return value.markup
    if isinstance(value, str):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    return ""


class _Job(QThread):
    """One `render` off the main thread: `done` carries what it returned. Unparented and held in _RUNNING until it has finished, so an editor deleted meanwhile never destroys a thread that still runs."""

    done = Signal(object)

    def __init__(self, work):
        super().__init__()
        self.work = work

    def run(self):
        try:
            result = self.work()
        except Exception as exc:        # broad: an answer whatever happens -- its message shown; never leave the canvas waiting for ever
            result = {"text": None, "ok": False, "message": str(exc), "pdf": None, "boxes": None}
        self.done.emit(result)


_RUNNING = set()


class Compiler:
    """The sheet's compiles: `request()` starts one DEBOUNCE_MS later, one at a time, and a request made while one runs starts another once it has ended -- the newest wins, a result a newer request has overtaken being dropped. `on_result(result)` is called on the main thread with what `render` gave back."""

    def __init__(self, owner, on_result):
        self.owner = owner
        self.on_result = on_result
        self.target = None          # (here, sheet_id)
        self.running = False
        self.pending = False
        self.timer = QTimer(owner)
        self.timer.setSingleShot(True)
        self.timer.setInterval(DEBOUNCE_MS)
        self.timer.timeout.connect(self._start)

    def request(self, here, sheet_id, now=False):
        self.target = (here, sheet_id)
        if now:
            self.timer.stop()
            self._start()
        else:
            self.timer.start()

    def busy(self):
        return self.running or self.pending or self.timer.isActive()

    def _start(self):
        if self.target is None:
            return
        if self.running:
            self.pending = True
            return
        here, sheet_id = self.target
        folder = getattr(self.owner, "preview_folder", None)
        target = cache_target(here, sheet_id) if folder is None else Path(folder) / f"{sheet_id}.pdf"
        job = _Job(lambda: render(here, sheet_id, target))
        _RUNNING.add(job)
        owner = self.owner
        self.running = True
        activity = self.activity = tasks.activity().begin("activity_sheet")   # said by the chip at the top right while the sheet renders (REQ-007)
        job.done.connect(lambda result: self._finished(result) if shiboken6.isValid(owner) else None)
        # the chip told it is over whatever happens to the editor: one closed before its render ends never calls _finished (end() of a token already ended does nothing)
        job.finished.connect(lambda: (_RUNNING.discard(job), tasks.activity().end(activity), job.deleteLater()))
        job.start()

    def _finished(self, result):
        self.running = False
        if getattr(self, "activity", None) is not None:
            tasks.activity().end(self.activity)
            self.activity = None
        if self.pending:
            self.pending = False
            self._start()       # a newer change: this result is overtaken
            return
        self.on_result(result)
