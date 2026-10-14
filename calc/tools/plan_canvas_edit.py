"""The drawing tabs' editing tools (issue #18, docs/ui/window.md §10quater): «Déplacer» and «Copier» an object of the plan, and «Ligne d'aide», the construction aids the position plan is laid out with.

The engineer, 09.10.2026: «Ajouter dans l'onglet Plan de positions les outils déplacer, copier et ligne d'aide à la construction.» -- and, asked: Copier puts down copies one after another until Escape (D-014), the aids are horizontal, vertical, through two points, or parallel to a line at a distance (D-008), and the position plan alone has the aids for now (D-015).

The tools live here, beside plan_canvas_tools.py's ruler and dimensions, and act through what the canvas says of its selection -- `has_selection`, `translate_selection`, `copy_selection`, `selection_outline` --, which the position plan's canvas answers by plan.translate_entry and plan.copy_entry and the fire-protection plan's by fire.translate_entry and fire.copy_entry: the same gesture on two plans that hold different things (rule 16). Every change is one step of «Annuler» (`begin_change`, `end_change`).

**Déplacer**: the base point, then where it goes; the object moved, and the tool given back. **Copier**: the base point, then a copy at every click, the original still selected, until Escape. Both points snap and track as every point of the plan does (PlanCanvas.snapped); Shift keeps the move horizontal, vertical or at 45°.
"""

import math

from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor, QPainterPath

import theme  # the canvases' colours are tokens of theme.json (issue #29)
from domains import lines
from domains import plan as model

MOVE, COPY = "move", "copy"
EDIT_TOOLS = (MOVE, COPY)
# The aid tools, by the kind of aid each makes.
AID_TOOLS = {"aid-h": "horizontal", "aid-v": "vertical", "aid-2p": "two-points", "aid-par": "parallel"}
EDIT_COLOUR = theme.qcolor("plan-select")   # the selection's own orange (plan_canvas.SELECT_COLOUR): what is moved is what was selected
AID_COLOUR = theme.qcolor("plan-track")     # the tracking's blue (plan_canvas.TRACK_COLOUR): an aid is a drawing aid, as a track is


def handles(tool):
    """Whether `tool` is one of this module's."""
    return tool in EDIT_TOOLS or tool in AID_TOOLS


def click(canvas, raw, shift):
    """A left click with one of this module's tools."""
    if tool_is_aid(canvas.tool):
        return aid_click(canvas, raw, shift)
    if not canvas.has_selection():
        canvas.edit_refused.emit(canvas.tool)   # nothing selected: the tab says to select first
        return
    base = canvas.drawing[0] if canvas.drawing else None
    p, _kind = canvas.snapped(raw, base, shift)
    if base is None:
        canvas.drawing = [tuple(p)]
        canvas.cursor = tuple(p)
        canvas.update_helpers()
        return
    dx, dy = p[0] - base[0], p[1] - base[1]
    if math.hypot(dx, dy) <= canvas.tolerance() * 0.25:
        return   # the base point clicked again: nothing to move by
    canvas.begin_change()
    if canvas.tool == MOVE:
        canvas.translate_selection(dx, dy)
        canvas.drawing = []
        canvas.cursor = None
        canvas.end_change()
        canvas.tool_done.emit()
    else:
        canvas.copy_selection(dx, dy)
        canvas.end_change()   # the base stays: the next click is the next copy (D-014)
    canvas.update_helpers()


def move(canvas, raw, shift):
    """The pointer moved with one of this module's tools: where the next click would put the point."""
    anchor = canvas.drawing[-1] if canvas.drawing and (canvas.tool in EDIT_TOOLS or canvas.tool == "aid-2p") else None
    p, snap = canvas.snapped(raw, anchor, shift)
    canvas.cursor = tuple(p)
    canvas.show_snap(p, snap)
    canvas.note_hover(p, snap)
    canvas.pointer.emit(p[0], p[1], canvas.readout(snap))
    canvas.update_helpers()


def tool_is_aid(tool):
    return tool in AID_TOOLS


def aid_click(canvas, raw, shift):
    """«Ligne d'aide»: horizontal or vertical through the point clicked; through two points; or parallel to the line clicked -- an axis, an aid or an element's side --, at the distance the tab asks for, on the side of the next click."""
    kind = AID_TOOLS[canvas.tool]
    if kind == "parallel":
        if not canvas.drawing:
            found = canvas.line_under(raw)
            if found is None:
                canvas.edit_refused.emit(canvas.tool)   # no line under the click to be parallel to
                return
            distance = canvas.ask_distance() if canvas.ask_distance is not None else None
            if distance is None:
                return
            canvas.drawing = [tuple(found[0])]
            canvas.aid_pending = (found[1], distance)
            canvas.update_helpers()
            return
        angle, distance = canvas.aid_pending
        point, angle = lines.parallel_at(canvas.drawing[0], angle, distance, raw)
        canvas.drawing, canvas.aid_pending = [], None
        canvas.add_aid(kind, point, angle)
        return
    p, _snap = canvas.snapped(raw, canvas.drawing[-1] if canvas.drawing else None, shift)
    if kind in ("horizontal", "vertical"):
        canvas.add_aid(kind, p, 0.0 if kind == "horizontal" else 90.0)
        return
    if not canvas.drawing:
        canvas.drawing = [tuple(p)]
        canvas.update_helpers()
        return
    made = lines.through(canvas.drawing[0], p)
    if made is None:
        return
    canvas.drawing = []
    canvas.add_aid(kind, made[0], made[1])


def preview(canvas):
    """(path, colour) of what the tool would do at the pointer: the selection's outline where it would go, or the aid across the frame."""
    path = QPainterPath()
    window = model.crop_of(canvas.frame_source())
    if canvas.tool in EDIT_TOOLS:
        if canvas.drawing and canvas.cursor is not None:
            base = canvas.drawing[0]
            path = canvas.selection_outline(canvas.cursor[0] - base[0], canvas.cursor[1] - base[1])
        return path, EDIT_COLOUR
    kind = AID_TOOLS[canvas.tool]
    line = None
    if kind in ("horizontal", "vertical") and canvas.cursor is not None:
        line = (canvas.cursor, 0.0 if kind == "horizontal" else 90.0)
    elif kind == "two-points" and canvas.drawing and canvas.cursor is not None:
        line = lines.through(canvas.drawing[0], canvas.cursor)
    elif kind == "parallel" and canvas.drawing and canvas.cursor is not None and canvas.aid_pending:
        line = lines.parallel_at(canvas.drawing[0], canvas.aid_pending[0], canvas.aid_pending[1], canvas.cursor)
    if line is not None:
        segment = model.axis_segment({"point": list(line[0]), "angle": line[1]}, window)
        if segment:
            path.moveTo(QPointF(*segment[0]))
            path.lineTo(QPointF(*segment[1]))
    return path, AID_COLOUR


def aids_path(source, window):
    """Every construction aid of `source` across `window`: what the canvas draws, thin and dashed, and the report never does."""
    path = QPainterPath()
    for aid in source.get("aids") or []:
        segment = model.axis_segment(aid, window)
        if segment:
            path.moveTo(QPointF(*segment[0]))
            path.lineTo(QPointF(*segment[1]))
    return path


def duplicate_offset(canvas):
    """How far «Dupliquer» puts the copy from its original: a fiftieth of the frame's diagonal, down and right -- seen at once, and clear of it."""
    window = model.crop_of(canvas.frame_source())
    step = math.hypot(window["w"], window["h"]) / 50.0
    return step, step
