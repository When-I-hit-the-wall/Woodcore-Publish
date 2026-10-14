"""SchemaCanvas's placing -- what a click puts down (an element, a connector, an aid, a dimension), the tracking that places it, its turning, and the modifications of a selection (move, turn, mirror, split, merge) -- a mixin of methods moved verbatim out of calc/tools/schema_canvas.py (issue #30). SchemaCanvas names it among its bases.
"""

import math
import theme  # the ground of a distance that cannot be read (theme.py, v0.90)
from domains import schema as model


# An aid line the pointer turns settles on multiples of this, as a static model's support does; the panel takes any angle, to a tenth.
ANGLE_STEP = 15.0


# The five kinds of fastener the tool bar offers, in the order the Connecteurs tab's own bar names them (connectors_tab.TOOL_TYPES). The German name is the connector's own, so a marker drawn here already says what it will be calculated as; the tab's own STRINGS give it its French and its English.
CONNECTOR_TOOLS = ("Nagel", "Stabdübel", "Vollgewindeschraube", "Bolzen", "Dübel besonderer Bauart")


# What each tool draws. `geo` says how a click is read; `kind` what is written down.
TOOLS = {
    "select": {},
    "pan": {},
    # «Cadrage» (v0.75): a rectangle dragged out, what the report shows -- plan_canvas's own crop tool.
    "crop": {"drag": "crop"},
    "linear": {"geo": "linear"},
    "area": {"geo": "area"},
    "aid-centre": {"geo": "aid-point", "kind": "centre"},
    "aid-point": {"geo": "aid-point", "kind": "point"},
    "aid-vertical": {"geo": "aid-fixed", "kind": "vertical", "angle": 90.0},
    "aid-horizontal": {"geo": "aid-fixed", "kind": "horizontal", "angle": 0.0},
    "aid-point-angle": {"geo": "aid-turn", "kind": "point-angle"},
    "aid-perpendicular": {"geo": "aid-reference", "kind": "perpendicular", "turn": 90.0},
    "aid-parallel": {"geo": "aid-reference", "kind": "parallel", "turn": 0.0},
    "aid-two-points": {"geo": "aid-two", "kind": "two-points"},
    "dimension-horizontal": {"geo": "dimension", "on": "free", "kind": "horizontal"},
    "dimension-vertical": {"geo": "dimension", "on": "free", "kind": "vertical"},
    "dimension-parallel": {"geo": "dimension", "on": "free", "kind": "parallel"},
    "dimension-angle": {"geo": "dimension", "on": "element", "kind": "angle"},
    # a text, put down where the click falls (issue #43): one click, like a connector, and written in the pane
    "text": {"geo": "text"},
    # The four verbs that take clicks. «Trancher» and «fusionner» are not here: they act on what is
    # already selected and are buttons, not tools -- there is nothing on the grid for them to point at.
    "move": {"geo": "modify", "verb": "move"},
    "duplicate": {"geo": "modify", "verb": "duplicate"},
    "rotate": {"geo": "modify", "verb": "rotate"},
    "mirror": {"geo": "modify", "verb": "mirror"},
}


for _kind in CONNECTOR_TOOLS:
    TOOLS[f"connector:{_kind}"] = {"geo": "connector", "kind": _kind}


def _round(value, digits=2):
    """A coordinate as it is saved: to a hundredth of a millimetre, far below what a click can place."""
    value = round(float(value), digits) + 0.0
    return int(value) if value.is_integer() else value


