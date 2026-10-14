"""StaticsTab's properties of what is selected -- a point and its support, a dimension, a member and its release, a load and its magnitude, a label, and the size and style of an entry -- a mixin of methods moved verbatim out of calc/tools/statics_tab.py (issue #30). StaticsTab names it among its bases.
"""

from PySide6.QtGui import QColor, QIcon, QKeySequence, QPainter, QPixmap, QShortcut
from PySide6.QtWidgets import (
    QButtonGroup, QCheckBox, QComboBox, QDoubleSpinBox, QGridLayout,
    QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPlainTextEdit,
    QPushButton, QRadioButton, QSlider, QSplitter, QTabWidget, QTableWidget,
    QTableWidgetItem, QToolButton, QVBoxLayout, QWidget,
)
import theme  # the colours this tab states itself (theme.py, v0.90)
import text_pane  # a text's pane, the four drawing engines' one (issue #43)
import linkable_spin  # the button beside a field that may follow a variable (spec 2026-10-11-variables-liees-champs-et-textes)
import variable_sources  # what a field being linked may take (variable_sources.linkable)
import cards  # the properties in cards, after the website (cards.py, v0.95)
import stylefactors  # the factors one entry states over the drawing's three, as an overridden b/h is shown (stylefactors.py, v0.99)
from domains import figure_style  # which of the three each kind of entry may state (figure_style.py, v0.99)
from domains import statics as model
from statics_tab_build import (  # split out of this module (issue #30): every name it had is still importable from it
    GRID_CHOICES,
    ICON_PX,
    MEMBER_ICONS,
    RELEASES,
    SWATCH_FILL,
    SWATCH_INK,
    TOOL_GROUPS,
    _as_number,
    _canvas,
    _fix_direction,
    _fix_kind,
    _fix_shape,
    _member_icon,
    _set_along,
    _set_angle,
    _set_number,
    _set_stiffness,
    _set_unit,
    _set_width,
    _stiffness_text,
    _width_text,
    plain_label,
    svg_icon,
    StaticsBuildMixin,
)


# What a load's magnitude may name (UI-005): a force, a force per metre or per square metre -- which an influence width makes a load per metre --, or a moment
MAGNITUDE_UNITS = ("kN", "kN/m", "kN/m²", "kNm")


