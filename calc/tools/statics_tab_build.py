"""StaticsTab's building -- the list, the four tables and their columns, the tool bar and its buttons, the canvas, the right pane -- a mixin of methods moved verbatim out of calc/tools/statics_tab.py (issue #30). StaticsTab names it among its bases.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QButtonGroup, QCheckBox, QComboBox, QDoubleSpinBox, QGridLayout,
    QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPlainTextEdit,
    QPushButton, QRadioButton, QSlider, QSplitter, QTabWidget, QTableWidget,
    QTableWidgetItem, QToolButton, QVBoxLayout, QWidget,
)
import grouped_list
import source_archive  # «Supprimer» archives (source_archive.py)
import identity
import project  # where the project this tab works on is (calc/project.py)
import theme  # the colours this tab states itself (theme.py, v0.90)
import richtext  # the calls coloured as the site's code, «Copié ✓» (richtext.py, v0.92)
import cards  # the properties in cards, after the website (cards.py, v0.95)
import text_pane  # the Text tool's pane and symbol, the four engines' one (issue #43)
from domains import statics as model
from domains import statics_svg
import flowbar
from flowbar import (BAR_SPACING, TOOL_ICON_PX, FlowLayout, FlowWidget, ResizableColumns, ToolBarArea,
                     set_tip, size_tool, symbol_px, tool_group)
from statics_tab_words import HINTS, STRINGS, TIPS, hint_key, tip_key  # split out of this module (issue #30): every name it had is still importable from it
from statics_canvas import TOOLS, StaticsCanvas
import svg_icons


# The four words the engineer uses for an articulation, the (dof, spring) each stands for, and the tool that draws it. A translational spring is not here: it is a member of kind 'spring'.
RELEASES = (
    ("st_dof_moment", "moment", False, "release-moment"),
    ("st_dof_shear", "shear", False, "release-shear"),
    ("st_dof_normal", "normal", False, "release-normal"),
    ("st_dof_spring_moment", "moment", True, "release-spring-moment"),
)


# The grid steps the engineer may force, beside «auto».
GRID_CHOICES = ("auto", 5.0, 1.0, 0.5, 0.1)


# The tool bar, in the groups the engineer asked for: a run of buttons per kind of thing, parted by a thin line, every tool its symbol alone (v0.94) -- its name and how it is used being its tooltip. The navigation and the history open the bar, as they open the position plan's and the schemas'.
TOOL_GROUPS = (
    ("st_group_elements", (("point", "st_tool_point"), ("bar", "st_tool_bar"),
                           ("cable", "st_tool_cable"), ("spring", "st_tool_spring"))),
    ("st_group_supports", (("support-fixed", "st_tool_support_fixed"),
                           ("support-pinned", "st_tool_support_pinned"),
                           ("support-roller", "st_tool_support_roller"))),
    ("st_group_releases", (("release-moment", "st_tool_release_moment"),
                           ("release-normal", "st_tool_release_normal"),
                           ("release-shear", "st_tool_release_shear"),
                           ("release-spring-moment", "st_tool_release_spring_moment"))),
    ("st_group_loads", (("point-load", "st_tool_point_load"),
                        ("line-load", "st_tool_line_load"),
                        ("line-load-linear", "st_tool_line_load_linear"))),
    ("st_group_dimensions", (("dimension-horizontal", "st_tool_dim_horizontal"),
                             ("dimension-vertical", "st_tool_dim_vertical"),
                             ("dimension-parallel", "st_tool_dim_parallel"),
                             ("dimension-angle", "st_tool_dim_angle"))),
    ("st_group_texts", (("text", "st_tool_text"),)),
)


# How big a tool's icon is drawn where no button gives it a size: the bar's own measure (flowbar.TOOL_ICON_PX). A tool of the bar is drawn at flowbar.symbol_px(), so the pixmap is drawn at the size it is shown and not scaled down blurred, and every button of the bar is flowbar.tool_height() tall -- a tool of the position plan's bar, measured (v0.94).
ICON_PX = TOOL_ICON_PX


def plain_label(text, wrap=False):
    """A label showing `text` exactly as it is -- given a text that looks like HTML, QLabel would render it as HTML."""
    label = QLabel(text)
    label.setTextFormat(Qt.TextFormat.PlainText)
    label.setWordWrap(wrap)
    return label


# What the figure draws its lines and its fills in. Only these two are recoloured for the button: a cable's blue and a load's red say which symbol it is, and read on either ground.
SWATCH_INK = statics_svg.BAR   # the figure's own ink, read where it is written (issue #29)


SWATCH_FILL = "#ffffff"   # colour-ok: the white the figure fills with, recognised to be recoloured


def _member_icon(body):
    """A member's button symbol: `body`, drawn along x from 1.5 to 22.5, turned onto the square's diagonal between the two nodes it joins."""
    nodes = "".join(f'<circle cx="{x}" cy="12" r="2.2" fill="{SWATCH_INK}"/>' for x in (1.5, 22.5))
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">'
            f'<g transform="rotate(-45 12 12)">{body}{nodes}</g></svg>')


# A member's own symbol is a line across the whole figure, a hundredth of its length thick: in a button 20 px wide it is a hair, and it carried its name under it until v0.94. Its button draws it here instead, on the diagonal and at a button's scale, in the figure's own colours -- a bar heavy and in ink, a cable fine and blue, a spring a blue zigzag -- so the three read apart with no name.
MEMBER_ICONS = {
    "bar": _member_icon(f'<path d="M1.5 12 H22.5" fill="none" stroke="{SWATCH_INK}" stroke-width="3"/>'),
    "cable": _member_icon(f'<path d="M1.5 12 H22.5" fill="none" stroke="{statics_svg.CABLE}" stroke-width="1.4"/>'),
    "spring": _member_icon(f'<polyline points="1.5,12 6,12 7.5,8.8 10.5,15.2 13.5,8.8 16.5,15.2 18,12 22.5,12" fill="none" '
                           f'stroke="{statics_svg.SPRING}" stroke-width="1.4" stroke-linejoin="round"/>'),
    # the Text tool's (issue #43): text_pane's T, the same in the four engines
    "text": text_pane.icon_svg(SWATCH_INK),
}


def svg_icon(tool, size=ICON_PX, ink=None, ground=None):
    """A tool's button icon: the very symbol the figure draws, **in its own proportions** -- a swatch stretched into a square is a symbol one cannot read -- or, for a member, its symbol at a button's scale (MEMBER_ICONS). On a dark theme the ink and the fills are taken from the palette, the figure's black being invisible there."""
    try:
        svg = MEMBER_ICONS.get(tool) or statics_svg.swatch(tool)
    except KeyError:
        return QIcon()
    return svg_icons.svg_icon(svg_icons.recolour(svg, SWATCH_INK, SWATCH_FILL, ink, ground), size, fit=True)


