"""PlanCanvas's tools, tracking and editing -- the tool chosen, what the pointer snaps and tracks to, a selection, an element, an axis, a storey line or box and a load level added -- a mixin of methods moved verbatim out of calc/tools/plan_canvas.py (issue #30). PlanCanvas names it among its bases.
"""

import math
from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QObject, QPointF, QRect, QRectF, QSize, Qt, QTimer, Signal, qVersion
from PySide6.QtGui import QBrush, QColor, QFont, QImage, QPainter, QPainterPath, QPen, QPixmap, QPixmapCache, QTransform
import theme  # the desk around the sheet (theme.py, v0.90)
import plan_canvas_tools  # the circle a column is turned by, and the ruler (issue #9)
from domains import plan as model
from domains import plan_svg
from domains import plan_tracking as tracking
import plan_canvas_edit  # «Déplacer», «Copier» and «Ligne d'aide» (issue #18)
import plan_canvas_outline  # the building's outline: its tool, and how it is taken and reshaped (issue #54)
from domains import lines  # a parallel aid's line, through an element's side (issue #18)
import plan_clipboard  # the one clip of the process, Ctrl+C's and Ctrl+V's (issue #61)
from domains import plan_clip
from plan_canvas_view import (  # split out of this module (issue #30): every name it had is still importable from it
    BASE_RENDER_PX,
    CROP_MARGIN,
    DISK,
    DISK_CACHE_BYTES,
    DISK_CACHE_DIR,
    MEMORY_CACHE_BYTES,
    RENDERS,
    STOREY_COLOUR,
    STOREY_FILL,
    SUPERPOSE_RENDER_PX,
    TILE_MARGIN,
    TILE_MAX_PX,
    _round,
    PlanCanvasViewMixin,
)


# What a click must come within, on the screen, to take an element, a corner or a target.
PICK_PX = 8


# The tools, by name: the STE types draw an element, the others do what they say. A section's two (v0.114): a storey line, two clicks, and a storey box, two opposite corners.
POINT_TOOLS = {"S"}

# The Text tool (issue #43): a click puts a text down, written in the pane -- the position plan's and the fire-protection plan's, both canvases being this one.
TEXT_TOOL = "text"


AXIS_TOOLS = {"axis-v": 90, "axis-h": 0, "axis-o": None}


# A section's third tool (v0.116): the load transfer level, two clicks as a storey line, Shift keeping it horizontal.
LEVEL_TOOL = "load-level"


# What a selection may be, and the list of the source it is an index into.
SELECTION_LISTS = model.ENTRY_LISTS   # since issue #18 said once, in the domain, with the construction aids (`aid`)

READOUT_KINDS = ("axis-crossing", "vertex", "crossing", "midpoint", "on-axis", "on-line")


def readout_kind(kind):
    """What the readout under the plan says of a snap: the kinds the tab has a word for; where the cursor follows a tracking line, the dotted line says so, and nothing is written."""
    return kind if kind in READOUT_KINDS else ""


