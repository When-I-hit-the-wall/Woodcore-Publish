"""The drawing surface of Woodcore's «Plan de protection incendie» tab (docs/domain/position-plans.md §3.3sexies, docs/ui/window.md §10quater; ported from origin/Gian's v0.112 onto the position plan's canvas of v0.114 in v0.115): the architect's plan under what a fire-protection plan draws on it, and the tools that make and change it.

Since v0.115 it is shown as the position plan is (plan_canvas.PlanCanvas, v0.114): its crop alone, or the whole page under a veil where «Afficher toute la page» asks for it (`set_show_outside`, `apply_view_mode`); its background may be a page of an imported document (`background.document`), rendered with its layers and its rotation -- its own, or that of the position plan it follows, whose frame `frame_source` answers with, the plan's own crop over it.

It is a position plan's canvas (plan_canvas.PlanCanvas) with another source on it: everything about the background -- a PDF page rendered by QtPdf in a thread, the part in view first, the tiles and the caches that keep them, an image or an SVG -- is inherited unchanged, since a fire-protection plan is drawn over the very same pages and states the very same four frame fields (domains/fire.py). What is its own is the drawing over the background, which is domains/fire_svg.py's, and the tools. Everything is drawn by hand -- the program delimits nothing --: a surface of one of three kinds (an outline of as many clicks as it has corners), a wall of a fire resistance and an escape route's length (a line of as many clicks as it has points), a door (three clicks: the hinge, the other jamb, the side it opens to), an emergency exit (two clicks: tail and tip) and an escape route's width (two clicks, one on either side of the passage). With the selection tool a click takes what lies under it, a drag moves a point of the one in focus, a text -- a surface's name, an escape route's length or a width's figure -- is dragged clear of what it hides as a position number is (`label_offset`, which follows its entry), and the legend -- a box listing what is drawn, which is no entry of the plan -- is dragged by its body.

The geometry -- what lies under the pointer, how a door or an exit is shaped -- is domains/fire.py's, which has no Qt in it; this module turns the mouse and the keys into calls to it and into edits of the source it is given. It has no text of its own: the tab (fire_tab.py) says what is what, in the window's language.

⚠️ Nothing of the position plan's own drawing is reached from here: no symbol, no axis, no number, no snapping index -- those would read `elements` and `axes`, which a fire-protection plan has none of. The mouse and key handlers and the helpers are overridden whole (since v0.116 `snapped`, with the tracking of domains/plan_tracking.py, is the base class's own: a fire-protection plan only tells it what to snap to, `snap_index`), and the base class's own are called only for what a plan and a fire-protection plan do alike: panning, the crop and the calibration (which edit the source they are given, and so the fire-protection plan's own frame -- or, for the crop, the one a plan that follows a position plan may state for itself; the tab disables the calibration while the plan follows a position plan's).
"""

import math

from PySide6.QtCore import QByteArray, QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import QBrush, QColor, QPainterPath, QPolygonF
from PySide6.QtWidgets import QGraphicsItem, QGraphicsRectItem

import plan_canvas
import theme  # the paper of a handle (theme.py, issue #29)
import plan_canvas_tools  # the ruler, the position plan's own (issue #9, D-012)
import plan_canvas_edit  # «Déplacer» and «Copier», the position plan's own (issue #18, D-015: its construction aids are not this plan's)
import plan_clipboard  # the one clip of the process, Ctrl+C's and Ctrl+V's (issue #61)
from domains import plan_clip
from domains import fire, fire_svg, plan, plan_svg
from domains import plan_tracking as tracking

# How long the drawing waits between two renderings of itself while a point or the legend is dragged. The overlay is rendered whole -- every surface, every hatch, every length written along an escape route and measured again -- so rendering it at every movement of the pointer made a drag stutter; the selection's outline and the handles, which are cheap, follow the pointer at once, and the overlay catches up every half second and once more when the button is let go.
DRAG_REDRAW_MS = 500

# The tools that draw with clicks, by name: what each puts down is decided where it is finished.
DRAWING_TOOLS = ("polygon", "wall", "route", "door", "exit", "width", "calibrate")

# The two that draw a line of as many points as the engineer clicks: a wall of a fire resistance and an escape route's length.
LINE_TOOLS = ("wall", "route")

# The three that draw a fixed number of points, and the collection each one's entry goes to. A door takes one click more than its two points: the third says which side of the line it opens to.
FIXED_TOOLS = {"door": "doors", "exit": "exits", "width": "widths"}
FIXED_POINTS = 2