def _as_number(text):
    """A cell's text as a number -- a comma read as a decimal point, the keyboard here having one -- or None."""
    try:
        return float(str(text).strip().replace(",", "."))
    except (TypeError, ValueError):
        return None


def _set_number(entry, field, text):
    value = _as_number(text)
    if value is None:
        return False
    entry[field] = value
    return True


def _set_angle(entry, text):
    if entry.get("direction") not in ("angle", "member"):
        return not str(text).strip()  # an angle belongs to those two directions only
    return _set_number(entry, "angle", text)


def _set_unit(entry, key, text):
    unit = str(text).strip()
    if not unit:
        return False
    magnitude = entry.get(key) or {}
    if model.magnitude_kind(magnitude) == "reference":
        return False
    magnitude["unit"] = unit
    entry[key] = magnitude
    if "magnitude_end" in entry and model.magnitude_kind(entry["magnitude_end"]) == "literal":
        entry["magnitude_end"]["unit"] = unit
    return True


def _set_along(entry, text):
    """How far along its reference member a point load is drawn: a length in metres, or a fraction such as 0.5l. Empty puts it back on its point."""
    text = str(text).strip()
    if not text:
        entry.pop("along", None)
        return True
    if model.parse_along(text) is None:
        return False
    entry["along"] = text
    return True


def _width_text(entry):
    width = entry.get("width")
    return "" if not width else model.fmt_number(width["value"])


def _set_width(entry, text):
    text = str(text).strip()
    if not text:
        entry.pop("width", None)
        return True
    value = _as_number(text)
    if value is None or value <= 0:
        return False
    width = entry.setdefault("width", {"unit": model.WIDTH_UNIT, "label": model.DEFAULT_WIDTH_LABEL,
                                       "description": "", "show": True})
    width["value"] = value
    width.setdefault("unit", model.WIDTH_UNIT)
    return True


def _stiffness_text(entry):
    stiffness = entry.get("stiffness")
    return "" if not stiffness else model.fmt_number(stiffness["value"])


