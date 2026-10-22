"""The building's outline on the position plan's canvas (issue #54, docs/ui/tab-plans.md §10quater; spec docs/requirements/completed/2026-10-13-plan-positions-centre-rigidite-centre-masse.md): the tool that draws it, and how «Sélection» takes it, reshapes it and moves it.

The engineer, 12.10.2026: «Ajouter un outil pour dessiner le contour du bâtiment (un polygone) sur le plan» -- the mass centre M being its area centroid (calc/domains/plan_centres.py). The outline is drawn as every area of the plan is -- a click a corner, the first corner or Enter to close it, the same snapping, tracking and Shift --, which is why the tool answers `poly` to `PlanCanvas.tool_kind` and nothing of the drawing is written twice. What is its own is here: a plan has **one** outline, so a new one takes the place of the one it had (D-010); it is taken by its **edge** and never by its inside, which is the whole building (ARCH-007); and it is no element -- it carries no position, no number and no symbol --, so it is a selection kind of its own, `outline`, an index into the source's `outlines` (plan.ENTRY_LISTS).

Functions over the canvas, as plan_canvas_tools.py's ruler and plan_canvas_edit.py's «Déplacer» are: the fire-protection plan's canvas inherits the position plan's, and a source that has no `outlines` makes every one of them answer «nothing».
"""

from PySide6.QtCore import QPointF

from domains import plan as model
from domains import plan_centres

TOOL = "outline"
KIND = "outline"
# The two drags of a selected outline: the whole of it, and one corner.
DRAG_ALL, DRAG_VERTEX = "outline", "outline-vertex"


def selected(canvas):
    """The outline selected ({points}), or None."""
    outlines = canvas.source.get(model.ENTRY_LISTS[KIND]) or []
    if canvas.selection and canvas.selection[0] == KIND and canvas.selection[1] < len(outlines):
        return outlines[canvas.selection[1]]
    return None


def snap_points(canvas, dragged=None):
    """The outline's corners, which a point being drawn snaps to behind «Accrocher aux éléments» -- a wall's end put on the building's corner. None of them while the outline's own corner is dragged (`dragged` is then (KIND, index)): a corner is no target of its own."""
    if dragged is not None and dragged[0] == KIND:
        return []
    return [(float(x), float(y)) for outline in canvas.source.get(model.ENTRY_LISTS[KIND]) or [] for x, y in outline.get("points") or []]


def add(canvas, points):
    """The outline just drawn, written into the source and selected: the plan has one, so it takes the place of the one the plan had -- one step of «Annuler», which brings the old one back. The tool is given back: there is no second outline to draw."""
    canvas.begin_change()
    canvas.source[model.ENTRY_LISTS[KIND]] = [{"points": model.shifted(points, 0, 0)}]
    canvas.selection = (KIND, 0)
    canvas.end_change()
    canvas.selection_changed.emit()
    canvas.tool_done.emit()


def press_vertex(canvas, raw, tol):
    """A press with «Sélection» on a corner of the outline selected: the corner is taken, to be dragged. True where it was."""
    outline = selected(canvas)
    if outline is None:
        return False
    vertex = model.nearest_vertex(outline, raw, tol)
    if vertex is None:
        return False
    canvas.drag = {"kind": DRAG_VERTEX, "index": canvas.selection[1], "vertex": vertex, "moved": False}
    return True


def press_edge(canvas, raw, tol):
    """A press with «Sélection» on the outline's edge: it is selected, and taken to be moved whole. True where it was."""
    index = plan_centres.hit_outline(canvas.source, raw, tol)
    if index is None:
        return False
    canvas.select((KIND, index))
    canvas.drag = {"kind": DRAG_ALL, "index": index, "start": raw, "moved": False,
                   "points": [list(p) for p in canvas.source[model.ENTRY_LISTS[KIND]][index]["points"]]}
    return True


def follow(canvas, drag, raw, shift):
    """One of the outline's two drags, followed to the pointer: the whole of it by the pointer's move -- Shift keeping it horizontal, vertical or at 45° --, or one corner, snapped and tracked as a wall's corner is. True where `drag` is one of the two."""
    if drag["kind"] == DRAG_ALL:
        dx, dy = raw[0] - drag["start"][0], raw[1] - drag["start"][1]
        if shift:
            moved = model.constrain(drag["start"], raw)
            dx, dy = moved[0] - drag["start"][0], moved[1] - drag["start"][1]
        canvas.source[model.ENTRY_LISTS[KIND]][drag["index"]]["points"] = model.shifted(drag["points"], dx, dy)
        canvas.pointer.emit(raw[0], raw[1], "")
        return True
    if drag["kind"] == DRAG_VERTEX:
        points = canvas.source[model.ENTRY_LISTS[KIND]][drag["index"]]["points"]
        j = drag["vertex"]
        p, kind = canvas.snapped(raw, points[j - 1], shift, exclude_storey=(KIND, drag["index"]))
        points[j] = model.shifted([p], 0, 0)[0]
        canvas.show_snap(p, kind)
        canvas.note_hover(p, kind)
        canvas.pointer.emit(p[0], p[1], canvas.readout(kind))
        return True
    return False


def highlight(canvas, path):
    """The outline selected, added to the selection's `path` -- its corners joined and closed -- with a handle on each corner. True where one is selected."""
    outline = selected(canvas)
    if outline is None or not outline.get("points"):
        return False
    points = [QPointF(float(x), float(y)) for x, y in outline["points"]]
    path.moveTo(points[0])
    for q in points[1:]:
        path.lineTo(q)
    path.closeSubpath()
    for q in points:
        canvas._add_handle(q)
    return True