class StaticsPropertiesMixin:
    """Methods of statics_tab.StaticsTab, moved verbatim (issue #30): the class names this mixin among its bases."""

    def refresh_selection(self):
        self.clear_layout(self.selection_layout)
        self.style_rows, self.style_may = None, ()
        collection, entry = self.canvas.selected()
        if entry is None:
            self.selection_layout.addWidget(self.note(self.t("st_none_selected")))
            return
        self.selection_layout.addWidget(plain_label(f"{entry['id']}"))
        if collection == "points":
            self.point_properties(entry)
        elif collection == "members":
            self.member_properties(entry)
        elif collection in ("point_loads", "line_loads"):
            self.load_properties(collection, entry)
        elif collection == "dimensions":
            self.dimension_properties(entry)
        elif collection == model.figure_text.COLLECTION:
            self.text_properties(entry)
        self.style_properties(collection, entry)
        if collection != model.figure_text.COLLECTION:   # a text is moved itself and has no place of its own to come back to
            self.label_properties(collection, entry)

    def style_properties(self, collection, entry):
        """The factors this one entry states over the drawing's three (figure_style): one slider per factor it is drawn with, in per cent, and nothing at all for a factor it does not draw -- a `point` on a bar would be a field nobody could see the effect of.

        Shown the way an overridden b/h is shown (v0.75): while the entry states none, a row stands at 100 % and follows the drawing; the moment it states one, its name and its readout are orange and «Reprendre» appears beside them. Setting a slider back to 100 % by hand does not take the factor off -- the b/h rule, «typing the very value the position holds still writes it over».
        """
        may = figure_style.allowed(model.STYLE_KIND, collection)
        if not may:
            return
        group = cards.card(self.t("st_style_own"))
        form = cards.form(group)
        form.addRow(cards.note(self.t("st_style_own_note")))
        self.style_may = may
        self.style_rows = stylefactors.EntryRows(
            form, self.t, "st",
            lambda key, factor, e=entry: self.set_entry_style(e, key, factor),
            lambda key, e=entry: self.take_back_entry_style(e, key),
            pressed=self.style_drag_begin,
            released=self.style_drag_end,
        )
        self.style_rows.fill(entry, may)
        self.selection_layout.addWidget(group)

    def style_drag_begin(self):
        """A slider taken hold of: the one step of «Annuler» the whole drag makes, pushed here rather than at every pixel."""
        self.slider_down = True
        self.push_history()

    def style_drag_end(self):
        """The slider let go: the step is dropped again where the drag ended where it began -- `edit`'s own rule, applied to a change that arrives one pixel at a time.

        ⚠️ The drawing's own three sliders still leave a drag outside the history altogether (`on_style`), which is a separate thing and not this version's to change.
        """
        self.slider_down = False
        if self.undo_stack and self.undo_stack[-1] == self.source:
            self.undo_stack.pop()

    def set_entry_style(self, entry, key, factor):
        """One factor this entry states over the drawing's. During a drag the change is applied straight, the step having been pushed when the slider was taken hold of; typed or clicked, it is one `edit`."""
        if self.loading:
            return
        if self.slider_down:
            entry.setdefault("style", {})[key] = factor
            self.canvas.invalidate()
            self.dirty = True
            self.update_list_marker()
        else:
            self.edit(lambda: entry.setdefault("style", {}).update({key: factor}))
        self.refresh_style_rows(entry)

    def take_back_entry_style(self, entry, key):
        """«Reprendre»: the factor leaves the entry, which follows the drawing again -- and the whole `style` goes with the last of them, so an entry that overrides nothing is saved exactly as it was before the factors existed."""
        def apply():
            own = entry.get("style")
            if not own:
                return
            own.pop(key, None)
            if not own:
                entry.pop("style", None)
        self.edit(apply)
        self.refresh_style_rows(entry)

    def refresh_style_rows(self, entry):
        """The card's own rows read again -- the orange, the readout, «Reprendre». Only the rows: rebuilding the whole panel from inside a slider's own signal would delete the slider being dragged."""
        if self.style_rows is not None:
            self.style_rows.fill(entry, self.style_may)

    def point_properties(self, entry):
        # where the point is, each coordinate typed or following a variable of the export (D-05: the geometry)
        place = cards.card(self.t("st_coords"))
        place_form = cards.form(place)
        for key in ("x", "z"):
            spin = QDoubleSpinBox()
            spin.setRange(-1e5, 1e5)
            spin.setDecimals(3)
            spin.setSuffix(" m")
            spin.setValue(float(entry.get(key, 0.0)))
            spin.valueChanged.connect(lambda v, e=entry, k=key: self.edit(lambda: e.update({k: model._clean(v)})))
            place_form.addRow(self.app.label("st_coord_" + key), self.linked_field(spin, entry, key, "m", key))
        self.selection_layout.addWidget(place)
        group = cards.card(self.t("st_support"))   # a card inside the selection's card (cards.py)
        form = cards.form(group)
        support = self.support_of(entry)
        combo = QComboBox()
        combo.addItem(self.t("st_support_none"), "")
        for value, key in zip(model.SUPPORT_TYPES,
                              ("st_tool_support_fixed", "st_tool_support_pinned", "st_tool_support_roller")):
            combo.addItem(self.t(key), value)
        combo.setCurrentIndex(max(combo.findData(support["type"] if support else ""), 0))
        combo.currentIndexChanged.connect(lambda _i, e=entry, c=combo: self.change_support(e, c.currentData()))
        form.addRow(combo)
        if support is not None:
            angle = QDoubleSpinBox()
            angle.setRange(-180.0, 180.0)
            angle.setDecimals(1)
            angle.setSingleStep(0.1)
            angle.setValue(float(support.get("angle", 0.0)))
            angle.valueChanged.connect(lambda v, s=support: self.edit(lambda: s.update(angle=round(float(v), 1))))
            form.addRow(self.app.label("st_support_angle"), angle)
        if support is not None and support["type"] in model.HINGED_SUPPORTS:
            # a Festlager and a Loslager are hinges: where their pin is drawn is the engineer's to say, the model being unable to tell whether the bar turns about it or runs over it
            hinge = QComboBox()
            for value, key in zip(model.SUPPORT_HINGES,
                                  ("st_support_hinge_shared", "st_support_hinge_through")):
                hinge.addItem(self.t(key), value)
            hinge.setCurrentIndex(max(hinge.findData(support.get("hinge", model.SUPPORT_HINGES[0])), 0))
            hinge.currentIndexChanged.connect(
                lambda _i, s=support, c=hinge: self.edit(lambda: s.update(hinge=c.currentData()))
            )
            form.addRow(self.app.label("st_support_hinge"), hinge)
        self.selection_layout.addWidget(group)

    def set_support(self, point, type_):
        """The support a point carries, set from the list or from the panel. Nothing here is an edit on its own -- the caller wraps it."""
        existing = self.support_of(point)
        if not type_:
            if existing is not None:
                self.source["supports"].remove(existing)
        elif existing is not None:
            existing["type"] = type_
            # an Einspannung has no pin to place, and a source carrying one on it is refused
            if type_ not in model.HINGED_SUPPORTS:
                existing.pop("hinge", None)
        else:
            self.source["supports"].append(
                {"id": model.next_id(self.source, "supports"), "point": point["id"], "type": type_, "angle": 0.0}
            )

    def change_support(self, point, type_):
        self.edit(lambda: self.set_support(point, type_))
        self.refresh_selection()

    def dimension_properties(self, entry):
        """What a dimension carries beside its two ends: how far from them its line is drawn, what it measured, its name, and what the figure writes beside it -- a load's own four, `show`."""
        group = cards.card(self.t("st_dimension"))
        form = cards.form(group)
        form.addRow(self.app.label("st_col_dim_value"),
                    plain_label(model.dimension_value_text(self.source, entry)))
        offset = QDoubleSpinBox()
        offset.setRange(-10000.0, 10000.0)
        offset.setDecimals(3)
        offset.setSingleStep(0.1)
        offset.setValue(float(entry.get("offset", 0.0)))
        offset.valueChanged.connect(
            lambda v, e=entry: self.edit(lambda: e.update(offset=round(float(v), 3)))
        )
        form.addRow(self.app.label("st_col_dim_offset"), offset)
        text = QLineEdit(entry.get("label", ""))
        text.setToolTip(self.t("st_dim_text_hint"))
        text.editingFinished.connect(
            lambda e=entry, f=text: self.edit(lambda: e.update(label=f.text()))
        )
        form.addRow(self.app.label("st_col_dim_text"), text)
        form.addRow(self.app.label("st_col_show"), self.show_combo(model.dimension_show(entry),
                    lambda value, e=entry: self.edit(lambda: e.update(show=value))))
        self.selection_layout.addWidget(group)

    def show_combo(self, current, apply):
        """What a load or a dimension writes beside itself, as a combo of the four -- the lists' own column, in the panel. `apply(value)` makes the change, as one step of «Annuler»."""
        combo = QComboBox()
        for value, key in zip(model.LABEL_MODES, ("st_show_none", "st_show_name", "st_show_value", "st_show_both")):
            combo.addItem(self.t(key), value)
        combo.setCurrentIndex(max(combo.findData(current), 0))
        combo.currentIndexChanged.connect(lambda _i, c=combo: apply(c.currentData()))
        return combo

    def colour_combo(self, entry):
        """The colour a load is drawn in, as a combo of the five, each beside a swatch of its own ink -- the lists' own column, in the panel."""
        combo = QComboBox()
        for name, ink in model.LOAD_COLOURS.items():
            swatch = QPixmap(14, 14)
            swatch.fill(QColor(ink))
            combo.addItem(QIcon(swatch), self.t(f"st_colour_{name}"), name)
        combo.setCurrentIndex(max(combo.findData(model.load_colour(entry)), 0))
        combo.currentIndexChanged.connect(lambda _i, c=combo, e=entry: self.edit(lambda: self.set_load_colour(e, c.currentData())))
        return combo

    @staticmethod
    def set_load_colour(entry, name):
        """A load's colour, set from its list or its panel. Red is the colour a load states by stating none, so choosing it takes the key off: a model left red is saved exactly as it was before the colour could be chosen. Nothing here is an edit on its own -- the caller wraps it."""
        if name == model.DEFAULT_LOAD_COLOUR or name not in model.LOAD_COLOURS:
            entry.pop("color", None)
        else:
            entry["color"] = name

    def member_properties(self, entry):
        length = model.member_length(self.source, entry["id"])
        self.selection_layout.addWidget(plain_label(f"{self.app.label('st_length')} {model.fmt_number(length)} m"))
        if entry.get("kind") == "spring":
            group = cards.card(self.t("st_stiffness"))
            form = cards.form(group)
            stiffness = entry.setdefault("stiffness", {"value": 1000.0, "unit": model.MEMBER_STIFFNESS_UNIT})
            value = QDoubleSpinBox()
            value.setRange(0.001, 1e9)
            value.setDecimals(3)
            value.setValue(float(stiffness["value"]))
            value.setSuffix(" " + stiffness["unit"])
            value.valueChanged.connect(lambda v, s=stiffness: self.edit(lambda: s.update(value=float(v))))
            form.addRow(self.linked_field(value, entry, "stiffness", model.MEMBER_STIFFNESS_UNIT, "k"))
            self.selection_layout.addWidget(group)
        for end, key in (("start", "st_release_start"), ("end", "st_release_end")):
            group = cards.card(self.t(key))
            form = cards.form(group)
            release = next((r for r in self.source["releases"]
                            if r["member"] == entry["id"] and r["end"] == end), None)
            combo = QComboBox()
            combo.addItem(self.t("st_release_none"), None)
            for label_key, dof, spring, _tool in RELEASES:
                combo.addItem(self.t(label_key), (dof, spring))
            current = None
            if release is not None:
                current = (release["dof"], release.get("stiffness") is not None)
            combo.setCurrentIndex(max(combo.findData(current), 0))
            combo.currentIndexChanged.connect(
                lambda _i, m=entry["id"], e=end, c=combo: self.set_release(m, e, c.currentData())
            )
            form.addRow(combo)
            if release is not None and release.get("stiffness"):
                stiffness = QDoubleSpinBox()
                stiffness.setRange(0.001, 1e9)
                stiffness.setDecimals(3)
                stiffness.setValue(float(release["stiffness"]["value"]))
                stiffness.setSuffix(" " + release["stiffness"]["unit"])
                stiffness.valueChanged.connect(
                    lambda v, r=release: self.edit(lambda: r["stiffness"].update(value=float(v)))
                )
                form.addRow(self.app.label("st_stiffness"), self.linked_field(stiffness, release, "stiffness", release["stiffness"]["unit"], "k"))
            self.selection_layout.addWidget(group)

    def apply_release(self, member_id, end, choice):
        """The release at one end of one member, set from a member's panel or from the row of the point it sits on."""
        self.set_release(member_id, end, choice)
        self.set_tables()

    def set_release(self, member_id, end, choice):
        def apply():
            existing = [r for r in self.source["releases"] if r["member"] == member_id and r["end"] == end]
            for r in existing:
                self.source["releases"].remove(r)
            if choice is None:
                return
            dof, spring = choice
            entry = {"id": model.next_id(self.source, "releases"), "member": member_id, "end": end, "dof": dof}
            if spring and dof in model.SPRING_UNITS:
                entry["stiffness"] = {"value": 1000.0, "unit": model.SPRING_UNITS[dof]}
            self.source["releases"].append(entry)
        self.edit(apply)
        self.refresh_selection()

    def load_properties(self, collection, entry):
        # how the load is drawn -- its colour and what it writes beside itself -- the two columns of its list, in the panel
        look = cards.card(self.t("st_load_look"))
        look_form = cards.form(look)
        look_form.addRow(self.app.label("st_col_colour"), self.colour_combo(entry))
        look_form.addRow(self.app.label("st_col_show"), self.show_combo(entry.get("show", "name+value"),
                         lambda value, e=entry: self.edit(lambda: e.update(show=value))))
        self.selection_layout.addWidget(look)

        group = cards.card(self.t("st_magnitude"))
        form = cards.form(group)
        is_reference = model.magnitude_kind(entry.get("magnitude")) == "reference"
        literal = QRadioButton(self.t("st_magnitude_value"))
        variable = QRadioButton(self.t("st_magnitude_var"))
        literal.setChecked(not is_reference)
        variable.setChecked(is_reference)
        literal.toggled.connect(lambda on, e=entry: self.set_magnitude_kind(e, on))
        form.addRow(literal)
        form.addRow(variable)
        if is_reference:
            m = entry["magnitude"]
            # the variable it names, chosen in the «Variables» tab as every linked field's is (spec 2026-10-11-variables-liees-champs-et-textes, UI-005): no list of domains, cases and variables of its own any more
            row = QWidget()
            line = QHBoxLayout(row)
            line.setContentsMargins(0, 0, 0, 0)
            line.addWidget(QLabel(self.variable_text(m)), 1)
            choose = QPushButton(self.t("st_var_choose"))
            choose.clicked.connect(lambda _c=False, e=entry: self.pick_magnitude(e))
            line.addWidget(choose)
            form.addRow(self.app.label("st_var"), row)
            # the var may be taken with a factor and a constant -- 0.8 x SL, SL + 10 -- which is how a design value is written beside the characteristic one it comes from
            factor = QDoubleSpinBox()
            factor.setRange(-1e6, 1e6)
            factor.setDecimals(4)
            factor.setValue(float(m.get("factor", 1.0)))
            factor.valueChanged.connect(lambda v, mm=m: self.edit(lambda: mm.update(factor=float(v))))
            form.addRow(self.app.label("st_factor"), factor)
            constant = QDoubleSpinBox()
            constant.setRange(-1e9, 1e9)
            constant.setDecimals(4)
            constant.setValue(float(m.get("offset", 0.0)))
            constant.valueChanged.connect(lambda v, mm=m: self.edit(lambda: mm.update(offset=float(v))))
            form.addRow(self.app.label("st_offset"), constant)
            told = QLineEdit(m.get("description", ""))
            told.editingFinished.connect(lambda mm=m, t=told: self.edit(lambda: mm.update(description=t.text())))
            form.addRow(self.app.label("st_value_desc"), told)
        else:
            value = QDoubleSpinBox()
            value.setRange(-1e9, 1e9)
            value.setDecimals(3)
            value.setValue(float((entry.get("magnitude") or {}).get("value", 0.0)))
            value.valueChanged.connect(
                lambda v, e=entry: self.edit(lambda: e.setdefault("magnitude", {}).update(value=float(v)))
            )
            form.addRow(self.app.label("st_col_value"), value)
            unit = QLineEdit((entry.get("magnitude") or {}).get("unit", ""))
            unit.editingFinished.connect(
                lambda e=entry, u=unit: self.edit(lambda: e.setdefault("magnitude", {}).update(unit=u.text().strip()))
            )
            form.addRow(self.app.label("st_col_unit"), unit)
        width, from_model = model.width_of(self.source, entry)
        resolved = model.resolve(entry.get("magnitude"), width, self.values, from_model)
        text = (self.t("st_unresolved", text=resolved["missing"]) if resolved["missing"]
                else self.t("st_resolved", text=f"{model.fmt_number(resolved['value'])} {resolved['unit']}".strip()))
        note = self.note(text)
        if resolved["missing"]:
            note.setStyleSheet(f"color: {theme.colour('warning')};")
        form.addRow(note)
        expression = model.value_note(entry, resolved, width)
        if expression:
            form.addRow(self.note(self.t("st_expression", text=expression)))
        self.selection_layout.addWidget(group)

        width_group = cards.card(self.t("st_width_group"))
        wlayout = QVBoxLayout(width_group)
        self.width_form(wlayout, entry, "st_width_use", lambda on, e=entry: self.set_width(e, on))
        self.selection_layout.addWidget(width_group)

    def set_magnitude_kind(self, entry, literal):
        def apply():
            if literal:
                # the variable it named is kept here, not in the source, so that changing one's mind twice does not lose it
                if model.magnitude_kind(entry.get("magnitude")) == "reference":
                    self.last_reference[entry["id"]] = dict(entry["magnitude"])
                if entry["id"] in self.last_literal:
                    entry["magnitude"] = dict(self.last_literal[entry["id"]])
                else:
                    # a point load carries a force, a line load a force per metre
                    entry["magnitude"] = {"value": 1.0, "unit": "kN" if "point" in entry else "kN/m"}
                return
            if model.magnitude_kind(entry.get("magnitude")) == "literal":
                self.last_literal[entry["id"]] = dict(entry["magnitude"])
            entry["magnitude"] = dict(self.last_reference[entry["id"]])
        if not literal and entry["id"] not in self.last_reference:
            # nothing named yet: the variable is chosen first, and the load stays a value where the choice is given up
            self.pick_magnitude(entry)
            return
        self.edit(apply)
        self.refresh_selection()

    def variable_text(self, magnitude):
        """The variable a magnitude names, as the «Variables» tab shows it: its symbol and its domain."""
        record = model.links.lookup(magnitude, self.values) or {}
        domain = magnitude["instance"] if magnitude.get("origin") == model.links.FORMULAS else f"{magnitude['domain']} · {magnitude['instance']}"
        return f"{record.get('symbol') or magnitude['var']} — {domain}"

    def pick_magnitude(self, entry):
        """The «Variables» tab in its choosing mode for a load's magnitude (UI-001, UI-005): a number of the export or of a «Formule» domain that is a force, a force per metre or per square metre, or a moment."""
        begin = getattr(self.app, "begin_variable_pick", None)

        def accept(var, domain):
            return any(variable_sources.linkable(var, domain, unit) for unit in MAGNITUDE_UNITS)

        def done(chosen):
            if chosen is not None:
                origin, domain_name, var, address = chosen
                link = model.links.from_choice(origin, domain_name, var.key, address)
                if link is not None:
                    def apply():
                        kept = {k: v for k, v in (entry.get("magnitude") or {}).items() if k in ("factor", "offset", "description")}
                        if model.magnitude_kind(entry.get("magnitude")) == "literal":
                            self.last_literal[entry["id"]] = dict(entry["magnitude"])
                        entry["magnitude"] = {**link, **kept}
                    self.edit(apply)
            self.refresh_selection()

        if begin is None or not begin(done, self.t("st_var_pick_title", load=entry["id"]), accept):
            self.app.set_status(self.t("st_var_unavailable"))
            self.refresh_selection()

    def linked_field(self, spin, owner, key, unit, label):
        """`spin`, editing `owner[key]`, with the button that links it to a variable of the export (spec 2026-10-11-variables-liees-champs-et-textes, UI-001, D-05): the widget the form holds in its place. The link is one step of «Annuler», as every edit of the model is."""
        wrapper = linkable_spin.LinkableSpin(spin, unit, label, lambda: self.app, self.app.lang)
        wrapper.set_link(model.links.links_of(owner).get(key), self.values)

        def changed():
            link = wrapper.link()

            def apply():
                found = dict(model.links.links_of(owner))
                if link is None:
                    found.pop(key, None)
                else:
                    found[key] = link
                if found:
                    owner[model.links.LINKS] = found
                else:
                    owner.pop(model.links.LINKS, None)
            self.edit(apply)
        wrapper.changed.connect(changed)
        return wrapper

    def text_properties(self, entry):
        """A text's pane (issue #43, UI-004): text_pane's, the four engines' one -- its content, «Insérer une variable», a card per variable."""
        self.text_pane = text_pane.TextPane(entry, lambda: self.app, self.app.lang, self.edit, self.refresh_selection, self.values,
                                            bool(getattr(self.app, "read_only", False)))
        self.selection_layout.addWidget(self.text_pane)

    def set_width(self, entry, on):
        def apply():
            if on:
                entry["width"] = {"value": 1.0, "unit": model.WIDTH_UNIT,
                                  "label": model.DEFAULT_WIDTH_LABEL, "description": "", "show": True}
            else:
                entry.pop("width", None)
        self.edit(apply)
        self.refresh_selection()

    def label_properties(self, collection, entry):
        if entry.get("label_offset"):
            button = QPushButton(self.t("st_reset_label"))
            button.clicked.connect(
                lambda _c=False, e=entry: (self.edit(lambda: e.pop("label_offset", None)), self.refresh_selection())
            )
            self.selection_layout.addWidget(button)
        else:
            self.selection_layout.addWidget(self.note(self.t("st_label_home")))