def _set_stiffness(entry, text):
    text = str(text).strip()
    if not text:
        entry.pop("stiffness", None)
        return entry.get("kind") != "spring" or True
    if entry.get("kind") != "spring":
        return False
    value = _as_number(text)
    if value is None or value <= 0:
        return False
    entry["stiffness"] = {"value": value, "unit": model.MEMBER_STIFFNESS_UNIT}
    return True


def _fix_direction(entry):
    """An angle belongs to 'angle' and 'member' only, and a reference member to a point load in 'member' mode -- a direction changed in a list takes its companions with it."""
    direction = entry.get("direction")
    if direction not in ("angle", "member"):
        entry.pop("angle", None)
    else:
        # a right angle: a load given at an angle is nearly always across its member or straight down, never along it
        entry.setdefault("angle", 90.0)
    if direction != "member" or "member" in entry:
        entry.pop("reference", None)


def _fix_shape(entry):
    """A linear load needs its value at the far end, a uniform one must not carry it."""
    if entry.get("shape") == "linear":
        entry.setdefault("magnitude_end", {"value": 0.0, "unit": (entry.get("magnitude") or {}).get("unit", "kN/m")})
    else:
        entry.pop("magnitude_end", None)


def _fix_kind(entry):
    """Only a spring carries a stiffness of its own."""
    if entry.get("kind") != "spring":
        entry.pop("stiffness", None)
    else:
        entry.setdefault("stiffness", {"value": 1000.0, "unit": model.MEMBER_STIFFNESS_UNIT})