class FireCanvas(plan_canvas.PlanCanvas):
    """The fire-protection plan being edited. It edits the `source` dictionary it is given in place -- the tab's draft -- and says so as the position plan's canvas does: `about_to_change` just before an edit (the tab keeps the state for its undo history), `changed` once it is made, `selection_changed` when other entries are selected."""

    # What a canvas that has no plan yet is drawn over; set_plan gives the real ones. At class level so that the base class's own construction, which does not ask for them, cannot find them missing.
    frame = None
    selected = ()
    # What the next entry of each tool is drawn as: the tab's combos set them.
    wall_class = "EI 30"       # the fire resistance of the next wall
    zone_kind = "horizontal"   # the kind of the next surface (fire.SURFACES)
    door_kind = "swing"        # how the next door opens (fire.DOOR_KINDS)
    door_class = "EI 30"       # the fire resistance of the next door; None for a door without one, which is no symbol of the sheet
    lang = "de"                # the language the legend is written in: the window's, set by the tab

    def __init__(self, parent=None):
        super().__init__(parent)
        self.source = fire.new_source("?")
        self.frame = {"sheet": dict(plan.BLANK_SHEET)}
        self.selected = []   # the ids of what is selected -- of any collection --, the last one focused: the one whose points can be dragged
        # the overlay catches up with a drag at most this often (DRAG_REDRAW_MS)
        self.drag_timer = QTimer(self)
        self.drag_timer.setSingleShot(True)
        self.drag_timer.setInterval(DRAG_REDRAW_MS)
        self.drag_timer.timeout.connect(self.redraw_after_drag)

    # -- the plan shown --

    def frame_source(self):
        """What the drawing is made over (PlanCanvas.frame_source, v0.115): the fire-protection plan itself where it carries a frame of its own; where it follows a position plan, that plan's frame -- handed over by the tab (`frame`, set_plan, set_frame) -- with the plan's own crop laid over it at every call, so that a crop drawn by the crop tool, taken back or undone is the one shown at once, without the tab having to hand the frame over again."""
        if fire.follows(self.source) is None or self.frame is None:
            return self.source
        frame = dict(self.frame)
        if "crop" in self.source:
            frame["crop"] = self.source["crop"]
        return frame

    def set_source(self, source, project_root, here=None):
        """Shows `source` -- the base class's own, the selection forgotten first: a fire plan's selection is a list of ids, not the position plan's (kind, index)."""
        self.selected = []
        super().set_source(source, project_root, here)

    def set_plan(self, source, frame, project_root, here=None):
        """Shows `source` over `frame` (the followed position plan's, or None for a plan with a frame of its own), its background included -- a plan just opened, or read from its file."""
        self.frame = frame
        self.set_source(source, project_root, here)


    def redraw(self):
        """The overlay rendered by fire_svg over the frame, the crop marked, and the scene laid out as the position plan's is (apply_view_mode, v0.114): the crop shown alone, or the whole page under a veil where «Afficher toute la page» asks for it."""
        frame = self.frame_source()
        sheet = self.sheet_rect()
        window = {"x": 0.0, "y": 0.0, "w": sheet.width(), "h": sheet.height()}
        svg = fire_svg.render(self.source, frame, window=window, editing=True, lang=self.lang, values=self.values)
        self.overlay_renderer.load(QByteArray(svg.encode("utf-8")))
        self.overlay.set_rect(sheet)
        self.crop_item.setRect(self.crop_rect())
        self.apply_view_mode()  # the crop may have moved
        self.update_helpers()

    def redraw_after_drag(self):
        """The drag's timer ran out: the overlay is rendered as the source now is. Its own method -- not `redraw` connected directly -- so that what the timer calls is whatever `redraw` is when it runs."""
        self.redraw()

    # -- the selection --

    def add_text(self, point):
        """A text put down at `point` (issue #43), with an id of its own (fire.next_id): empty, selected, written in the pane -- one step of «Annuler» -- and the tool back to «Sélection»."""
        self.begin_change()
        entry = {"id": fire.next_id(self.source, "texts"), "points": [[plan._clean(round(point[0], 2)), plan._clean(round(point[1], 2))]], "text": ""}
        self.source.setdefault("texts", []).append(entry)
        self.end_change()
        self.tool_done.emit()   # «Sélection» first: choosing a tool lets go of what was selected
        self.select_ids([entry["id"]])

    def entry_by_id(self, eid):
        """The entry `eid` of any collection, or None: an id is unique across all of them."""
        found = fire.entry_of(self.source, eid)
        return None if found is None else self.source[found[0]][found[1]]

    def focused_entry(self):
        return self.entry_by_id(self.selected[-1]) if self.selected else None

    def select_ids(self, ids):
        """Selects the entries `ids`, the last one focused; says so when that is not what was selected."""
        ids = list(dict.fromkeys(ids))
        if ids != list(self.selected):
            self.selected = ids
            self.update_helpers()
            self.selection_changed.emit()

    def select(self, selection):
        """The base class's way to clear a selection (None) or to set one; here a selection is a list of ids."""
        self.select_ids([] if selection is None else selection)

    # -- the selection moved, copied, duplicated (issue #18, plan_canvas_edit.py): every entry selected, by id --

    def has_selection(self):
        return bool(self.selected)

    def translate_selection(self, dx, dy):
        for eid in self.selected:
            fire.translate_entry(self.source, eid, dx, dy)

    def copy_selection(self, dx, dy):
        """A copy of every entry selected, moved by (dx, dy), each with an id of its own; the originals stay selected (D-014). Returns (None, the copies' ids)."""
        return None, [fire.copy_entry(self.source, eid, dx, dy) for eid in list(self.selected)]

    def duplicate_selection(self):
        """«Dupliquer» under «Objet sélectionné» (D-016): a copy of what is selected beside it, one step of «Annuler», the copies selected."""
        if not self.selected:
            return False
        dx, dy = plan_canvas_edit.duplicate_offset(self)
        self.begin_change()
        _kind, made = self.copy_selection(dx, dy)
        self.selected = made
        self.end_change()
        self.selection_changed.emit()
        return True

    def selection_outline(self, dx, dy):
        """What is selected, drawn where (dx, dy) would put it."""
        path = QPainterPath()
        for eid in self.selected:
            found = fire.entry_of(self.source, eid)
            if found is not None:
                path.addPath(self.entry_outline(found[0], self.source[found[0]][found[1]], dx, dy))
        return path

    def entry_outline(self, collection, entry, dx=0.0, dy=0.0):
        """One entry drawn where (dx, dy) would put it: its outline or its line (`outline_of`)."""
        path = QPainterPath()
        rings, closed = self.outline_of(collection, entry)
        for ring in rings:
            if not ring:
                continue
            path.moveTo(QPointF(ring[0][0] + dx, ring[0][1] + dy))
            for x, y in ring[1:]:
                path.lineTo(QPointF(x + dx, y + dy))
            if closed:
                path.closeSubpath()
        return path

    def selected_entries(self):
        """The position plan's question (plan_canvas_editing), answered for a canvas that selects ids: none of the position plan's kind."""
        return []

    def selection_count(self):
        """How many entries are selected."""
        return len(self.selected)

    def select_all(self):
        """Ctrl+A (issue #61): every entry of the plan -- a fire-protection plan has no building outline to leave out."""
        self.select_ids([entry["id"] for collection in fire.ENTRY_COLLECTIONS for entry in self.source.get(collection) or []])

    def clip_outline(self, point):
        """The clip held drawn as Ctrl+V would put it down at `point` (plan_clip.placed)."""
        path = QPainterPath()
        clip = plan_clipboard.current()
        if clip is None or clip.kind != plan_clip.FIRE:
            return path
        for collection, entry in plan_clip.placed(clip, point, self.per_m()):
            path.addPath(self.entry_outline(collection, entry))
        return path

    def delete_selection(self):
        """Everything selected, of whatever kind, removed in one step of the history. A collection the plan does not carry is not made for it."""
        ids = set(self.selected)
        if not ids:
            return
        self.begin_change()
        for collection in fire.ENTRY_COLLECTIONS:
            if collection in self.source:
                self.source[collection] = [entry for entry in self.source[collection] if entry["id"] not in ids]
        if "texts" in self.source and not self.source["texts"]:
            del self.source["texts"]   # the last text gone: the plan is written as before one was placed
        self.selected = []
        self.end_change()
        self.selection_changed.emit()

    # -- tools --

    def tool_kind(self):
        """What the current tool draws: `poly` (an outline), `polyline` (a wall or an escape route's length: as many points as are clicked), `fixed` (a door, an exit, a width: two points, and for a door a click more), or None for the others."""
        if self.tool == "polygon":
            return "poly"
        if self.tool in LINE_TOOLS:
            return "polyline"
        if self.tool in FIXED_TOOLS:
            return "fixed"
        return None

    def snap_index(self, exclude=None, exclude_storey=None):
        """What a point may snap to (PlanCanvas.snap_index): a fire-protection plan has no axis or element -- the walls it is drawn over are an image --, so only the points the plan itself carries (`existing_points`), gathered afresh at every call: the plan has a few dozen entries and a drag moves them. `exclude` is the id of the entry being dragged, which does not snap to itself. The tracking of PlanCanvas.snapped (v0.116) acquires and follows these points as it does a position plan's corners."""
        # since v0.116 also the points of the fire plan shown over this one (PlanCanvas.superposition_snap_points)
        return tracking.PlanSnapIndex(self.source, plan.crop_of(self.frame_source()), axes=False, elements=False, extra_points=self.existing_points(exclude) + self.superposition_snap_points())

    def existing_points(self, exclude=None, source=None):
        """Every point of every entry of the plan -- the outline and the islands of a surface, the points of a wall, a door, an escape route, an exit, a width -- but those of the entry `exclude` (an id). `source` another fire plan's: the one shown over this one (v0.116)."""
        source = self.source if source is None else source
        out = []
        for collection in fire.COLLECTIONS:
            for entry in source.get(collection, []):
                if exclude is not None and entry.get("id") == exclude:
                    continue
                rings = [entry["points"]] + (list(entry.get("holes", [])) if collection == "zones" else [])
                for ring in rings:
                    out.extend((q[0], q[1]) for q in ring)
        return out

    def superposition_svg(self, other, frame):
        """The fire plan shown over this one (PlanCanvas.superposition_svg, v0.116): fire_svg's drawing of it over its whole sheet, without the veil its background would have it drawn over and without its legend -- a box of words that would lie over this plan's own."""
        bare = {key: value for key, value in frame.items() if key != "background"}
        sheet = frame.get("sheet") or plan.BLANK_SHEET
        window = {"x": 0.0, "y": 0.0, "w": float(sheet["width"]), "h": float(sheet["height"])}
        svg = fire_svg.render(other, bare, window=window, editing=False, lang=self.lang)
        start, end = svg.find(fire_svg.LEGEND_OPEN), svg.find(fire_svg.LEGEND_CLOSE)
        if 0 <= start < end:
            svg = svg[:start] + svg[end + len(fire_svg.LEGEND_CLOSE):]
        return svg

    def superposition_points(self, other, frame):
        """The fire plan shown over this one's points: every point of its entries (existing_points)."""
        return [(float(x), float(y)) for x, y in self.existing_points(source=other)]

    def click_point(self, raw, shift):
        """What a left click at `raw` does (PlanCanvas.click_point): the tools that draw with clicks put a point down."""
        if self.tool == "polygon" or self.tool in LINE_TOOLS or self.tool in FIXED_TOOLS:
            self.add_point(raw, shift)


    # -- drawing --

    def add_point(self, point, shift=False):
        """A click of a drawing tool. The polygon tool: a point of the outline being drawn, or its end -- a click on the first point, with three down, closes it; a click on the last one ends it. The wall and the escape route's length: a point of the line being drawn, and a click on its last point ends it -- with a single point down the line has no end yet, and the click waits for the next. The door, the exit and the width: see add_fixed."""
        if self.tool in FIXED_TOOLS:
            self.add_fixed(point, shift)
            return
        anchor = self.drawing[-1] if self.drawing else None
        p, _kind = self.snapped(point, anchor, shift)
        tol = self.tolerance()
        if self.tool in LINE_TOOLS:
            if self.drawing and math.dist(p, self.drawing[-1]) <= tol * 0.75:
                if len(self.drawing) >= 2:
                    self.finish_drawing()
                return
            self.drawing.append(p)
            self.update_helpers()
            return
        if self.drawing and math.dist(p, self.drawing[-1]) <= tol * 0.75:
            self.finish_drawing()
            return
        if len(self.drawing) >= 3 and math.dist(p, self.drawing[0]) <= tol:
            self.finish_drawing()
            return
        self.drawing.append(p)
        self.update_helpers()

    def add_fixed(self, point, shift=False):
        """A click of the door, the emergency exit or the width tool. The first two are the entry's two points -- a door's hinge and its other jamb, an exit's tail and its tip, a width's two sides of the passage --, the second ending the exit and the width. A door takes a third click that is no point of it: the side of the line hinge -> jamb it opens to (fire.side_of), taken where it is."""
        if self.tool == "door" and len(self.drawing) == FIXED_POINTS:
            self.finish_fixed(tuple(point))
            return
        anchor = self.drawing[-1] if self.drawing else None
        p, _kind = self.snapped(point, anchor, shift)
        if self.drawing and math.dist(p, self.drawing[-1]) <= self.tolerance() * 0.75:
            return   # the same point twice: the entry waits for its other end
        self.drawing.append(p)
        if self.tool != "door" and len(self.drawing) == FIXED_POINTS:
            self.finish_fixed()
            return
        self.update_helpers()

    def finish_fixed(self, side_point=None):
        """The door, the exit or the width just drawn, saved and selected; one step of the history. A door carries the fire resistance in `door_class` -- and none where that is None --, the way it opens in `door_kind`, and the side `side_point` (the third click) lies on."""
        points = fire.rounded(self.drawing[:FIXED_POINTS])
        self.drawing = []
        self.cursor = None
        collection = FIXED_TOOLS[self.tool]
        entry = {"id": fire.next_id(self.source, collection), "points": points}
        if self.tool == "door":
            entry["kind"] = self.door_kind
            if self.door_class is not None:
                entry["class"] = self.door_class
            entry["side"] = fire.side_of(points[0], points[1], side_point)
        self.begin_change()
        self.source.setdefault(collection, []).append(entry)
        self.selected = [entry["id"]]
        self.end_change()
        self.selection_changed.emit()
        self.update_helpers()

    def finish_drawing(self):
        """Ends the outline being drawn: at least three points, none of them the one before it clicked twice, and a surface. What is left of fewer is nothing. The line of the wall or the escape route's length ends the same way, with at least two points. A door, an exit or a width not yet drawn is given up."""
        if self.tool in LINE_TOOLS and self.drawing:
            self.finish_line()
            return
        if self.tool != "polygon" or not self.drawing:
            self.drawing = []
            self.cursor = None
            self.update_helpers()
            return
        tol = self.tolerance() * 0.5
        points = []
        for p in self.drawing:
            if not points or math.dist(p, points[-1]) > tol:
                points.append(p)
        if len(points) > 3 and math.dist(points[0], points[-1]) <= tol:
            points.pop()
        self.drawing = []
        self.cursor = None
        if len(points) >= 3 and fire.ring_area(points) > fire.SAME_POINT:
            self.add_zone(points)
        self.update_helpers()

    def add_zone(self, points):
        """The outline drawn, saved as a surface of the kind in `zone_kind` and selected; one step of the history."""
        zone = {"id": fire.next_id(self.source, "zones"), "kind": self.zone_kind, "points": fire.rounded(points)}
        self.begin_change()
        self.source["zones"].append(zone)
        self.selected = [zone["id"]]
        self.end_change()
        self.selection_changed.emit()

    def finish_line(self):
        """Ends the wall or the escape route's length being drawn: a point clicked twice is one point, and what is left of fewer than two is nothing."""
        tol = max(self.tolerance() * 0.5, fire.SAME_POINT)
        points = []
        for p in self.drawing:
            if not points or math.dist(p, points[-1]) > tol:
                points.append(p)
        self.drawing = []
        self.cursor = None
        if len(points) >= 2:
            self.add_line(points)
        self.update_helpers()

    def add_line(self, points):
        """The line drawn, saved as a wall of the fire resistance in `wall_class` or as an escape route's length, and selected; one step of the history. The id is the next free one of its kind: a deleted entry's number is not given again."""
        if self.tool == "wall":
            collection = "walls"
            entry = {"id": fire.next_id(self.source, collection), "class": self.wall_class, "points": fire.rounded(points)}
        else:
            collection = "routes"
            entry = {"id": fire.next_id(self.source, collection), "points": fire.rounded(points)}
        self.begin_change()
        self.source.setdefault(collection, []).append(entry)
        self.selected = [entry["id"]]
        self.end_change()
        self.selection_changed.emit()

    # -- the mouse and the keys --

    def mousePressEvent(self, event):
        self.setFocus()
        button = event.button()
        if button == Qt.MouseButton.MiddleButton or (button == Qt.MouseButton.LeftButton and (self.tool == "pan" or self.space_down)):
            self.start_pan(event)
            return
        if button == Qt.MouseButton.RightButton:
            if self.typing:
                self.hide_distance()
            elif self.drawing:
                self.drawing = []
                self.cursor = None
                self.update_helpers()
            elif self.acquired:
                self.reset_tracking()   # the next right click lets go of what was acquired (the static models' tab's rule)
                self.update_helpers()
            else:
                self.select_ids([])
            return
        if button != Qt.MouseButton.LeftButton:
            return
        if self.tool in ("crop", "calibrate", plan_canvas.ALIGN_TOOL):
            super().mousePressEvent(event)   # the position plan's own: the crop and the calibration edit the frame fields of the source, «Aligner» the superposition's offset (v0.116)
            return
        self.hide_distance()
        raw = self.scene_point(event)
        shift = bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier)
        ctrl = bool(event.modifiers() & Qt.KeyboardModifier.ControlModifier)
        if self.tool == plan_canvas_tools.RULER:
            plan_canvas_tools.ruler_click(self, raw, shift)   # a measure shown and kept nowhere (issue #9)
            return
        if plan_canvas_edit.handles(self.tool):
            plan_canvas_edit.click(self, raw, shift)   # «Déplacer», «Copier» (issue #18)
            return
        if self.tool == "select":
            self.press_select(raw, ctrl)
        elif self.tool == plan_canvas.TEXT_TOOL:
            self.add_text(raw)   # a text placed with the Text tool (issue #43)
        elif self.tool == "polygon" or self.tool in LINE_TOOLS or self.tool in FIXED_TOOLS:
            self.add_point(raw, shift)
        self.update_helpers()

    def legend_under(self, raw):
        """Whether `raw` lies in the legend's box -- the legend is drawn over everything, so a press there means the legend."""
        box = fire_svg.legend_box(self.source, self.frame_source(), self.lang)
        if box is None:
            return False
        x, y, w, h = box
        return x <= raw[0] <= x + w and y <= raw[1] <= y + h

    def text_under(self, raw):
        """The frame (fire_svg.text_frames') of the text drawn under `raw`, or None -- a position plan's `label_under`. A text is drawn over what it names and is asked for fresh at every press and every movement of the pointer: it costs a pass over the entries, and a cache would be one more thing an in-place edit has to remember to empty."""
        return fire_svg.hit_text(self.source, self.frame_source(), raw, editing=True, slack=0.5 * self.tolerance())

    def press_select(self, raw, ctrl):
        """A press with the selection tool. On a point of the focused entry it takes the point, which a drag then moves; on a text it takes the text, which a drag then moves clear of what it hides -- and selects its entry --; in the legend's box it takes the legend, drawn over everything and no entry of the plan -- it is not selected and Delete does not remove it --; else a click selects what lies under it (fire.hit); Ctrl toggles it in the selection and, on nothing, a plain click clears it.

        A text is drawn over every symbol and the legend over the texts, but a press is asked of the texts first: a text lying in the legend's box is the plan's, not the legend's. With Ctrl a text is only toggled in the selection -- no drag starts in a set the engineer is still building --, which is how an escape route is chosen by its length written beside it."""
        tol = self.tolerance()
        if self.clipped() and not self.shown_rect().adjusted(-tol, -tol, tol, tol).contains(QPointF(*raw)):
            if not ctrl:
                self.select_ids([])  # nothing outside the crop is shown, and nothing there is taken (the position plan's rule, v0.114)
            return
        entry = self.focused_entry()
        if entry is not None and not ctrl:
            vertex = plan.nearest_vertex(entry, raw, self.tolerance())
            if vertex is not None:
                self.drag = {"kind": "vertex", "id": entry["id"], "vertex": vertex, "moved": False}
                return
        placed = plan_svg.hit_text(self.source, raw, 0.5 * tol, self.values)
        if placed is not None:
            # a text placed with the Text tool (issue #43), drawn over the concept: taken, and a drag moves it whole
            eid = self.source["texts"][placed]["id"]
            if ctrl:
                self.select_ids([e for e in self.selected if e != eid] + ([] if eid in self.selected else [eid]))
                return
            self.select_ids([eid])
            self.drag = {"kind": "placed-text", "id": eid, "start": raw, "points": [list(p) for p in self.source["texts"][placed]["points"]], "moved": False}
            return
        text = self.text_under(raw)
        if text is not None:
            eid = text["id"]
            if ctrl:
                self.select_ids([e for e in self.selected if e != eid] + ([] if eid in self.selected else [eid]))
                return
            self.select_ids([eid])
            offset = self.entry_by_id(eid).get("label_offset") or (0.0, 0.0)
            self.drag = {"kind": "text", "id": eid, "start": raw, "offset": (float(offset[0]), float(offset[1])), "moved": False}
            return
        if self.legend_under(raw):
            legend = self.source["legend"]
            self.drag = {"kind": "legend", "start": raw, "origin": (float(legend["x"]), float(legend["y"])), "moved": False}
            return
        eid = fire.hit(self.source, raw, self.tolerance(), band=fire.band_width(self.frame_source()))
        if eid is None:
            if not ctrl:
                self.select_ids([])
            return
        if ctrl:
            self.select_ids([e for e in self.selected if e != eid] + ([] if eid in self.selected else [eid]))
        else:
            self.select_ids([eid])

    def schedule_redraw(self):
        """While something is dragged the overlay is rendered at most every DRAG_REDRAW_MS: a timer already running is left alone, so the render it ends with is of the source as it then is."""
        if not self.drag_timer.isActive():
            self.drag_timer.start()

    def mouseMoveEvent(self, event):
        if self.panning is not None or (self.drag is not None and self.drag["kind"] == "crop") or (self.drag is None and self.tool == plan_canvas.ALIGN_TOOL):
            super().mouseMoveEvent(event)   # the position plan's own: the pan, the crop's rectangle and «Aligner»'s line (v0.116)
            return
        raw = self.scene_point(event)
        shift = bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier)
        if self.tool == plan_canvas_tools.RULER:
            plan_canvas_tools.ruler_move(self, raw, shift)
            return
        if plan_canvas_edit.handles(self.tool) and self.drag is None:
            plan_canvas_edit.move(self, raw, shift)
            return
        drag = self.drag
        if drag is not None and event.buttons() & Qt.MouseButton.LeftButton:
            if drag["kind"] == "legend":
                self.drag_legend(drag, raw)
                return
            if drag["kind"] == "text":
                self.drag_text(drag, raw, shift)
                return
            if drag["kind"] == "placed-text":
                entry = self.entry_by_id(drag["id"])
                if entry is not None:
                    if not drag["moved"]:
                        drag["moved"] = True
                        self.begin_change()
                    entry["points"] = plan.shifted(drag["points"], raw[0] - drag["start"][0], raw[1] - drag["start"][1])
                    self.redraw()
                return
            entry = self.entry_by_id(drag["id"])
            if entry is None:
                return
            if not drag["moved"]:
                drag["moved"] = True
                self.begin_change()
            points = entry["points"]
            j = drag["vertex"]
            anchor = points[j - 1] if j > 0 else points[1]
            p, kind = self.snapped(raw, anchor, shift, exclude=drag["id"])
            points[j] = [plan_canvas._round(p[0]), plan_canvas._round(p[1])]
            self.show_snap(p, kind)
            self.note_hover(p, kind)
            self.pointer.emit(p[0], p[1], "")
            # the outline and the handles follow the pointer at once; the overlay, with its lengths and its areas, every DRAG_REDRAW_MS
            self.update_helpers()
            self.schedule_redraw()
            return
        if self.typing:
            return   # a distance is being typed: the cursor stays where Tab found it
        if self.tool in DRAWING_TOOLS:
            anchor = self.drawing[-1] if self.drawing else None
            if self.tool == "door" and len(self.drawing) == FIXED_POINTS:
                p, kind = tuple(raw), None   # the side the door opens to is where the pointer is, not a point snapped to
                self.locked = []
            else:
                p, kind = self.snapped(raw, anchor, shift)
            self.cursor = p
            self.show_snap(p, kind)
            self.note_hover(p, kind)
            self.pointer.emit(p[0], p[1], "")
            self.update_helpers()
        else:
            self.pointer.emit(raw[0], raw[1], "")
            if self.tool == "select" and not self.space_down and drag is None:
                # over a text, the pointer says that it can be moved, as it does over a position number
                over = self.text_under(raw) is not None
                if over != self._over_label:
                    self._over_label = over
                    self.viewport().setCursor(Qt.CursorShape.SizeAllCursor if over else Qt.CursorShape.ArrowCursor)

    def drag_text(self, drag, raw, shift=False):
        """A text dragged clear of what it hides: its entry's `label_offset` is how far it stands from its own place, so it goes on following its entry when the entry is moved or reshaped. Brought back within the pick tolerance of its own place it goes back to following it, and the key goes. The first movement past half the pick tolerance starts the step of the history; a press that does not move leaves none. Shift keeps the move horizontal, vertical or at 45°."""
        if not drag["moved"]:
            if math.dist(raw, drag["start"]) < self.tolerance() * 0.5:
                return
            drag["moved"] = True
            self.begin_change()
        entry = self.entry_by_id(drag["id"])
        if entry is None:
            return
        dx, dy = raw[0] - drag["start"][0], raw[1] - drag["start"][1]
        if shift:
            moved = plan.constrain(drag["start"], raw)
            dx, dy = moved[0] - drag["start"][0], moved[1] - drag["start"][1]
        ox, oy = drag["offset"][0] + dx, drag["offset"][1] + dy
        if math.hypot(ox, oy) <= self.tolerance():
            entry.pop("label_offset", None)
        else:
            entry["label_offset"] = [plan_canvas._round(ox), plan_canvas._round(oy)]
        self.pointer.emit(raw[0], raw[1], "")
        # the text's box follows the pointer at once; the overlay, with the text where it now stands, every DRAG_REDRAW_MS
        self.update_helpers()
        self.schedule_redraw()

    def drag_legend(self, drag, raw):
        """The legend dragged: it follows the pointer from where it was, to a hundredth of a sheet unit. The first movement past half the pick tolerance starts the step of the history; a press that does not move leaves none."""
        if not drag["moved"]:
            if math.dist(raw, drag["start"]) < self.tolerance() * 0.5:
                return
            drag["moved"] = True
            self.begin_change()
        legend = self.source["legend"]
        legend["x"] = round(drag["origin"][0] + raw[0] - drag["start"][0], fire.DECIMALS) + 0.0
        legend["y"] = round(drag["origin"][1] + raw[1] - drag["start"][1], fire.DECIMALS) + 0.0
        self.pointer.emit(raw[0], raw[1], "")
        self.update_helpers()
        self.schedule_redraw()

    def mouseReleaseEvent(self, event):
        if self.panning is not None or (self.drag is not None and self.drag["kind"] == "crop"):
            super().mouseReleaseEvent(event)
            return
        drag, self.drag = self.drag, None
        self.drag_timer.stop()   # end_change renders the final state; a render still waiting would only repeat it
        self.show_snap((0, 0), None)
        if drag is not None and drag.get("moved"):
            self.end_change()

    def mouseDoubleClickEvent(self, event):
        if (self.tool == "polygon" or self.tool in LINE_TOOLS) and self.drawing:
            self.finish_drawing()
            return
        if self.tool in FIXED_TOOLS:
            # a quick second click on a tool of two or three clicks arrives as a double-click: it is the entry's other end, and is not lost
            self.mousePressEvent(event)
            return
        super().mouseDoubleClickEvent(event)

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key.Key_Tab and self.locked and not self.typing:
            self.show_distance()
            return
        if key == Qt.Key.Key_Escape:
            if self.ruler:
                plan_canvas_tools.clear_ruler(self)
            elif self.typing:
                self.hide_distance()
                self.update_helpers()
            elif self.drawing:
                self.drawing = []
                self.cursor = None
                self.update_helpers()
            elif self.acquired:
                self.reset_tracking()   # Escape lets go of what was acquired before it leaves the tool
                self.update_helpers()
            elif self.tool != "select":
                self.tool_done.emit()
            else:
                self.select_ids([])
            return
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.finish_drawing()
            return
        if key == Qt.Key.Key_Backspace and self.drawing:
            self.drawing.pop()
            self.update_helpers()
            return
        if key == Qt.Key.Key_Delete and self.selected and not self.drawing:
            self.delete_selection()
            return
        super().keyPressEvent(event)   # Space, which borrows the hand, and the keys the view itself reads

    # -- what only the editor shows --

    def outline_of(self, collection, entry):
        """The closed outlines the selection of `entry` is drawn round, or its open line: ([rings], closed). A surface its outline and its islands; a door and an exit their shape; a wall, an escape route's length and a width their line."""
        if collection == "zones":
            return [entry["points"]] + list(entry.get("holes", [])), True
        if collection == "doors":
            return [fire.door_shape(entry)], True
        if collection == "exits":
            return [fire.exit_shape(entry["points"])], True
        if collection == "texts":
            # a text placed with the Text tool (issue #43): the box it is written in
            for i, (x, y), hw, hh, _lines, _size in plan_svg.text_frames(self.source, self.values):
                if self.source["texts"][i] is entry:
                    return [[(x - hw, y - hh), (x + hw, y - hh), (x + hw, y + hh), (x - hw, y + hh)]], True
            return [], True
        return [entry["points"]], False

    def text_box(self, eid):
        """The four corners of the box the text of entry `eid` is drawn in, where it now stands and turned as it is read -- or None where that entry writes no text. What the outline of a text being dragged is drawn along."""
        for item in fire_svg.text_frames(self.source, self.frame_source(), editing=True):
            if item["id"] == eid:
                (cx, cy), hw, hh = item["at"], item["hw"], item["hh"]
                a = math.radians(item["angle"])
                c, s = math.cos(a), math.sin(a)
                return [(cx + u * c - v * s, cy + u * s + v * c) for u, v in ((-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh))]
        return None

    def preview_shape(self):
        """The closed shape the door or the exit being drawn will have, following the pointer, or None: a door once its two points are down, with the side the pointer is on; an exit once its tail is."""
        if self.cursor is None:
            return None
        if self.tool == "door" and len(self.drawing) == FIXED_POINTS:
            door = {"kind": self.door_kind, "points": [list(p) for p in self.drawing], "side": fire.side_of(self.drawing[0], self.drawing[1], self.cursor)}
            return fire.door_shape(door)
        if self.tool == "exit" and len(self.drawing) == 1 and math.dist(self.drawing[0], self.cursor) > 0:
            return fire.exit_shape([list(self.drawing[0]), list(self.cursor)])
        return None

    def preview_colour(self):
        """The colour the entry being drawn will have, where it is known: a wall's and a door's fire resistance, the escape routes' green."""
        if self.tool == "wall":
            return QColor(fire_svg.wall_colour(self.wall_class))
        if self.tool == "route":
            return QColor(fire_svg.route_colour())
        if self.tool == "door":
            door = {"kind": self.door_kind}
            if self.door_class is not None:
                door["class"] = self.door_class
            return QColor(fire_svg.door_colour(door) or fire_svg.INK)
        if self.tool == "exit":
            return QColor(fire_svg.colour_of("exit"))
        if self.tool == "width":
            return QColor(fire_svg.colour_of("width"))
        if self.tool == "calibrate":
            return QColor(plan_svg.AXIS_COLOUR)
        return QColor(fire_svg.ZONE_COLOUR)

    def update_helpers(self):
        scene = self.scene()
        for handle in self.handles:
            scene.removeItem(handle)
        self.handles = []
        entries = {entry["id"]: (collection, entry) for collection in fire.ENTRY_COLLECTIONS for entry in self.source.get(collection, [])}
        # an undo may have taken a selected entry away: what is selected is what is there
        self.selected = [eid for eid in self.selected if eid in entries]
        path = QPainterPath()
        for eid in self.selected:
            collection, entry = entries[eid]
            rings, closed = self.outline_of(collection, entry)
            for ring in rings:
                if closed:
                    path.addPolygon(QPolygonF([QPointF(x, y) for x, y in ring]))
                    path.closeSubpath()
                else:
                    # a wall, an escape route's length or a width is outlined along its line, which stays open
                    path.moveTo(QPointF(ring[0][0], ring[0][1]))
                    for x, y in ring[1:]:
                        path.lineTo(QPointF(x, y))
        focused = entries[self.selected[-1]][1] if self.selected else None
        if focused is not None:
            for x, y in focused["points"]:
                handle = QGraphicsRectItem(-4, -4, 8, 8)
                handle.setPos(QPointF(x, y))
                handle.setBrush(QBrush(theme.qcolor("paper")))
                handle.setPen(plan_canvas._cosmetic(plan_canvas.SELECT_COLOUR, 1.6))
                handle.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations)
                handle.setZValue(21)
                scene.addItem(handle)
                self.handles.append(handle)
        self.select_item.setPath(path)

        preview = QPainterPath()
        colour = QColor(fire_svg.ZONE_COLOUR)
        unit = 2.5 / max(self.transform().m11(), 1e-9)
        if self.drag is not None and self.drag["kind"] == "crop":
            (x0, y0), (x1, y1) = self.drag["start"], self.drag["now"]
            preview.addRect(QRectF(QPointF(x0, y0), QPointF(x1, y1)).normalized())
            colour = plan_canvas.CROP_COLOUR
        elif self.drag is not None and self.drag["kind"] == "legend":
            # the legend follows the pointer as an outline; the overlay renders it in its new place a moment later
            box = fire_svg.legend_box(self.source, self.frame_source(), self.lang)
            if box is not None:
                preview.addRect(QRectF(*box))
            colour = plan_canvas.SELECT_COLOUR
        elif self.drag is not None and self.drag["kind"] == "text":
            # the text's box follows the pointer as an outline, turned as the text is; the overlay writes it in its new place a moment later
            shape = self.text_box(self.drag["id"])
            if shape is not None:
                preview.addPolygon(QPolygonF([QPointF(x, y) for x, y in shape]))
                preview.closeSubpath()
            colour = plan_canvas.SELECT_COLOUR
        elif plan_canvas_edit.handles(self.tool):
            preview, colour = plan_canvas_edit.preview(self)
        elif self.drawing:
            colour = self.preview_colour()
            shape = self.preview_shape()
            if shape is not None:
                preview.addPolygon(QPolygonF([QPointF(x, y) for x, y in shape]))
                preview.closeSubpath()
            else:
                points = list(self.drawing) + ([self.cursor] if self.cursor is not None else [])
                preview.moveTo(QPointF(*points[0]))
                for q in points[1:]:
                    preview.lineTo(QPointF(*q))
                if self.tool == "polygon" and len(points) > 2:
                    preview.lineTo(QPointF(*points[0]))
            for q in self.drawing:
                preview.addEllipse(QPointF(*q), unit, unit)
        self.preview.setPen(plan_canvas._cosmetic(colour, 3 if self.tool == "wall" and self.drawing else 2, [4, 3]))
        self.preview.setPath(preview)
        self.update_track()