class SchemaCanvasPlaceMixin:
    """Methods of schema_canvas.SchemaCanvas, moved verbatim (issue #30): the class names this mixin among its bases."""

    def _add(self, collection, entry):
        self.source[collection].append(entry)
        self.selection = (collection, entry["id"])

    def add_linear(self, a, b):
        """A piece seen edge-on, between two clicks."""
        if math.dist(a, b) <= model.SAME_POINT:
            self.refused.emit("element")
            return
        self.begin_change()
        entry = {
            "id": model.next_id(self.source, "elements"),
            "kind": "linear",
            "points": [[_round(a[0]), _round(a[1])], [_round(b[0]), _round(b[1])]],
            "view": "h",
        }
        # the position last chosen: its section is the piece's until one is written over (v0.75)
        if self.element_position:
            entry["position"] = self.element_position
        self._add("elements", entry)
        self.end_change()
        self.selection_changed.emit()

    def view_centre(self):
        """The middle of what the canvas shows, in mm, rounded to the millimetre -- where «Ajouter» puts an entry down."""
        centre = self.mapToScene(self.viewport().rect().center())
        return (_round(centre.x(), 0), _round(centre.y(), 0))

    def add_default(self, collection, kind=None):
        """«Ajouter», under a list (v0.75): one entry of that collection, put down in the middle of the view, selected, in one step of «Annuler» -- a piece 100 mm long, a plate 100 × 100, a marker, a named point, or a horizontal dimension 100 mm long. Returns its id. What it is is then typed into its row, which is why it is put where the engineer is looking.

        `collection` is a list's own name: "linear", "area", "connectors", "points", "aids", "dims". A point is an aid of kind `point`, not ticked as a connector; «Ajouter» under the other aids puts a centre down (v0.77, the points having a list of their own). A marker takes the fastener tool in hand, else a Stabdübel -- the one kind this project calculates.
        """
        cx, cz = self.view_centre()
        half = 50
        if collection == "linear":
            self.add_linear((cx - half, cz), (cx + half, cz))
            return self.selection[1] if self.selection else None
        if collection == "area":
            self.add_area([(cx - half, cz - half), (cx + half, cz - half), (cx + half, cz + half), (cx - half, cz + half)])
            return self.selection[1] if self.selection else None
        self.begin_change()
        if collection == "connectors":
            tool_kind = TOOLS.get(self.tool, {}).get("kind")
            marker_kind = kind or (tool_kind if tool_kind in model.CONNECTOR_KINDS else "Stabdübel")
            entry = {"id": model.next_id(self.source, "connectors"), "kind": marker_kind, "x": cx, "z": cz}
            self._add("connectors", entry)
        elif collection == "points":
            entry = {"id": model.next_id(self.source, "aids"), "kind": "point", "x": cx, "z": cz, "shown": True, "connector": False}
            self._add("aids", entry)
        elif collection == "aids":
            entry = {"id": model.next_id(self.source, "aids"), "kind": kind or "centre", "x": cx, "z": cz, "shown": True}
            self._add("aids", entry)
        else:
            entry = {"id": model.next_id(self.source, "dimensions"), "kind": "horizontal",
                     "from": {"x": cx - half, "z": cz}, "to": {"x": cx + half, "z": cz}, "offset": -30}
            self._add("dimensions", entry)
        self.end_change()
        self.selection_changed.emit()
        return entry["id"]

    def set_crop(self, rect):
        """«Cadrage»: what the report shows, (x, z, w, h) in mm, or None for the whole detail -- one step of «Annuler». A rectangle with no area is refused and says so."""
        if rect is not None:
            x, z, w, h = rect
            if abs(w) < 1.0 or abs(h) < 1.0:
                self.refused.emit("crop-empty")
                return False
            x, w = (x + w, -w) if w < 0 else (x, w)
            z, h = (z + h, -h) if h < 0 else (z, h)
        if rect is None and "crop" not in self.source:
            return True
        self.begin_change()
        if rect is None:
            self.source.pop("crop", None)
        else:
            self.source["crop"] = {"x": _round(x), "z": _round(z), "w": _round(w), "h": _round(h)}
        self.end_change()
        return True

    def set_hover(self, key):
        """Lights one entry -- a (collection, id) pair, or None -- the way a row of the lists does while the pointer is over it (v0.75). Hovering selects nothing, which is why it has its own colour."""
        if key == self.hover:
            return
        self.hover = key
        self.update_helpers()

    def area_points(self, clicks, cursor=None):
        """The four corners the clicks so far would give, or None where there are not enough yet -- the tool bar's three modes, which schema.py reduces to two constructions. With a position that fixes a side (`area_fixed`, v0.117) the fixed side is the position's: dragged by corners the other side follows the cursor, drawn by an edge the third click only says on which side of it the rectangle lies."""
        points = list(clicks) + ([cursor] if cursor is not None else [])
        if self.area_mode == "diagonal":
            if len(points) < 2:
                return None
            if self.area_fixed is not None:
                return model.rectangle_with_fixed_side(points[0], points[1], self.area_fixed[1], self.area_fixed[0])
            return model.rectangle_two_corners(points[0], points[1])
        if len(points) < 3:
            return None
        if self.area_fixed is not None:
            return model.rectangle_with_fixed_width(points[0], points[1], points[2], self.area_fixed[1])
        width = model.perpendicular_offset(points[0], points[1], points[2])
        return model.rectangle_from_edge(points[0], points[1], width)

    def add_area(self, corners):
        if corners is None:
            self.refused.emit("element")
            return
        a, b = corners[0], corners[1]
        if math.dist(a, b) <= model.SAME_POINT or math.dist(corners[1], corners[2]) <= model.SAME_POINT:
            self.refused.emit("element")
            return
        self.begin_change()
        entry = {
            "id": model.next_id(self.source, "elements"),
            "kind": "area",
            "points": [[_round(p[0]), _round(p[1])] for p in corners],
        }
        # the position last chosen is the element's, as it is a piece seen edge-on's (v0.117): its section is the element's until one is written over
        if self.element_position:
            entry["position"] = self.element_position
        self._add("elements", entry)
        self.end_change()
        self.selection_changed.emit()

    def add_connector(self, p):
        kind = TOOLS[self.tool]["kind"]
        self.begin_change()
        self._add("connectors", {
            "id": model.next_id(self.source, "connectors"),
            "kind": kind,
            "x": _round(p[0]),
            "z": _round(p[1]),
        })
        self.end_change()
        self.selection_changed.emit()

    def add_text(self, p):
        """A text put down at `p` (issue #43): empty, selected, written in the pane -- one step of «Annuler»."""
        entry = {"id": model.next_id(self.source, "texts"), "x": _round(p[0]), "z": _round(p[1]), "text": ""}
        self.begin_change()
        self.source.setdefault("texts", []).append(entry)
        self.selection = ("texts", entry["id"])
        self.end_change()
        self.selection_changed.emit()
        self.tool_done.emit()

    def place_markers(self, points, kind=None, replace=True):
        """A whole group of connector markers at once -- what the schemas tab's «Grille…» puts down (v0.74).

        `replace` clears the markers there are first, which is what setting out a pattern usually means;
        without it the group is added to what is already drawn, for a second grid on the same detail. One
        step of «Annuler», whatever it placed, as every other modification is.

        ⚠️ Markers a calculation has TICKED are named by id (`connectors/<id>.json`, `connections/<id>.json`),
        so replacing them renumbers what those calculations point at. That is the same exposure as deleting
        a marker by hand, and it is reported the same way -- by the export, as a warning naming the ids.
        """
        # the fastener tool in force, else a Stabdübel -- never the kind of an aid or a dimension tool, and no KeyError for a tool without one, «Sélection» first of all (periodic audit 260916)
        if kind not in model.CONNECTOR_KINDS:
            tool_kind = TOOLS.get(self.tool, {}).get("kind")
            kind = tool_kind if tool_kind in model.CONNECTOR_KINDS else "Stabdübel"
        self.begin_change()
        if replace:
            for marker in list(self.source.get("connectors", [])):
                model.remove(self.source, "connectors", marker["id"])
            self.selection = None
        for x, z in points:
            self._add("connectors", {
                "id": model.next_id(self.source, "connectors"),
                "kind": kind,
                "x": _round(x),
                "z": _round(z),
            })
        self.end_change()
        self.selection_changed.emit()

    def add_aid_point(self, p):
        self.begin_change()
        self._add("aids", {
            "id": model.next_id(self.source, "aids"),
            "kind": TOOLS[self.tool]["kind"],
            "x": _round(p[0]),
            "z": _round(p[1]),
            "shown": True,
        })
        self.end_change()
        self.selection_changed.emit()

    def add_aid_line(self, p, angle, kind=None):
        """A construction line through one point, at a plain angle -- `shown` false, which is what keeps an aid out of the report unless it is asked for."""
        self.begin_change()
        self._add("aids", {
            "id": model.next_id(self.source, "aids"),
            "kind": kind or TOOLS[self.tool]["kind"],
            "x": _round(p[0]),
            "z": _round(p[1]),
            "angle": _round(model.normalize_angle(angle), 1),
            "shown": False,
        })
        self.end_change()
        self.selection_changed.emit()

    def add_aid_two_points(self, a, b):
        if math.dist(a, b) <= model.SAME_POINT:
            self.refused.emit("element")
            return
        self.begin_change()
        self._add("aids", {
            "id": model.next_id(self.source, "aids"),
            "kind": "two-points",
            "x1": _round(a[0]), "z1": _round(a[1]),
            "x2": _round(b[0]), "z2": _round(b[1]),
            "shown": False,
        })
        self.end_change()
        self.selection_changed.emit()

    def add_aid_from_reference(self, p, reference_click):
        """A perpendicular or a parallel: the second click names the line it is measured from by lying near it, there being nothing at a click to name one by. Where nothing is near enough, it says so rather than drawing at a guessed angle."""
        u = model.reference_direction(self.source, reference_click)
        if u is None:
            self.refused.emit("reference")
            return
        angle = math.degrees(math.atan2(u[1], u[0])) + TOOLS[self.tool]["turn"]
        self.add_aid_line(p, angle)

    def dimension_anchor(self, p):
        """One end of a dimension: the aid point under it, which the dimension then follows as that aid is moved, or a place of its own (statics_canvas's own rule, section 3.3octies)."""
        aid = model.hit_aid_point(self.source, p, self.tolerance())
        return {"point": aid} if aid is not None else {"x": _round(p[0]), "z": _round(p[1])}

    def linear_entry(self, a, b, c=None):
        """The length dimension the clicks so far would make, or None where there is nothing to measure."""
        entry = {
            "id": model.next_id(self.source, "dimensions"),
            "kind": TOOLS[self.tool]["kind"],
            "from": self.dimension_anchor(a),
            "to": self.dimension_anchor(b),
            "offset": 0.0,
        }
        ends = model.dimension_ends(self.source, entry)
        frame = model.dimension_direction(self.source, entry)
        if ends is None or frame is None or math.dist(ends[0], ends[1]) <= model.SAME_POINT:
            return None
        if c is not None:
            _u, n = frame
            middle = ((ends[0][0] + ends[1][0]) / 2.0, (ends[0][1] + ends[1][1]) / 2.0)
            entry["offset"] = _round((c[0] - middle[0]) * n[0] + (c[1] - middle[1]) * n[1])
        return entry

    def add_dimension(self, a, b, c):
        entry = self.linear_entry(a, b, c)
        if entry is None:
            self.refused.emit("dimension-ends")
            return
        self.begin_change()
        self._add("dimensions", entry)
        self.end_change()
        self.selection_changed.emit()

    def angle_entry(self, p):
        """The angle dimension a third click at `p` would make: the click gives the arc its radius and, as a `bearing` from the corner, which of the four sectors is meant (schema.angle_rays, statics.py's own rule)."""
        entry = {
            "id": model.next_id(self.source, "dimensions"),
            "kind": "angle",
            "from": {"element": self.dim_elements[0]},
            "to": {"element": self.dim_elements[1]},
            "offset": 0.0,
        }
        corner = model.dimension_corner(self.source, entry)
        if corner is None:
            return None
        centre = corner[0]
        reach = (p[0] - centre[0], p[1] - centre[1])
        radius = math.hypot(reach[0], reach[1])
        if radius <= model.SAME_POINT:
            return None
        entry["offset"] = _round(radius)
        entry["bearing"] = _round(math.degrees(math.atan2(reach[1], reach[0])), 1)
        return entry

    def add_angle_dimension(self, p):
        entry = self.angle_entry(p)
        if entry is None:
            self.refused.emit("dimension-parallel")
            return
        self.dim_elements = []
        self.dim_hover = None
        self.begin_change()
        self._add("dimensions", entry)
        self.end_change()
        self.selection_changed.emit()

    def turn(self, raw):
        """An aid line just put down, turned to face where the pointer is -- in steps of ANGLE_STEP, the way a static model's support is turned."""
        entry = model.entry_of(self.source, "aids", self.turning["id"])
        at = self.turning["at"]
        if entry is None or at is None:
            return
        dx, dz = raw[0] - at[0], raw[1] - at[1]
        if math.hypot(dx, dz) < 1e-9:
            return
        angle = math.degrees(math.atan2(dz, dx))
        entry["angle"] = _round(model.normalize_angle(round(angle / ANGLE_STEP) * ANGLE_STEP), 1)
        self._drawing_cache = None
        self.redraw_timer.start()

    def finish_turning(self):
        if self.turning is not None:
            self.turning = None
            self.end_change()
            self.selection_changed.emit()

    def anchor(self):
        return self.drawing[-1] if self.drawing else self.acquired

    def acquire(self):
        if self._hover is None or self.drawing:
            return
        self.acquired = self._hover
        self.rays = model.tracking_rays(self.source, self.acquired)
        self.update_helpers()

    def track(self, raw, shift=False):
        anchor = self.anchor()
        if anchor is not None and shift:
            return {"point": model.constrain(anchor, raw), "ray": None, "kind": "shift",
                    "distance": math.dist(anchor, raw), "angle": None}
        if anchor is None:
            p, kind = model.snap(self.source, raw, self.tolerance(), self.snap_step(), geometry=self.snap_geometry())
            return {"point": p, "ray": None, "kind": kind, "distance": None, "angle": None}
        return model.track(self.source, anchor, raw, self.tolerance(), self.snap_step(), geometry=self.snap_geometry())

    def rotation_waiting(self):
        """True while «Tourner» has its centre and waits for the direction -- which Tab may give as an angle instead (v0.75)."""
        return TOOLS.get(self.tool, {}).get("verb") == "rotate" and len(self.drawing) == 1

    def show_distance(self):
        if self.rotation_waiting():
            # «Tourner», 1 clic + un angle tapé: the field takes degrees, counted from +x towards +z as every angle here is
            self.typing = True
            self.typing_angle = True
            centre = self.drawing[0]
            p = self.mapFromScene(self.qp(self.cursor or centre))
            self.distance.move(min(max(p.x() + 14, 0), max(self.viewport().width() - 130, 0)), max(p.y() - 12, 0))
            self.distance.setText(model.fmt_number(self.modify_angle(centre, self.cursor or centre), 1))
            self.distance.selectAll()
            self.distance.show()
            self.distance.setFocus()
            return
        if self.ray is None or self.anchor() is None:
            return
        self.typing = True
        self.typing_angle = False
        p = self.mapFromScene(self.qp(self.cursor or self.anchor()))
        self.distance.move(min(max(p.x() + 14, 0), max(self.viewport().width() - 130, 0)), max(p.y() - 12, 0))
        self.distance.setText(model.fmt_number(math.dist(self.anchor(), self.cursor or self.anchor())))
        self.distance.selectAll()
        self.distance.show()
        self.distance.setFocus()

    def hide_distance(self):
        self.typing = False
        self.typing_angle = False
        self.distance.hide()
        self.distance.setStyleSheet("")
        self.setFocus()

    @staticmethod
    def typed_angle(text):
        """Degrees off the angle field, or None where the text is not a finite number (a comma is a decimal point)."""
        try:
            value = float(str(text).strip().replace(",", "."))
        except ValueError:
            return None
        return value if math.isfinite(value) else None

    def on_typed(self, text):
        if self.typing_angle:
            angle = self.typed_angle(text)
            self.distance.setStyleSheet("" if angle is not None or not text.strip() else f"background:{theme.colour('danger-soft')};")
            if angle is not None and self.drawing:
                centre = self.drawing[0]
                reach = max(math.dist(centre, self.cursor) if self.cursor else 0.0, 60.0 / self.scale_px())
                a = math.radians(angle)
                self.cursor = (centre[0] + reach * math.cos(a), centre[1] + reach * math.sin(a))
                self.update_helpers()
            return
        p = model.typed_point(self.anchor(), self.ray, text) if self.ray else None
        self.distance.setStyleSheet("" if p is not None or not text.strip() else f"background:{theme.colour('danger-soft')};")
        if p is not None:
            self.cursor = p
            self.update_helpers()

    def commit_typed(self):
        if self.typing_angle:
            angle = self.typed_angle(self.distance.text())
            if angle is None or not self.drawing:
                return
            centre = self.drawing[0]
            self.hide_distance()
            self.drawing = []
            self.cursor = None
            self.apply_modify("rotate", centre, centre, angle=angle)
            self.update_helpers()
            return
        p = model.typed_point(self.anchor(), self.ray, self.distance.text()) if self.ray else None
        if p is None:
            return
        self.hide_distance()
        self.place(p)

    def place(self, p):
        """Puts a point down where the tool is drawing."""
        geo = TOOLS[self.tool].get("geo")
        if geo == "connector":
            self.add_connector(p)
        elif geo == "text":
            self.add_text(p)
        elif geo == "aid-point":
            self.add_aid_point(p)
        elif geo == "aid-fixed":
            self.add_aid_line(p, TOOLS[self.tool]["angle"])
        elif geo == "aid-turn":
            self.add_aid_line(p, 0.0)
            # the pointer now turns it, in steps of ANGLE_STEP, until the next click sets it
            self.turning = {"id": self.selection[1], "at": p}
            self.begin_change()
        elif geo == "aid-reference":
            self.drawing.append(p)
            if len(self.drawing) == 2:
                a, b = self.drawing
                self.drawing = []
                self.cursor = None
                self.add_aid_from_reference(a, b)
        elif geo == "aid-two":
            self.drawing.append(p)
            if len(self.drawing) == 2:
                a, b = self.drawing
                self.drawing = []
                self.cursor = None
                self.add_aid_two_points(a, b)
        elif geo == "linear":
            self.drawing.append(p)
            if len(self.drawing) == 2:
                a, b = self.drawing
                self.drawing = []
                self.cursor = None
                self.add_linear(a, b)
                # AutoCAD's chain: the end just put down is where the next one starts from
                self.acquired = b
                self.rays = model.tracking_rays(self.source, b)
        elif geo == "area":
            self.drawing.append(p)
            wanted = 2 if self.area_mode == "diagonal" else 3
            if len(self.drawing) == wanted:
                corners = self.area_points(self.drawing)
                self.drawing = []
                self.cursor = None
                self.add_area(corners)
        elif geo == "modify":
            self.drawing.append(p)
            if len(self.drawing) == 2:
                a, b = self.drawing
                self.drawing = []
                self.cursor = None
                self.apply_modify(TOOLS[self.tool]["verb"], a, b)
        elif geo == "dimension":
            if TOOLS[self.tool]["kind"] == "angle":
                if len(self.dim_elements) == 2:
                    self.cursor = None
                    self.add_angle_dimension(p)
            else:
                self.drawing.append(p)
                if len(self.drawing) == 3:
                    a, b, c = self.drawing
                    self.drawing = []
                    self.cursor = None
                    self.add_dimension(a, b, c)
        self.update_helpers()

    def refusal_text(self, refusal, fallback):
        """A model refusal as the reason the tab shows: its own code, and what it names after a bar -- «merge-positions|T001, S001». The tab looks the code up in its three languages and puts the detail in the hole; a code it has no words for falls through as the English sentence, which says more than nothing."""
        if refusal is None:
            return fallback
        return f"{refusal.code}|{refusal.detail}" if refusal.detail else refusal.code

    def modify_angle(self, a, b):
        """The rotation a second click asks for: the bearing of `b` from `a`, counted from +x towards +z like every other angle here.

        ⚠️ There is deliberately no angle step of its own. **Shift already constrains the second click** to 0/45/90 degrees from the first, which is `track()`'s own doing for every tool on this canvas -- so Shift gives a quarter and an eighth turn without this knowing anything about it, and the tracking rays give a member's own axis besides.
        """
        dx, dz = b[0] - a[0], b[1] - a[1]
        if math.hypot(dx, dz) < 1e-9:
            return 0.0
        return model.normalize_angle(math.degrees(math.atan2(dz, dx)))

    def transform_for(self, verb, a, b, angle=None):
        """The (place, bearing, flips) triple a verb and its two clicks name, or None where they name none. `angle` is a rotation typed rather than clicked (v0.75), which then wins over `b`."""
        if verb in ("move", "duplicate"):
            return model.translation(b[0] - a[0], b[1] - a[1])
        if verb == "rotate":
            return model.rotation(a, self.modify_angle(a, b) if angle is None else float(angle))
        if verb == "mirror":
            try:
                return model.reflection(a, b)
            except ValueError:
                return None
        return None

    def apply_modify(self, verb, a, b, angle=None):
        """One modification, on everything selected, in one step of «Annuler». `angle` is a rotation typed after the centre (Tab), in degrees.

        ⚠️ It acts on **the selection**, never on what is under the pointer: the two clicks say how far and about what, not what to move. A tool chosen with nothing selected therefore refuses and says so, rather than silently doing nothing.
        """
        chosen = [eid for _collection, eid in self.selection_ids()]
        if not chosen:
            self.refused.emit("modify-nothing")
            return
        transform = self.transform_for(verb, a, b, angle)
        if transform is None:
            self.refused.emit("modify-axis")
            return
        self.begin_change()
        if verb == "duplicate":
            made = model.duplicate(self.source, chosen, transform)
            if made:
                # The copies become the selection, so a second duplicate copies the copy -- which is
                # what an engineer laying out a row of identical pieces is doing.
                pairs = [model.find_entry(self.source, eid)[0] for eid in made]
                self.selection = (pairs[0], made[0])
                self.extra = [(c, i) for c, i in zip(pairs[1:], made[1:])]
        else:
            model.modify(self.source, chosen, transform)
        self.end_change()
        self.selection_changed.emit()

    def split_selection(self):
        """«Trancher»: every element selected, cut on the one construction line selected with them.

        The line is chosen the way everything else here is chosen -- by selecting it (Ctrl) -- rather than by a second click, so that the same gesture serves one element and six.
        """
        lines, elements = [], []
        for collection, entry in self.selected_entries():
            if collection == "aids" and model.aid_line(entry) is not None:
                lines.append(entry["id"])
            elif collection == "elements":
                elements.append(entry["id"])
        if not elements:
            self.refused.emit("split-no-element")
            return
        if len(lines) != 1:
            self.refused.emit("split-no-line" if not lines else "split-many-lines")
            return
        # ⚠️ Tried on a copy first. `begin_change()` is what pushes a step of «Annuler», so a
        # refusal after it would leave the engineer an undo that undoes nothing -- and a cut that
        # misses is the common case here, not the rare one.
        probe = model.snapshot(self.source)
        cuts, refusal = 0, None
        for eid in elements:
            try:
                model.split_element(probe, eid, lines[0])
                cuts += 1
            except model.Refused as exc:
                refusal = exc
        if not cuts:
            self.refused.emit(self.refusal_text(refusal, "split-missed"))
            return
        self.begin_change()
        made = []
        for eid in elements:
            try:
                made += model.split_element(self.source, eid, lines[0])
            except model.Refused:
                pass
        pairs = [("elements", eid) for eid in made]
        self.selection, self.extra = pairs[0], pairs[1:]
        self.end_change()
        self.selection_changed.emit()
        if refusal is not None:
            self.refused.emit(self.refusal_text(refusal, "split-missed"))

    def merge_selection(self):
        """«Fusionner»: the elements selected, joined into one -- only where they carry the same position number, which is the rule the engineer set."""
        elements = [entry["id"] for collection, entry in self.selected_entries() if collection == "elements"]
        if len(elements) < 2:
            self.refused.emit("merge-too-few")
            return
        try:
            model.merge_elements(model.snapshot(self.source), elements)
        except model.Refused as exc:
            self.refused.emit(self.refusal_text(exc, "merge-apart"))
            return
        self.begin_change()
        kept = model.merge_elements(self.source, elements)
        self.selection, self.extra = ("elements", kept), []
        self.end_change()
        self.selection_changed.emit()