class PlanCanvasEditMixin:
    """Methods of plan_canvas.PlanCanvas, moved verbatim (issue #30): the class names this mixin among its bases."""

    def set_tool(self, tool):
        was = self.clipped()
        if tool != plan_canvas_tools.RULER:
            plan_canvas_tools.clear_ruler(self)
        plan_canvas_tools.clear_dimension_draft(self)
        self.tool = tool
        self.drawing = []
        self.cursor = None
        self.drag = None
        self.aid_pending = None
        self.reset_tracking()
        self.snap_marker.setPath(QPainterPath())
        self.align_from = None
        self.align_item.setPath(QPainterPath())
        self.restore_cursor()
        if self.clipped() != was:
            # the crop tool shows the whole page, and leaving it shows the crop just drawn
            self.apply_view_mode()
            self.fit()
        self.update_helpers()

    def set_storey_choice(self, storey):
        """The storey a section's tools draw from now on -- the tab's choice; blank, they draw nothing and say so (storeyMissing)."""
        self.storey_choice = str(storey or "").strip()

    def tool_kind(self):
        """What the current tool draws: `point`, `line`, `poly`, `axis`, or None for the others."""
        tool = self.tool
        if tool in AXIS_TOOLS:
            return "axis"
        if tool == plan_canvas_outline.TOOL:
            return "poly"   # the building's outline is drawn as every area is (issue #54), and ends as its own (finish_drawing)
        if tool not in model.TYPES:
            return None
        if tool in POINT_TOOLS or (tool == "L" and self.subtypes.get("L") == "punkt"):
            return "point"
        return model.TYPES[tool]["geo"]

    def tolerance(self):
        return PICK_PX / max(self.transform().m11(), 1e-9)

    def snap_index(self, exclude=None, exclude_storey=None):
        """What a point may snap to (domains/plan_tracking.PlanSnapIndex), gathered once per state of the plan: the axes, the elements' corners, middles and crossings, and since v0.116 a section's storey lines' ends and storey boxes' corners. `exclude_storey` is the (kind, index) of the storey line or box being dragged."""
        key = (exclude, exclude_storey, self.snap_axes, self.snap_elements, self._sup_snap_off)
        if self._snap_index is None or self._snap_index[0] != key:
            # since v0.116 also a section's load transfer levels' ends and the superposed plan's points, both behind «Accrocher aux éléments»
            # ... and the corners of the building's outline (issue #54), none of them while one of its own is dragged
            extra = (self.load_level_points(exclude_storey) + self.superposition_snap_points() + plan_canvas_outline.snap_points(self, exclude_storey)) if self.snap_elements else []
            index = tracking.PlanSnapIndex(self.source, model.crop_of(self.frame_source()), axes=self.snap_axes, elements=self.snap_elements, exclude=exclude, exclude_storey=exclude_storey, extra_points=extra)
            self._snap_index = (key, index)
        return self._snap_index[1]

    def label_frames(self):
        """Where every number is drawn (plan_svg.number_frames), asked for on every movement of the pointer and gathered once per state of the plan."""
        if self._label_frames is None:
            self._label_frames = plan_svg.number_frames(self.source)
        return self._label_frames

    def label_under(self, raw):
        """The index of the element whose number lies under `raw`, or None."""
        return model.hit_label(self.source, raw, self.tolerance(), self.label_frames())

    def snapped(self, raw, anchor=None, shift=False, exclude=None, exclude_storey=None):
        """The point a click at `raw` puts down, and what it snapped to: the two snapping buttons decide the targets, Shift the direction from `anchor` (0, 45 or 90 degrees, as ever). Without Shift the pointer **tracks** (v0.116, domains/plan_tracking.py): it locks to the rays through the points it has rested on -- and through `anchor`, the last point of what is being drawn --, to where two of them cross, and to where one crosses a line of the plan; the rays it is locked to are kept in `locked` for the dotted lines and for Tab. A point put down by a typed distance (`place`) is that point."""
        if self._forced is not None:
            return self._forced, None
        self.locked = []
        if not (self.snap_axes or self.snap_elements):
            if shift and anchor is not None:
                return model.constrain(anchor, raw), None
            return tuple(raw), None
        index = self.snap_index(exclude, exclude_storey)
        if shift and anchor is not None:
            return index.snap(raw, self.tolerance(), anchor, constrained=True)
        anchors = ([tuple(anchor)] if anchor is not None else []) + [q for q in self.acquired if anchor is None or math.dist(q, anchor) > 1e-6]
        result = tracking.track(index, anchors, raw, self.tolerance())
        self.locked = result["rays"]
        return result["point"], result["kind"]

    def reset_tracking(self):
        """Nothing acquired, nothing locked, no distance being typed: after another tool, another plan, Escape."""
        self.acquired = []
        self.locked = []
        self._hover = None
        self.acquire_timer.stop()
        self.hide_distance()

    def note_hover(self, point, kind):
        """The pointer is at `point`, which snapped as `kind`: resting on a point of the plan for ACQUIRE_MS acquires it. Moving off, or onto another, starts again; a point already acquired is not acquired twice."""
        at = tuple(point) if kind in tracking.HARD_KINDS and not self.typing else None
        if at is not None and any(math.dist(at, q) <= 1e-6 for q in self.acquired):
            at = None
        if at != self._hover:
            self._hover = at
            self.acquire_timer.stop()
            if at is not None:
                self.acquire_timer.start()

    def acquire(self):
        """The dwell is over: the point the pointer rests on becomes a reference the cursor can lock to -- up to MAX_ACQUIRED at once, the newest first."""
        if self._hover is None:
            return
        self.acquired = tracking.acquire(self.acquired, self._hover)
        self._hover = None
        self.update_helpers()

    def per_m(self):
        """Sheet units per metre of the frame the plan is drawn over, or None where it has no scale."""
        return model.units_per_m(self.frame_source())

    def show_distance(self):
        """Tab: the field for a distance along the ray the cursor is locked to, filled with the distance so far, in metres where the plan has a scale."""
        if len(self.locked) != 1 or self.typing:
            return
        ray = self.locked[0]
        self.typing = True
        self.typing_ray = ray
        at = self.cursor if self.cursor is not None else ray["anchor"]
        p = self.mapFromScene(QPointF(*at))
        self.distance.move(min(max(p.x() + 14, 0), max(self.viewport().width() - 120, 0)), max(p.y() - 12, 0))
        self.distance.setText(tracking.distance_text(ray, at, self.per_m()))
        self.distance.selectAll()
        self.distance.show()
        self.distance.setFocus()

    def hide_distance(self):
        self.typing = False
        self.typing_ray = None
        self.distance.hide()
        self.distance.setStyleSheet("")
        if self.hasFocus() or self.distance.hasFocus():
            self.setFocus()

    def on_typed(self, text):
        p = tracking.typed_point(self.typing_ray, text, self.per_m()) if self.typing_ray else None
        self.distance.setStyleSheet("" if p is not None or not text.strip() else f"background:{theme.colour('danger-soft')};")
        if p is not None:
            self.cursor = p
            self.update_helpers()

    def commit_typed(self):
        p = tracking.typed_point(self.typing_ray, self.distance.text(), self.per_m()) if self.typing_ray else None
        if p is None:
            return
        self.hide_distance()
        self.place(p)

    def place(self, p):
        """A point put down where a typed distance says, as if the pointer had clicked exactly there -- with Shift, and the tracking, left out."""
        self._forced = (float(p[0]), float(p[1]))
        try:
            self.click_point(self._forced, False)
        finally:
            self._forced = None
        self.update_helpers()

    def click_point(self, raw, shift):
        """What a left click at `raw` does with the current tool: the position plan's own; the fire-protection plan's canvas does its own."""
        self._left_click(raw, shift)

    def show_snap(self, point, kind):
        path = QPainterPath()
        if kind:
            s = 6.0
            if kind == "track-line":
                kind = "crossing"
            if kind == "vertex":
                path.addRect(-s, -s, 2 * s, 2 * s)
            elif kind == "midpoint":
                path.moveTo(0, -s)
                path.lineTo(s, s)
                path.lineTo(-s, s)
                path.closeSubpath()
            elif kind in ("crossing", "axis-crossing"):
                path.moveTo(-s, -s)
                path.lineTo(s, s)
                path.moveTo(-s, s)
                path.lineTo(s, -s)
                if kind == "axis-crossing":
                    path.addEllipse(QPointF(0, 0), s * 1.3, s * 1.3)
            else:
                path.addEllipse(QPointF(0, 0), s * 0.8, s * 0.8)
            self.snap_marker.setPos(QPointF(*point))
        self.snap_marker.setPath(path)

    def begin_change(self):
        self.about_to_change.emit()

    def end_change(self):
        self.invalidate()
        self.changed.emit()

    # -- the selection (issue #61): the object in focus -- `selection`, (kind, index) or None, which the handles, the right pane and every reader of one object take -- and `extra`, the others Ctrl+click or Ctrl+A added, in the order added. Setting `selection` lets go of `extra`, so an object drawn or a plan opened leaves one object selected (ARCH-004, the schemas' SchemaCanvas.select(add=True)).

    @property
    def selection(self):
        return self.__dict__.get("_focus")

    @selection.setter
    def selection(self, value):
        self.__dict__["_focus"] = value
        self.__dict__["extra"] = []

    @property
    def extra(self):
        return self.__dict__.setdefault("extra", [])

    def select(self, selection, add=False):
        """Selects `selection` alone; with `add` (Ctrl+click) toggles it in the selection instead -- added and focused, or taken out, the last one added then in focus."""
        if add and selection is not None:
            entries = self.selected_entries()
            if selection in entries:
                entries.remove(selection)
            else:
                entries.append(selection)
            self.set_selected(entries)
            return
        if selection != self.selection or self.extra:
            self.selection = selection
            self.update_helpers()
            self.selection_changed.emit()

    def set_selected(self, entries):
        """Selects `entries` [(kind, index)], the last one in focus; says so when that is not what was selected."""
        entries = list(dict.fromkeys(tuple(entry) for entry in entries))
        if entries == self.selected_entries():
            return
        self.selection = entries[-1] if entries else None
        self.__dict__["extra"] = entries[:-1]
        self.update_helpers()
        self.selection_changed.emit()

    def selected_entries(self):
        """Every object selected, [(kind, index)], the one in focus last -- those the plan still has."""
        out = []
        for entry in self.extra + ([self.selection] if self.selection else []):
            kind, index = entry
            if kind in SELECTION_LISTS and index < len(self.source.get(SELECTION_LISTS[kind]) or []) and entry not in out:
                out.append(entry)
        return out

    def selection_count(self):
        """How many objects are selected."""
        return len(self.selected_entries())

    def select_all(self):
        """Ctrl+A (issue #61): everything the plan holds, but the building's outline -- taken by hand only (T7)."""
        entries = [(kind, i) for kind, key in SELECTION_LISTS.items() if kind not in model.SINGLE_ENTRIES for i in range(len(self.source.get(key) or []))]
        self.set_selected(entries)

    def selected_element(self):
        if self.selection and self.selection[0] == "element" and self.selection[1] < len(self.source["elements"]):
            return self.source["elements"][self.selection[1]]
        return None

    def selected_axis(self):
        if self.selection and self.selection[0] == "axis" and self.selection[1] < len(self.source["axes"]):
            return self.source["axes"][self.selection[1]]
        return None

    def _selected_of(self, kind):
        entries = self.source.get(SELECTION_LISTS[kind]) or []
        if self.selection and self.selection[0] == kind and self.selection[1] < len(entries):
            return entries[self.selection[1]]
        return None

    def selected_storey_line(self):
        """The storey line selected on a section ({storey, points}), or None."""
        return self._selected_of("storey-line")

    def selected_storey_box(self):
        """The storey box selected on a section ({storey, x, y, w, h}), or None."""
        return self._selected_of("storey-box")

    def selected_load_level(self):
        """The load transfer level selected on a section ({storey, floor, points, label_offset}), or None (v0.116)."""
        return self._selected_of("load-level")

    def load_level_frames(self):
        """[(index, frame)] of every load transfer level's words, where plan_svg draws them: what a click takes, to move them."""
        if not self.source.get("load_levels"):
            return []  # every plan but a section that carries one -- a fire-protection plan's canvas, which inherits this one, included
        sz = plan_svg.sizes_of(self.source)
        boxes = self.source.get("storey_boxes") or []
        frames = []
        for i, level in enumerate(self.source.get("load_levels") or []):
            frame = plan_svg.load_level_frame(level, sz, boxes, self.language)
            if frame is not None:
                frames.append((i, frame))
        return frames

    def delete_selection(self):
        """Everything selected removed, in one step of «Annuler» (issue #61)."""
        chosen = self.selected_entries()
        if not chosen:
            return
        self.begin_change()
        for kind, index in sorted(chosen, key=lambda entry: -entry[1]):
            entries = self.source.get(SELECTION_LISTS[kind]) or []
            del entries[index]
            if kind in model.SINGLE_ENTRIES and not entries:
                self.source.pop(SELECTION_LISTS[kind], None)   # the building's outline deleted: the plan is the file it was before one was drawn, not one with an empty list (issue #54)
        self.selection = None
        self.end_change()
        self.selection_changed.emit()

    # -- the selection moved, copied, duplicated (issue #18, plan_canvas_edit.py) --

    def has_selection(self):
        return bool(self.selected_entries())

    def single_selected(self):
        """The kind of the object selected where a plan has one of it, which is therefore moved and never copied -- the building's outline (plan.SINGLE_ENTRIES, issue #54) --, or None. Only when it is all that is selected: with other objects, «Copier» copies them and leaves the outline (issue #61). None on a canvas whose selection is not this one's (the fire-protection plan's, which selects ids)."""
        kinds = {kind for kind, _index in self.selected_entries()}
        return next(iter(kinds)) if len(kinds) == 1 and kinds <= set(model.SINGLE_ENTRIES) else None

    def translate_selection(self, dx, dy):
        """Every object selected moved by (dx, dy) -- inside a change the caller opened (plan.translate_entry)."""
        for kind, index in self.selected_entries():
            model.translate_entry(self.source, kind, index, dx, dy)

    def copy_selection(self, dx, dy):
        """A copy of every object selected, moved by (dx, dy) -- inside a change the caller opened; the originals stay selected, so the next copy is made of them again (D-014). The building's outline is not copied: a plan has one, and it is moved (issue #54). Returns the copies' [(kind, index)]."""
        chosen = self.selected_entries()
        if chosen and all(kind in model.SINGLE_ENTRIES for kind, _index in chosen):
            self.edit_refused.emit(chosen[0][0])
            return []
        objects = [(kind, self.source[SELECTION_LISTS[kind]][index]) for kind, index in chosen]
        made, renamed = [], []
        for kind, original in objects:
            if kind in model.SINGLE_ENTRIES:
                continue
            entries = self.source[SELECTION_LISTS[kind]]
            index = next(i for i, entry in enumerate(entries) if entry is original)
            new, renames = model.copy_entry(self.source, kind, index, dx, dy, model.crop_of(self.frame_source()))
            made.append((kind, entries[new]))
            renamed += renames
        # an axis copied is placed among the others, which may move an index: every object found again by identity
        def where(kind, entry):
            return (kind, next(i for i, other in enumerate(self.source[SELECTION_LISTS[kind]]) if other is entry))
        focus = objects[-1]
        self.__dict__["_focus"] = where(*focus)
        self.__dict__["extra"] = [where(*item) for item in objects[:-1]]
        if renamed:
            self.axes_renamed.emit(renamed)
        return [where(*item) for item in made]

    def duplicate_selection(self):
        """«Dupliquer» under «Objet sélectionné» (issue #18, D-016): a copy of the object selected beside it, one step of «Annuler», and the copy selected."""
        if not self.has_selection():
            return False
        if self.single_selected():
            self.edit_refused.emit(self.single_selected())
            return False
        dx, dy = plan_canvas_edit.duplicate_offset(self)
        self.begin_change()
        made = self.copy_selection(dx, dy)
        self.selection = made[-1] if made else None
        self.__dict__["extra"] = made[:-1]
        self.end_change()
        self.selection_changed.emit()
        return True

    def selection_outline(self, dx, dy):
        """Every object selected drawn where (dx, dy) would put it."""
        path = QPainterPath()
        for kind, index in self.selected_entries():
            path.addPath(self.entry_outline(kind, self.source[SELECTION_LISTS[kind]][index], dx, dy))
        return path

    def clip_outline(self, point):
        """The clip held drawn as Ctrl+V would put it down at `point` (plan_clip.placed, the paste's own placing)."""
        path = QPainterPath()
        clip = plan_clipboard.current()
        if clip is None or clip.kind != plan_clip.POSITION:
            return path
        for kind, entry in plan_clip.placed(clip, point, self.per_m()):
            path.addPath(self.entry_outline(kind, entry))
        return path

    def entry_outline(self, kind, entry, dx=0.0, dy=0.0):
        """One object of the plan drawn where (dx, dy) would put it: its points joined, or a line across the frame for an axis or an aid -- what «Déplacer», «Copier» and Ctrl+V show, and what marks an object selected beside the one in focus (issue #61)."""
        path = QPainterPath()
        if kind in ("axis", "aid"):
            moved = {"point": [entry["point"][0] + dx, entry["point"][1] + dy], "angle": entry["angle"]}
            segment = model.axis_segment(moved, model.crop_of(self.frame_source()))
            if segment:
                path.moveTo(QPointF(*segment[0]))
                path.lineTo(QPointF(*segment[1]))
            return path
        if kind == "storey-box":
            path.addRect(QRectF(float(entry["x"]) + dx, float(entry["y"]) + dy, float(entry["w"]), float(entry["h"])))
            return path
        points = [QPointF(x + dx, y + dy) for x, y in entry.get("points", [])]
        if len(points) == 1:
            r = 6.0 / max(self.transform().m11(), 1e-9)
            path.addEllipse(points[0], r, r)
        elif points:
            path.moveTo(points[0])
            for q in points[1:]:
                path.lineTo(q)
            if kind == plan_canvas_outline.KIND or (kind == "element" and model.element_kind(entry) == "poly"):
                path.closeSubpath()
        return path

    def line_under(self, raw):
        """The line under `raw` a parallel aid is drawn to: an aid, an axis, or the side of an element -- (a point of it, its angle), or None."""
        tol = self.tolerance()
        window = model.crop_of(self.frame_source())
        i = model.hit_aid(self.source, raw, tol, window)
        if i is not None:
            aid = self.source["aids"][i]
            return tuple(aid["point"]), float(aid["angle"])
        i = model.hit_axis(self.source, raw, tol, window)
        if i is not None:
            axis = self.source["axes"][i]
            return tuple(axis["point"]), float(axis["angle"])
        best = None
        for element in self.source.get("elements", []):
            for a, b in model.segments_of(element):
                d = model._point_segment(raw, a, b)[0]
                if d <= tol and (best is None or d < best[0]):
                    best = (d, a, b)
        if best is None:
            return None
        made = lines.through(best[1], best[2])
        return made if made else None

    def add_text(self, point):
        """A text put down at `point` (issue #43): empty, selected, written in the pane -- one step of «Annuler». The tool goes back to «Sélection», the text being written in the pane and not on the sheet."""
        self.begin_change()
        texts = self.source.setdefault("texts", [])
        texts.append({"points": [[_round(point[0]), _round(point[1])]], "text": ""})
        self.selection = ("text", len(texts) - 1)
        self.end_change()
        self.selection_changed.emit()
        self.tool_done.emit()

    def add_aid(self, kind, point, angle):
        """A construction aid added to the source, selected, one step of «Annuler»."""
        self.begin_change()
        aids = self.source.setdefault("aids", [])
        aids.append(model.new_aid(kind, point, angle))
        self.selection = ("aid", len(aids) - 1)
        self.end_change()
        self.selection_changed.emit()

    def readout(self, kind):
        return readout_kind(kind)

    def finish_drawing(self):
        """Ends the element being drawn: a line needs two points (an Auflager may keep one, and is then a point), an area three. Points closer than a click's reach are one point clicked twice."""
        kind = self.tool_kind()
        if kind not in ("line", "poly") or not self.drawing:
            self.drawing = []
            self.update_helpers()
            return
        tol = self.tolerance() * 0.5
        points = []
        for p in self.drawing:
            if not points or math.dist(p, points[-1]) > tol:
                points.append(p)
        if kind == "poly" and len(points) > 3 and math.dist(points[0], points[-1]) <= tol:
            points.pop()
        self.drawing = []
        self.cursor = None
        enough = len(points) >= (3 if kind == "poly" else 2) or (self.tool == "M" and len(points) == 1)
        if enough and self.tool == plan_canvas_outline.TOOL:
            plan_canvas_outline.add(self, points)   # the building's outline is no element: it takes the place of the one the plan had (issue #54)
        elif enough:
            self.add_element(self.tool, points)
        self.update_helpers()

    def add_element(self, type_, points):
        element = {"type": type_, "label": self.propose_label(type_), "points": [[_round(x), _round(y)] for x, y in points]}
        subtype = self.subtypes.get(type_)
        if subtype is not None:
            element["subtype"] = subtype
        self.begin_change()
        self.new_element(element)
        self.source["elements"].append(element)
        self.selection = ("element", len(self.source["elements"]) - 1)
        self.end_change()
        self.selection_changed.emit()

    def add_axis(self, point, angle):
        """A new axis, named by where it lies among the others (plan.insert_axis): between A and B it becomes B, and B moves up to C."""
        axis = {"label": "", "point": [_round(point[0]), _round(point[1])], "angle": _round(angle), "bubbles": "both"}
        self.begin_change()
        renames = model.insert_axis(self.source["axes"], axis, model.crop_of(self.frame_source()))
        self.selection = ("axis", len(self.source["axes"]) - 1)
        self.end_change()
        self.selection_changed.emit()
        if renames:
            self.axes_renamed.emit(renames)

    def add_storey_line(self, a, b):
        """A section's storey line between `a` and `b`, of the storey chosen: written into the source as every edit is, selected, and said (storeyLineDrawn)."""
        points = [[_round(a[0]), _round(a[1])], [_round(b[0]), _round(b[1])]]
        self.begin_change()
        lines = self.source.setdefault("storey_lines", [])
        lines.append({"storey": self.storey_choice, "points": points})
        self.selection = ("storey-line", len(lines) - 1)
        self.end_change()
        self.selection_changed.emit()
        self.storeyLineDrawn.emit([list(q) for q in points])

    def add_storey_box(self, a, b):
        """A section's storey box with `a` and `b` its opposite corners, of the storey chosen -- and its numbering character, which its designation x1xx is made of (v0.116): written into the source, selected, and said (storeyBoxDrawn)."""
        x0, x1 = sorted((a[0], b[0]))
        y0, y1 = sorted((a[1], b[1]))
        box = {"storey": self.storey_choice, "x": _round(x0), "y": _round(y0), "w": _round(x1 - x0), "h": _round(y1 - y0)}
        floor = self.floor_of(self.storey_choice)
        if floor:
            box["floor"] = floor
        self.begin_change()
        boxes = self.source.setdefault("storey_boxes", [])
        boxes.append(box)
        self.selection = ("storey-box", len(boxes) - 1)
        self.end_change()
        self.selection_changed.emit()
        self.storeyBoxDrawn.emit(dict(box))

    def add_load_level(self, a, b):
        """A section's load transfer level between `a` and `b`, of the storey chosen and its numbering character (v0.116): written into the source and selected."""
        points = [[_round(a[0]), _round(a[1])], [_round(b[0]), _round(b[1])]]
        level = {"storey": self.storey_choice, "points": points}
        floor = self.floor_of(self.storey_choice)
        if floor:
            level["floor"] = floor
        self.begin_change()
        levels = self.source.setdefault("load_levels", [])
        levels.append(level)
        self.selection = ("load-level", len(levels) - 1)
        self.end_change()
        self.selection_changed.emit()

    def storey_point(self, raw, shift):
        """(point, snapped to) of a click with a storey tool: snapped as every tool's, and on a storey line's or a load level's second click with Shift on the horizontal through its first -- both are level."""
        anchor = self.drawing[-1] if self.drawing else None
        if self.tool in ("storey-line", LEVEL_TOOL) and anchor is not None:
            if shift:
                p, kind = self.snapped((raw[0], anchor[1]))
                return (p[0], anchor[1]), kind
            return self.snapped(raw, anchor)
        return self.snapped(raw)