class StaticsBuildMixin:
    """Methods of statics_tab.StaticsTab, moved verbatim (issue #30): the class names this mixin among its bases."""

    def heading(self, text):
        label = plain_label(text)
        label.setFont(self.app.bold_font)
        return label

    def note(self, text):
        """An explanation, muted and wrapping, as a card's note is (cards.note)."""
        return cards.note(text)

    def build_tables(self):
        """The four lists, under the drawing where they are as wide as it is."""
        self.tables = QTabWidget()
        self.table_specs = self.build_table_specs()
        self.table_widgets = {}
        self.table_columns = {}
        for collection, spec in self.table_specs.items():
            page = QWidget()
            inner = QVBoxLayout(page)
            inner.setContentsMargins(2, 4, 2, 2)
            table = QTableWidget(0, len(spec["columns"]))
            table.setHorizontalHeaderLabels([self.t(c["title"]) for c in spec["columns"]])
            table.verticalHeader().setVisible(False)
            # the columns are the engineer's to widen by dragging the header's dividers, each starting at the width of what it holds (flowbar.ResizableColumns) -- sized by the header itself until then, which no divider can be dragged in
            self.table_columns[collection] = ResizableColumns(table)
            table.itemChanged.connect(lambda _item, c=collection: self.read_table(c))
            table.itemSelectionChanged.connect(lambda c=collection: self.on_table_selection(c))
            inner.addWidget(table, 1)
            buttons = QHBoxLayout()
            add = QPushButton(self.t("st_add"))
            add.clicked.connect(lambda _c=False, c=collection: self.add_row(c))
            remove = QPushButton(self.t("st_remove"))
            remove.clicked.connect(lambda _c=False, c=collection: self.remove_row(c))
            buttons.addWidget(add)
            buttons.addWidget(remove)
            buttons.addStretch(1)
            inner.addLayout(buttons)
            table.setMinimumHeight(2 * self.fontMetrics().height())
            self.table_widgets[collection] = table
            self.tables.addTab(page, self.t(spec["title"]))
        # A table's own minimum is its header and several rows, which would have stopped the splitter long before the engineer had given the drawing anything (v0.66). Its floor here is the tabs, a header, one row and the two buttons -- short enough to be worth dragging to, and still a list.
        self.tables.setMinimumHeight(5 * self.fontMetrics().height() + 52)
        return self.tables

    def support_of(self, point):
        return next((s for s in self.source["supports"] if s["point"] == point["id"]), None)

    def build_table_specs(self):
        """What each of the four lists shows, and how a cell round-trips into the source. A column is `text`, `number`, `id`, or a `choice` of fixed values or of the model's own ids."""
        def mag(entry, key):
            m = entry.get(key) or {}
            return "" if "value" not in m else model.fmt_number(m["value"])

        def set_mag(entry, key, text):
            m = entry.get(key) or {}
            if model.magnitude_kind(m) == "reference":
                return False  # a referenced magnitude is set in the panel, not here
            if not str(text).strip():
                # a value is optional: a cleared cell leaves the load with none, which is drawn at full length and shows only its name
                entry.pop(key, None)
                return True
            value = _as_number(text)
            if value is None:
                return False
            entry[key] = {"value": value, "unit": (m or {}).get("unit") or ("kN" if "point" in entry else "kN/m")}
            return True

        def anchor_text(entry, key):
            """One end of a dimension, as the list writes it: the id it follows, or the place of its own it was put at."""
            a = entry.get(key) or {}
            if a.get("member"):
                return a["member"]
            if a.get("point"):
                return a["point"]
            if "x" in a and "z" in a:
                return f"{model.fmt_number(a['x'])} / {model.fmt_number(a['z'])}"
            return ""

        def set_anchor(entry, key, text):
            """An id, which the dimension then follows as that thing is moved, or a place of its own written `x / z`."""
            text = str(text).strip()
            if not text:
                return False
            if entry.get("kind") == "angle":
                if any(m["id"] == text for m in self.source.get("members", [])):
                    entry[key] = {"member": text}
                    return True
                return False
            if any(q["id"] == text for q in self.source.get("points", [])):
                entry[key] = {"point": text}
                return True
            parts = [part for part in text.replace(";", "/").split("/") if part.strip()]
            if len(parts) == 2:
                x, z = _as_number(parts[0]), _as_number(parts[1])
                if x is not None and z is not None:
                    entry[key] = {"x": round(x, 3), "z": round(z, 3)}
                    return True
            return False

        colour_column = {"title": "st_col_colour", "kind": "choice", "values": tuple(model.LOAD_COLOURS),
                         "labels": tuple(f"st_colour_{name}" for name in model.LOAD_COLOURS),
                         "get_value": model.load_colour, "set_value": self.set_load_colour}

        def set_dim_kind(entry, value):
            # the cell is closed on an angle, so this only ever moves between the three linear kinds, whose ends are points
            if value in model.DIMENSION_LINEAR and entry.get("kind") in model.DIMENSION_LINEAR:
                entry["kind"] = value

        def support_type(point):
            support = self.support_of(point)
            return support["type"] if support else ""

        def release_here(point):
            """The articulation at this node, as the tool that draws it -- empty for none, and '?' where several member ends meet here and the answer is not one thing."""
            ends = model.releases_at(self.source, point["id"])
            if len(ends) != 1:
                return "?" if ends else ""
            release = ends[0][2]
            if release is None:
                return ""
            spring = release.get("stiffness") is not None
            return next((tool for _k, dof, sp, tool in RELEASES if dof == release["dof"] and sp == spring), "")

        def release_live(point):
            ends = model.releases_at(self.source, point["id"])
            return True if len(ends) == 1 else ("st_release_here" if ends else False)

        def set_release_here(point, tool):
            ends = model.releases_at(self.source, point["id"])
            if len(ends) != 1:
                return
            member_id, end, _release = ends[0]
            choice = next(((dof, sp) for _k, dof, sp, t in RELEASES if t == tool), None)
            self.apply_release(member_id, end, choice)

        def support_angle_text(point):
            support = self.support_of(point)
            return "" if support is None else model.fmt_number(float(support.get("angle", 0.0)))

        def set_support_angle(point, text):
            support = self.support_of(point)
            if support is None:
                return not str(text).strip()
            value = _as_number(text)
            if value is None:
                return False
            support["angle"] = round(value, 1)
            return True

        # Where a Festlager's or a Loslager's pin is drawn, which the model cannot tell by itself: on the node, the bar turning about it, or set back under a bar that runs over the support. An Einspannung has no pin, so its cell is closed.
        def hinge_live(point):
            support = self.support_of(point)
            return support is not None and support["type"] in model.HINGED_SUPPORTS

        def support_hinge(point):
            if not hinge_live(point):
                return ""
            return self.support_of(point).get("hinge", model.SUPPORT_HINGES[0])

        def set_support_hinge(point, value):
            if hinge_live(point) and value:
                self.support_of(point)["hinge"] = value

        return {
            "points": {
                "title": "st_tab_points",
                "columns": [
                    {"title": "st_col_id", "kind": "id"},
                    {"title": "st_col_x", "kind": "number", "get": lambda e: model.fmt_number(e["x"]),
                     "set": lambda e, v: _set_number(e, "x", v)},
                    {"title": "st_col_z", "kind": "number", "get": lambda e: model.fmt_number(e["z"]),
                     "set": lambda e, v: _set_number(e, "z", v)},
                    {"title": "st_col_release", "kind": "choice",
                     "values": ("",) + tuple(tool for _k, _d, _s, tool in RELEASES),
                     "labels": ("st_release_none",) + tuple(k for k, _d, _s, _t in RELEASES),
                     "get_value": release_here, "set_value": set_release_here, "enabled": release_live},
                    {"title": "st_col_support", "kind": "choice", "values": ("",) + model.SUPPORT_TYPES,
                     "labels": ("st_support_none", "st_tool_support_fixed", "st_tool_support_pinned",
                                "st_tool_support_roller"),
                     "get_value": support_type, "set_value": self.set_support},
                    {"title": "st_col_support_hinge", "kind": "choice",
                     "values": ("",) + model.SUPPORT_HINGES,
                     "labels": ("st_support_none", "st_support_hinge_shared", "st_support_hinge_through"),
                     "get_value": support_hinge, "set_value": set_support_hinge, "enabled": hinge_live},
                    {"title": "st_col_support_angle", "kind": "number", "get": support_angle_text,
                     "set": set_support_angle},
                    {"title": "st_col_name", "kind": "text", "get": lambda e: e.get("label", ""),
                     "set": lambda e, v: e.update(label=v) or True},
                ],
            },
            "members": {
                "title": "st_tab_members",
                "columns": [
                    {"title": "st_col_id", "kind": "id"},
                    {"title": "st_col_kind", "kind": "choice", "values": model.MEMBER_KINDS,
                     "labels": ("st_kind_bar", "st_kind_cable", "st_kind_spring"), "field": "kind",
                     "after": _fix_kind},
                    {"title": "st_col_p1", "kind": "ref", "of": "points", "field": "p1"},
                    {"title": "st_col_p2", "kind": "ref", "of": "points", "field": "p2"},
                    {"title": "st_col_stiffness", "kind": "number", "get": _stiffness_text, "set": _set_stiffness},
                    {"title": "st_col_name", "kind": "text", "get": lambda e: e.get("label", ""),
                     "set": lambda e, v: e.update(label=v) or True},
                ],
            },
            "point_loads": {
                "title": "st_tab_point_loads",
                "columns": [
                    {"title": "st_col_id", "kind": "id"},
                    {"title": "st_col_point", "kind": "ref", "of": "points", "field": "point"},
                    {"title": "st_col_reference", "kind": "ref", "of": "members", "field": "reference"},
                    {"title": "st_col_along", "kind": "text",
                     "get": lambda e: "" if e.get("along") in (None, "") else str(e["along"]),
                     "set": _set_along},
                    {"title": "st_col_dir", "kind": "choice", "values": model.LOAD_DIRECTIONS,
                     "labels": ("st_dir_vertical", "st_dir_horizontal", "st_dir_angle", "st_dir_member"),
                     "field": "direction", "after": _fix_direction},
                    {"title": "st_col_angle", "kind": "number",
                     "get": lambda e: model.fmt_number(e["angle"]) if "angle" in e else "",
                     "set": _set_angle},
                    {"title": "st_col_value", "kind": "number", "get": lambda e: mag(e, "magnitude"),
                     "set": lambda e, v: set_mag(e, "magnitude", v)},
                    {"title": "st_col_unit", "kind": "text",
                     "get": lambda e: (e.get("magnitude") or {}).get("unit", ""),
                     "set": lambda e, v: _set_unit(e, "magnitude", v)},
                    {"title": "st_col_width", "kind": "number", "get": _width_text, "set": _set_width},
                    {"title": "st_col_name", "kind": "text", "get": lambda e: e.get("label", ""),
                     "set": lambda e, v: e.update(label=v) or True},
                    {"title": "st_col_show", "kind": "choice", "values": model.LABEL_MODES,
                     "labels": ("st_show_none", "st_show_name", "st_show_value", "st_show_both"), "field": "show"},
                    colour_column,
                ],
            },
            "line_loads": {
                "title": "st_tab_line_loads",
                "columns": [
                    {"title": "st_col_id", "kind": "id"},
                    {"title": "st_col_member", "kind": "ref", "of": "members", "field": "member"},
                    {"title": "st_col_shape", "kind": "choice", "values": model.LINE_LOAD_SHAPES,
                     "labels": ("st_shape_uniform", "st_shape_linear"), "field": "shape", "after": _fix_shape},
                    {"title": "st_col_dir", "kind": "choice", "values": model.LOAD_DIRECTIONS,
                     "labels": ("st_dir_vertical", "st_dir_horizontal", "st_dir_angle", "st_dir_member"),
                     "field": "direction", "after": _fix_direction},
                    {"title": "st_col_angle", "kind": "number",
                     "get": lambda e: model.fmt_number(e["angle"]) if "angle" in e else "",
                     "set": _set_angle},
                    {"title": "st_col_value", "kind": "number", "get": lambda e: mag(e, "magnitude"),
                     "set": lambda e, v: set_mag(e, "magnitude", v)},
                    {"title": "st_col_value_end", "kind": "number", "get": lambda e: mag(e, "magnitude_end"),
                     "set": lambda e, v: set_mag(e, "magnitude_end", v),
                     "enabled": lambda e: e.get("shape") == "linear"},
                    {"title": "st_col_unit", "kind": "text",
                     "get": lambda e: (e.get("magnitude") or {}).get("unit", ""),
                     "set": lambda e, v: _set_unit(e, "magnitude", v)},
                    {"title": "st_col_width", "kind": "number", "get": _width_text, "set": _set_width},
                    {"title": "st_col_name", "kind": "text", "get": lambda e: e.get("label", ""),
                     "set": lambda e, v: e.update(label=v) or True},
                    {"title": "st_col_show", "kind": "choice", "values": model.LABEL_MODES,
                     "labels": ("st_show_none", "st_show_name", "st_show_value", "st_show_both"), "field": "show"},
                    colour_column,
                ],
            },
            "dimensions": {
                "title": "st_tab_dimensions",
                "columns": [
                    {"title": "st_col_id", "kind": "id"},
                    {"title": "st_col_dim_kind", "kind": "choice", "values": model.DIMENSION_KINDS,
                     "labels": ("st_dim_horizontal", "st_dim_vertical", "st_dim_parallel", "st_dim_angle"),
                     "get_value": lambda e: e.get("kind"), "set_value": set_dim_kind,
                     # an angle is not a length with another name: it is measured between members, so its kind is not a cell to change
                     "enabled": lambda e: e.get("kind") != "angle"},
                    {"title": "st_col_dim_from", "kind": "text",
                     "get": lambda e: anchor_text(e, "from"),
                     "set": lambda e, v: set_anchor(e, "from", v)},
                    {"title": "st_col_dim_to", "kind": "text",
                     "get": lambda e: anchor_text(e, "to"),
                     "set": lambda e, v: set_anchor(e, "to", v)},
                    {"title": "st_col_dim_offset", "kind": "number",
                     "get": lambda e: model.fmt_number(float(e.get("offset", 0.0))),
                     "set": lambda e, v: _set_number(e, "offset", v)},
                    # what was measured, whatever the figure writes: the list says the dimension's answer even where its `show` hides it
                    {"title": "st_col_dim_value", "kind": "text", "readonly": True,
                     "get": lambda e: model.dimension_value_text(self.source, e), "set": lambda e, v: True},
                    {"title": "st_col_dim_text", "kind": "text", "get": lambda e: e.get("label", ""),
                     "set": lambda e, v: e.update(label=v) or True},
                    # what the figure writes beside it, a load's own four; `show` written the moment it is chosen, a dimension that states none reading as it was drawn before the choice existed (statics.dimension_show)
                    {"title": "st_col_show", "kind": "choice", "values": model.LABEL_MODES,
                     "labels": ("st_show_none", "st_show_name", "st_show_value", "st_show_both"),
                     "get_value": model.dimension_show, "set_value": lambda e, v: e.update(show=v)},
                ],
            },
        }

    def bar_tip(self, widget, name_key, tip_key):
        """Names a control of the bar and says how it is used (flowbar.set_tip), and keeps the two keys it said it with in `bar_tips` -- what tests/test_toolbar.py reads each language's words back by."""
        set_tip(widget, self.t(name_key), self.t(tip_key))
        self.bar_tips.append((widget, name_key, tip_key))
        return widget

    def bar_button(self, icon, name_key, tip_key, checkable=False):
        """A control of the tool bar: its symbol alone in a square button as tall as a tool of the position plan's bar (flowbar.size_tool), and its name in bold with how it is used in the tooltip the pointer shows after half a second (flowbar.set_tip, v0.94)."""
        button = QToolButton()
        button.setCheckable(checkable)
        button.setAutoRaise(True)
        button.setFont(self.app.font())
        if icon is not None and not icon.isNull():
            button.setIcon(icon)
        else:
            button.setText(self.t(name_key))     # nothing draws a symbol for it: its word, kept compact
        self.bar_tip(button, name_key, tip_key)
        size_tool(button)
        return button

    def tool_button(self, tool, key):
        """One tool, its symbol alone -- the very symbol the figure draws, or the bar's own for the navigation (flowbar.ICONS) -- since the engineer judged the symbols clear enough to need no name (v0.94)."""
        px = symbol_px(self.app.font())
        icon = svg_icon(tool, px, self.icon_ink, self.icon_ground)
        if icon.isNull() and tool in flowbar.ICONS:
            icon = flowbar.icon(tool, px, theme.colour("ink"))
        button = self.bar_button(icon, key, tip_key(tool), checkable=True)
        button.clicked.connect(lambda _c=False, t=tool: self.choose_tool(t))
        self.tool_group.addButton(button)
        self.tool_buttons[tool] = button
        return button

    def tool_box(self, title_key, tools):
        """One group of the tool bar: its tools side by side, a thin line before them (flowbar.tool_group), its name the group's accessible name."""
        return tool_group([self.tool_button(tool, key) for tool, key in tools], self.t(title_key))

    def build_center(self):
        panel = QWidget()
        box = QVBoxLayout(panel)
        box.setContentsMargins(0, 0, 0, 0)
        self.canvas = StaticsCanvas()
        # The figure is drawn in the window's own language, so the preview reads like the report that language would set.
        self.canvas.lang = self.app.lang
        self.tool_group = QButtonGroup(self)
        self.tool_group.setExclusive(True)
        self.tool_buttons = {}
        self.bar_tips = []      # (control, name key, use key), every control of the bar
        # a dark theme needs the symbols in its own ink; a light one keeps the figure's, so a button looks like the drawing
        text_colour = self.palette().buttonText().color()
        ground_colour = self.palette().button().color()
        dark = text_colour.lightness() > ground_colour.lightness()
        self.icon_ink = text_colour.name() if dark else None
        self.icon_ground = ground_colour.name() if dark else None

        # The bar after the position plan's (v0.94): the navigation, then the history, then a run of tools per kind of thing, every control its symbol alone and as tall as the plan's tools, the groups parted by a thin line and named by no title.
        bar = FlowLayout(spacing=BAR_SPACING)
        font = self.app.font()
        px = symbol_px(font)
        ink = theme.colour("ink")
        view = [self.tool_button("select", "st_tool_select"), self.tool_button("pan", "st_tool_pan")]
        fit = self.bar_button(flowbar.icon("fit", px, ink), "st_bar_fit", "st_tip_fit")
        fit.clicked.connect(lambda: self.canvas.fit())
        view.append(fit)
        # the grid's step and the snapping are settings rather than tools: a combo as tall as a button, and a toggle drawn as a magnet
        self.grid_combo = QComboBox()
        for choice in GRID_CHOICES:
            self.grid_combo.addItem(self.t("st_grid_auto") if choice == "auto" else f"{choice:g} m", choice)
        flowbar.size_combo(self.grid_combo)
        self.bar_tip(self.grid_combo, "st_grid", "st_tip_grid")
        self.grid_combo.currentIndexChanged.connect(self.on_grid)
        self.snap_button = self.bar_button(flowbar.icon("snap", px, ink), "st_snap", "st_tip_snap", checkable=True)
        self.snap_button.setChecked(True)
        self.snap_button.toggled.connect(self.on_snap)
        view += [self.grid_combo, self.snap_button]
        bar.addWidget(tool_group(view, self.t("st_group_view")))

        history = []
        for name, key, tip, slot in (("undo", "st_undo", "st_tip_undo", self.undo), ("redo", "st_redo", "st_tip_redo", self.redo)):
            button = self.bar_button(flowbar.icon(name, px, ink), key, tip)
            button.clicked.connect(slot)
            history.append(button)
        bar.addWidget(tool_group(history, self.t("st_group_history")))

        for title_key, tools in TOOL_GROUPS:
            bar.addWidget(self.tool_box(title_key, tools))

        bar_holder = FlowWidget()
        bar_holder.setLayout(bar)
        self.bar_area = ToolBarArea(bar_holder)

        # The three heights are the engineer's (v0.66): the bar and the lists each give their height back to the drawing by being dragged shorter, which is what the drawing is short of. Not collapsible -- a bar or a list panel dragged to nothing is one the engineer has to know to drag back out of an edge.
        self.center_split = QSplitter(Qt.Orientation.Vertical)
        self.center_split.setChildrenCollapsible(False)
        self.center_split.addWidget(self.bar_area)
        self.center_split.addWidget(self.canvas)
        self.center_split.addWidget(self.build_tables())
        for index, stretch in ((0, 0), (1, 5), (2, 3)):
            self.center_split.setStretchFactor(index, stretch)

        # The pointer's coordinates and the tool's hint are drawn inside the drawing, where the eye already is; only the warnings need a box of their own, and it keeps its height so the drawing does not slide under the pointer as a message comes and goes. It stays outside the splitter for that reason: a fixed height is the point of it.
        self.message = QPlainTextEdit()
        self.message.setReadOnly(True)
        self.message.setFixedHeight(3 * self.fontMetrics().height() + 8)
        box.addWidget(self.center_split, 1)
        box.addWidget(self.message)
        # only the widest group of the tool bar, so the panels beside the drawing may be widened as far as the engineer likes
        panel.setMinimumWidth(bar.minimumSize().width() + 12)

        self.canvas.about_to_change.connect(self.push_history)
        self.canvas.changed.connect(self.on_changed)
        self.canvas.selection_changed.connect(self.on_selection)
        self.canvas.pointer.connect(self.on_pointer)
        self.canvas.tool_done.connect(lambda: self.choose_tool("select"))
        self.canvas.refused.connect(self.on_refused)
        return panel

    def slider(self, key, name):
        widget = QSlider(Qt.Orientation.Horizontal)
        widget.setRange(25, 300)
        widget.setValue(100)
        widget.sliderPressed.connect(lambda: setattr(self, "slider_down", True))
        widget.sliderReleased.connect(lambda: setattr(self, "slider_down", False))
        widget.valueChanged.connect(lambda value, k=key: self.on_style(k, value))
        self.style_sliders[key] = widget
        row = QHBoxLayout()
        row.addWidget(plain_label(self.t(name)))
        row.addWidget(widget, 1)
        holder = QWidget()
        holder.setLayout(row)
        return holder

    def build_properties(self):
        outer = QWidget()
        shell = QVBoxLayout(outer)
        shell.setContentsMargins(6, 0, 0, 0)
        # the properties in cards on the soft ground, after the website: a column that scrolls up and down only and is never narrower than its cards (cards.py)
        area, box = cards.column()

        group = cards.card(self.t("st_model"))
        form = cards.form(group)
        # Nom · Description · ID, the identity of every tab of the window (identity.py); read when a field is left, every change being a step of «Annuler» here
        self.identity = identity.IdentityRows(form, self.t, self.on_identity, live=False)
        self.name_edit, self.label_edit, self.id_edit = self.identity.name, self.identity.description, self.identity.id
        self.style_sliders = {}
        for key, name in (("line", "st_style_line"), ("point", "st_style_point"), ("text", "st_style_text")):
            form.addRow(self.slider(key, name))
        box.addWidget(group)

        self.model_width_group = cards.card(self.t("st_model_width"))
        self.model_width_layout = QVBoxLayout(self.model_width_group)
        box.addWidget(self.model_width_group)

        self.selection_group = cards.card(self.t("st_selection"))
        self.selection_layout = QVBoxLayout(self.selection_group)
        box.addWidget(self.selection_group)

        box.addStretch(1)

        shell.addWidget(area, 1)
        actions = QHBoxLayout()
        actions.addStretch(1)
        revert = QPushButton(self.t("st_revert"))
        revert.clicked.connect(self.revert)
        actions.addWidget(revert)
        save = QPushButton(self.t("st_save"))
        save.setDefault(True)
        save.clicked.connect(self.save)
        actions.addWidget(save)
        shell.addLayout(actions)
        return outer

    def code_field(self, text):
        return richtext.CodeField(text, self.app.mono_font)   # the call as the site sets a code block, coloured (v0.92)

    def copy_button(self, text):
        return richtext.copy_button(self.app.t("copy"), self.app.t("copied_short"), lambda: self.app.copy(text))

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                # hidden before it is detached: a shown widget with no parent is a top-level window, and Qt shows it as one (v0.77, connectors_tab._clear)
                widget.hide()
                widget.setParent(None)
            elif item.layout() is not None:
                self.clear_layout(item.layout())
