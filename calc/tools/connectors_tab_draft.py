"""ConnectorsTab's draft read off the form and the form filled from it, the live preview with its results and table, and the table's buttons -- a mixin of methods moved verbatim out of calc/tools/connectors_tab.py (issue #30). ConnectorsTab names it among its bases.
"""

import copy
from PySide6.QtCore import QByteArray, QEvent, Qt, QTimer
from PySide6.QtWidgets import (
    QAbstractItemView, QAbstractSpinBox, QApplication, QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout, QGroupBox,
    QHBoxLayout, QLabel, QMessageBox, QPushButton,
    QSizePolicy, QSpinBox, QSplitter, QTableWidget, QTableWidgetItem, QToolButton,
    QVBoxLayout, QWidget,
)
import build_reference as ref
import project  # where the project this tab works on is (calc/project.py)
import theme  # the colours this tab states itself: the orange of a value written over, a lit result (theme.py, v0.90)
import richtext  # symbols as mathematics, the calls coloured as the site's code, «✓» once copied (richtext.py, v0.92)
import cards  # the form and what is read off it in cards, after the website (cards.py)
import display_view  # the «Affichage» view: the command, its options, the call and the page (display_view.py, v0.117)
import validation
import linkable_spin  # the export's values a linked number is shown against (spec 2026-10-11-variables-liees-champs-et-textes)
from domains import connector, connector_svg, dowel, links
from domains import schema as schema_model
from i18n import strings
from norms import sia263, sia265, sn_en_14592
from connectors_tab_form import COLUMN_LABEL_WIDTH, ICON_PX, LABEL_WIDTH, SYMBOL_WIDTH, TOOL_HEIGHT, TOOL_MIN_WIDTH, TOOL_TYPES, UNIT_WIDTH, _n, svg_icon, ConnectorsFormMixin  # split out of this module (issue #30): every name it had is still importable from it


# Typst math as the data writes a symbol between dollars, in the rich text a QLabel shows (v0.77): richtext.py's since v0.92, which the loads, the polar moments and the commands tabs set their symbols with too.
_escape_html = richtext.escape


_math_html = richtext.math_html


_prose_html = richtext.prose_html


class ConnectorsDraftMixin:
    """Methods of connectors_tab.ConnectorsTab, moved verbatim (issue #30): the class names this mixin among its bases."""

    def choose_type(self, kind):
        self.source["type"] = kind
        block = connector.TYPE_BLOCK.get(kind)
        for name in set(connector.TYPE_BLOCK.values()):
            if name != block:
                self.source.pop(name, None)
        if block == "dowel" and "dowel" not in self.source:
            self.source["dowel"] = connector.new_dowel()
        self.collapse_types()
        self.touch()
        self.fill_form()

    def collapse_types(self):
        self.collapsed = True
        self.type_box.setVisible(False)
        self.expand_button.setVisible(True)

    def expand_types(self):
        self.collapsed = False
        self.type_box.setVisible(True)
        self.expand_button.setVisible(False)

    def decimal(self, value):
        """A norm's coefficient as a label writes it in the window's language: 1,4 in French and German, 1.4 in English."""
        text = _n(value)
        return text.replace(".", ",") if self.app.lang in ("fr", "de") else text

    def tl(self, text):
        """A word the DATA carries, in the window's language -- through the very glossary the report reads (docs/typst/language.md §4bis), so the tab and the PDF cannot call one assembly two things."""
        return strings.translate(text, self.app.lang)

    def on_position(self, _index=0):
        """A position chosen: the grade follows it again, unless it has been written over."""
        if self.loading:
            return
        self.touch()
        self.fill_material_notes()
        self.refresh()

    def on_dowel_steel(self, _index=0):
        """A grade chosen fills f_u,k with its f_u of SIA 263 Tabelle 1 (D-06); «—» leaves the value as it is."""
        grade = self.dowel_steel_box.currentData() or ""
        if grade:
            self.f_u_k_box.blockSignals(True)
            self.f_u_k_box.setValue(sn_en_14592.f_u_k(grade))
            self.f_u_k_box.blockSignals(False)
        self.touch()

    def on_f_u_k(self, value=0.0):
        """A value typed over the grade's is the engineer's own: the grade goes back to «—», so the report never credits S355 with a value that is not S355's (D-20)."""
        grade = self.dowel_steel_box.currentData() or ""
        if grade and abs(value - sn_en_14592.f_u_k(grade)) > 1e-9:
            self.dowel_steel_box.blockSignals(True)
            self.dowel_steel_box.setCurrentIndex(0)
            self.dowel_steel_box.blockSignals(False)

    def on_diameter(self, _value=0.0):
        self.touch()

    def take_back(self, index):
        """«Reprendre»: the member's grade follows its position again."""
        if index >= len(self.member_fields):
            return
        widgets = self.member_fields[index]
        widgets["overridden"] = False
        # ⚠️ through the member's ELEMENT since v0.74: `widgets["position"]` went with the member form, and reading it
        # raised a KeyError the moment «Reprendre» was clicked (found by the v0.75 audit, held by a test)
        pid = self.element_position(widgets["element"].currentData() or "")
        held = (connector.known_positions(project.current().data_dir).get(pid) or {}).get("strength_class") or ""
        if held:
            at = widgets["grade"].findData(held)
            if at >= 0:
                self.loading = True
                widgets["grade"].setCurrentIndex(at)
                self.loading = False
        self.touch()
        self.fill_material_notes()
        self.refresh()

    def on_assembly(self, _index=0):
        self.source["assembly"] = self.assembly_box.currentData() or self.assembly_box.currentText()
        self.touch()
        self.fill_members()
        self.refresh()

    def adopt_schema(self):
        """A source that names a schema but has nothing chosen off it -- a new connector -- takes that schema's first linear elements as its members and every marker as its fasteners, or every point ticked «connecteur» on a schema with no marker (schema.default_fasteners, v0.77). Only ever applied to a draft the engineer has not touched, so nothing already chosen is overwritten."""
        detail = self.schemas().get(self.source.get("schema", ""))
        if detail is None:
            return
        if not self.source.get("fasteners"):
            self.source["fasteners"] = schema_model.default_fasteners(detail)
            self.source["n_tot"] = {"value": max(1, len(self.source["fasteners"])), "override": False}
        elements = [e["id"] for e in detail.get("elements", []) if e.get("kind") == "linear"]
        for index, member in enumerate(self.source.get("members", [])):
            if not member.get("element") and index < len(elements):
                member["element"] = elements[index]

    def fill_form(self):
        self.loading = True
        s = self.source
        # «Désignation» and «Description» are one field now: a source that stated only a designation shows it here, and saving writes it as the description (draft).
        # An id nobody has typed over is the name's to recompose -- including the one «Nouveau» handed out.
        self.identity.fill(s.get("name", ""), s.get("description") or s.get("label", ""), s.get("id", ""),
                           saved=self.current_id is not None)
        index = self.assembly_box.findData(s.get("assembly", ""))
        if index >= 0:
            self.assembly_box.setCurrentIndex(index)
        self.seismic_box.setChecked(bool(s.get("conditions", {}).get("seismic")))
        self.truss_box.setChecked(bool(s.get("conditions", {}).get("truss")))
        for kind, button in self.type_buttons.items():
            button.setChecked(kind == s.get("type"))
        if s.get("type"):
            self.collapse_types()
        # The schema first: the elements and the markers below are read off it.
        self.fill_schemas()
        self.fill_markers()
        self.loading = False
        self.fill_members()

    def _clear(self, layout):
        """Empty a layout so it can be rebuilt.

        ⚠️ `hide()`, then `setParent(None)`, then `deleteLater()`, and none without the others. `takeAt`
        removes the layout item but leaves the widget a child of the box, and `deleteLater` only destroys
        it at the next turn of the event loop -- so the old rows went on painting under the new ones and
        the whole «Géométrie et matériau» box was drawn twice over. Detaching is what takes them out of the
        box; deleting is what frees them.

        ⚠️ **Hidden first** (v0.77): a widget detached while it was shown and never explicitly hidden is a
        top-level window, and Qt showed it as one on that same turn of the event loop -- the white windows,
        titled with the application's name, that flashed for less than a second each time another connector was chosen
        (six per switch, measured: the old «Diamètre d», «Pièce 1 / Pièce 2», «k_β» and «n_tot» rows).
        """
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                # the boxes inside it go with it: a key naming a widget about to be deleted would be lit at the next hover
                for inner in [widget] + widget.findChildren(QGroupBox):
                    self.box_results.pop(inner, None)
                    self.member_boxes.pop(inner, None)
                    if inner is self.hot_box:
                        self.hot_box = None
                widget.hide()
                widget.setParent(None)
                widget.deleteLater()

    def fill_members(self):
        """«Géométrie et matériau» and «Stabdübel», rebuilt for the assembly in force and then filled.

        Both depend on it: a Holz-Holz joint enters two timber members side by side and no plates, a
        Stahl-Holz joint one member, its `b`, its slots and the cells they feed.
        """
        self.loading = True
        s = self.source
        self._clear(self.material_layout)
        self._clear(self.dowel_layout)
        self.link_fields = {}   # the buttons of the rows about to be built, by (where, key)
        # ⚠️ The read-only cells live in the two boxes just cleared, so the map that names them has to go
        # with them: a QLabel Qt has deleted is still a key here, and writing into it raises
        # «Internal C++ object already deleted» from inside the next refresh.
        self.computed.clear()
        assembly = s.get("assembly", "Holz-Holz zweischnittig")
        spec = dowel.ASSEMBLIES.get(assembly, {"family": "timber-timber", "members": 2})
        self.build_material(assembly, spec, [])
        self.build_dowel(spec)

        timber = [m for m in s.get("members", []) if m.get("role") == "timber"]
        self.diameter_box.setValue((s.get("diameter") or {}).get("value", 12))
        moisture = s.get("moisture_class")
        at = self.moisture_box.findData(moisture)
        self.moisture_box.setCurrentIndex(at if at >= 0 else 0)
        self.steel_box.setCurrentIndex(max(0, self.steel_box.findData(s.get("steel", ""))))
        block = s.get("dowel") or {}
        self.f_u_k_box.setValue((block.get("f_u_k") or {}).get("value", sn_en_14592.f_u_k()))
        self.dowel_steel_box.blockSignals(True)
        self.dowel_steel_box.setCurrentIndex(max(0, self.dowel_steel_box.findData(connector.dowel_steel(s))))
        self.dowel_steel_box.blockSignals(False)
        plate = s.get("plate") or {}
        for key, box in self.plate_boxes.items():
            box.setValue(float((plate.get(key) or {}).get("value") or 0))
        self.n_tot_box.setValue((s.get("n_tot") or {}).get("value", 1))
        self.n_tot_override.setChecked(bool((s.get("n_tot") or {}).get("override")))
        self.sync_n_tot()

        self.fill_elements()
        for index, widgets in enumerate(self.member_fields):
            member = timber[index] if index < len(timber) else connector._new_member()
            material = member.get("material") or {}
            kind = connector.material_kind(material)
            eid = member.get("element") or ""
            at = widgets["element"].findData(eid)
            if at < 0 and eid:
                # An element the schema no longer carries is kept and marked, never silently replaced by
                # whichever entry happened to be first: the reference is the engineer's, and the mark is
                # what tells them to repair it (the plan tab's «T009 (?)» rule).
                widgets["element"].addItem("%s (?)" % eid, eid)
                at = widgets["element"].count() - 1
            widgets["element"].setCurrentIndex(at if at >= 0 else 0)
            widgets["overridden"] = kind == "override"
            pid = self.element_position(eid)
            grade = material.get("grade") or ""
            if not grade and pid:
                grade = (connector.known_positions(project.current().data_dir).get(pid) or {}).get("strength_class") or ""
            at = widgets["grade"].findData(grade or "C24")
            widgets["grade"].setCurrentIndex(at if at >= 0 else 0)
            widgets["predrilled"].setChecked(bool(member.get("predrilled", True)))
            widgets["alpha"].setValue(member.get("alpha") or 0)
            widgets["t"].setValue((member.get("t") or {}).get("value", 100))
            widgets["n"].setValue(member.get("n") or 1)
            widgets["a_1"].setValue((member.get("a_1") or {}).get("value", 0) or 0)
            widgets["grade"].currentIndexChanged.connect(
                lambda _i, i=index: self.mark_override(i))

        plates = next((m.get("plates") for m in s.get("members", []) if m.get("plates")), None)
        if self.plate_fields:
            first = timber[0] if timber else {}
            self.plate_fields["b"].setValue((first.get("t") or {}).get("value", 200))
            self.plate_fields["count"].setValue((plates or {}).get("count", 1))
            self.plate_fields["slot"].setValue((plates or {}).get("slot", {}).get("value", 12))
            self.plate_fields["ratio"].setValue((plates or {}).get("ratio", 0.5))
        self.loading = False
        self.fill_material_notes()

        self.fill_links(timber)

    def mark_override(self, index):
        """A grade typed over a position's stays overridden -- which is the engineer's own rule, so the moment it differs is the moment it is recorded."""
        if self.loading or index >= len(self.member_fields):
            return
        widgets = self.member_fields[index]
        pid = self.element_position(widgets["element"].currentData() or "")
        held = (connector.known_positions(project.current().data_dir).get(pid) or {}).get("strength_class") or ""
        widgets["overridden"] = bool(pid) and (widgets["grade"].currentData() or "") != held
        self.fill_material_notes()

    def fill_material_notes(self):
        """Where the grade and the moisture class come from, said the engineer's way: **a value that follows its position says so in its own field** -- «C24 — T001», «2 — S001, T001» -- and **a line under it appears only when the value is written over**, in orange, with «Reprendre» beside it (or when its position is gone, in orange too).

        Until now a following value was said again in a grey line under the field, which put two lines of text on every value and made the one that mattered -- an override -- look like the others.
        """
        positions = connector.known_positions(project.current().data_dir)
        for widgets in self.member_fields:
            box = widgets["grade"]
            pid = self.element_position(widgets["element"].currentData() or "")
            held = (positions.get(pid) or {}).get("strength_class") or ""
            note, back = "", False
            following = bool(pid) and pid in positions and not widgets.get("overridden")
            box.blockSignals(True)
            if following and held and box.findData(held) >= 0 and box.currentData() != held:
                # an element chosen, or a position changed in Excel: a grade that follows takes the position's
                box.setCurrentIndex(box.findData(held))
            for i in range(box.count()):
                box.setItemText(i, box.itemData(i))
            if following and held and box.currentData() == held:
                box.setItemText(box.currentIndex(), cards.followed(held, pid))
            box.blockSignals(False)
            if pid and pid not in positions:
                note = self.t("cn_no_position", pid=pid)
            elif pid and widgets.get("overridden"):
                note, back = self.t("cn_overridden", pid=pid, value=held or "—"), True
            widgets["grade_note"].setText(note)
            widgets["grade_note"].setStyleSheet("color: %s;" % theme.colour("override"))
            widgets["grade_back"].setVisible(back)
            widgets["form"].setRowVisible(widgets["note_row"], bool(note))

        stated = self.moisture_box.currentData()
        named = [self.element_position(w["element"].currentData() or "") for w in self.member_fields]
        named = [pid for pid in named if pid in positions]
        held = [positions[pid].get("moisture_class") for pid in named]
        held = [h for h in held if h is not None]
        where = ", ".join(sorted(set(named))) or "—"
        value = str(max(held)) if held else "—"
        self.moisture_box.blockSignals(True)
        self.moisture_box.setItemText(0, cards.followed(value, where) if held else "—")
        self.moisture_box.blockSignals(False)
        overridden = stated is not None and bool(held)
        self.moisture_note.setText(self.t("cn_overridden", pid=where, value=value) if overridden else "")
        self.moisture_note.setStyleSheet("color: %s;" % theme.colour("override"))
        self.moisture_back.setVisible(stated is not None and bool(named))
        self.moisture_form.setRowVisible(self.moisture_line, overridden or (stated is not None and bool(named)))
        self.fill_member_values(positions)

    def fill_member_values(self, positions=None):
        """Each member's material and characteristic density, whether or not the calculation runs: both depend on the member's position and grade alone, so a connector that cannot be calculated yet -- no marker ticked -- still shows what its timber is.

        - **Essence**: the position's `material` column of Positionen.xlsx (Fichte), through the member's element; «—» where the element names no position.
        - **ρ_k**: SIA 265 Tabelle 8 or 9 for the grade in the field (calc/norms/sia265-2021-tab08-vollholz.json, sia265-2021-tab09-brettschichtholz.json) -- the 5 % fractile, the one density the calculation reads.
        """
        positions = positions if positions is not None else connector.known_positions(project.current().data_dir)
        for index, widgets in enumerate(getattr(self, "member_fields", [])):
            pid = self.element_position(widgets["element"].currentData() or "")
            grade = widgets["grade"].currentData() or ""
            material = ((positions.get(pid) or {}).get("material") or "").strip()
            try:
                row = sia265.grade(grade)
            except Exception:  # broad: a grade the norm tables do not carry shows no value rather than breaking the form
                row = None
            for name, text in (("species_%d" % (index + 1), material or "—"),
                               ("rho_k_%d" % (index + 1), _n(row["rho_k"]) if row else "—")):
                view = self.computed.get(name)
                if view is not None:
                    view.setText(text)

    def take_back_moisture(self):
        """«Reprendre» on the moisture class: it follows the members' positions again, the worst of them governing."""
        index = self.moisture_box.findData(None)
        if index >= 0:
            self.moisture_box.setCurrentIndex(index)
        self.fill_material_notes()

    def fill_links(self, timber):
        """Each number's link, as the source states it -- the connector's own and each timber member's --, shown against the export's values read once (spec 2026-10-11-variables-liees-champs-et-textes, UI-002)."""
        if not self.link_fields:
            return
        values = linkable_spin.current_values()
        for (where, key), wrapper in self.link_fields.items():
            owner = self.source if where == "self" else (timber[where] if where < len(timber) else {})
            wrapper.set_link(links.links_of(owner).get(key), values)

    def draft_links(self, s, members, timber_indices):
        """The form's links into the draft: on the connector itself or on the member a slot is; a field the draft does not hold takes none (`links.drop_unheld`), and the schema_version says whether any is left (connector.stamp_version)."""
        for (where, key), wrapper in getattr(self, "link_fields", {}).items():
            if where == "self":
                owner = s
            elif where < len(timber_indices):
                owner = members[timber_indices[where]]
            else:
                continue
            found = dict(links.links_of(owner))
            link = wrapper.link()
            if link is None:
                found.pop(key, None)
            else:
                found[key] = link
            if found:
                owner[links.LINKS] = found
            else:
                owner.pop(links.LINKS, None)
        links.drop_unheld(s, connector.LINKABLE)
        connector.stamp_version(s)

    def draft(self):
        """The source as the form has it."""
        s = copy.deepcopy(self.source)
        s["schema_version"] = connector.SOURCE_SCHEMA_VERSION
        # the folder (`group`), the variant and the length stay what the source holds: none is a field any more
        s["name"], description, s["id"] = self.identity.values()
        s["description"] = description.strip()
        s["label"] = ""     # one field: what was the designation is the description now
        s["assembly"] = self.assembly_box.currentData() or self.assembly_box.currentText()
        s["diameter"] = {"value": self.diameter_box.value(), "unit": "mm"}
        # a plate grade only where there is a plate: a Holz-Holz joint saves none, whatever the hidden combo holds
        steel_joint = dowel.ASSEMBLIES.get(s["assembly"], {}).get("family") == "steel-timber"
        s["steel"] = (self.steel_box.currentData() or "") if steel_joint else ""
        s["moisture_class"] = self.moisture_box.currentData()
        if connector.TYPE_BLOCK.get(s.get("type")) == "dowel":
            # the dowel's grade fills f_u,k and is saved beside it, "" where the value is typed (D-06, D-20)
            s["dowel"] = {"steel": self.dowel_steel_box.currentData() or "", "f_u_k": {"value": self.f_u_k_box.value(), "unit": "N/mm²"}}
        s["conditions"] = {"seismic": self.seismic_box.isChecked(), "truss": self.truss_box.isChecked()}
        # the plate's bearing (D-14): a block only on a Stahl-Holz joint where one of its lengths is stated, a length of 0 being one not stated
        stated = {key: box.value() for key, box in self.plate_boxes.items()} if steel_joint else {}
        if any(stated.values()):
            s["plate"] = {key: ({"value": value, "unit": "mm"} if value > 0 else None) for key, value in stated.items()}
        else:
            s.pop("plate", None)

        s["schema"] = self.schema_box.currentData() or ""
        s["fasteners"] = self.ticked_markers()
        override = self.n_tot_override.isChecked()
        s["n_tot"] = {"value": self.n_tot_box.value() if override else max(1, len(s["fasteners"])),
                      "override": override}

        spec = dowel.ASSEMBLIES.get(s["assembly"], {"family": "timber-timber", "members": 2})
        plates = None
        if spec["family"] == "steel-timber" and self.plate_fields:
            plates = {
                "arrangement": "laschen" if s["assembly"] == "Stahl-Holz, Bleche aussen" else "schlitzblech",
                "count": self.plate_fields["count"].value(),
                "slot": {"value": self.plate_fields["slot"].value(), "unit": "mm"},
                "ratio": self.plate_fields["ratio"].value(),
            }
        members = s.get("members") or [connector._new_member(), connector._new_member()]
        timber_indices = [i for i, m in enumerate(members) if m.get("role") == "timber"]
        for slot, widgets in enumerate(getattr(self, "member_fields", [])):
            if slot >= len(timber_indices):
                break
            member = members[timber_indices[slot]]
            eid = widgets["element"].currentData() or ""
            member["element"] = eid
            pid = self.element_position(eid)
            grade = widgets["grade"].currentData() or ""
            # null FOLLOWS the element's position; a grade OVERRIDES it and stays overridden through the
            # next import. There is no third shape since schema 2.0: the element is the position reference,
            # so naming one here as well would be a second place for the same fact.
            member["material"] = None if (pid and not widgets.get("overridden")) else {"grade": grade}
            member["predrilled"] = widgets["predrilled"].isChecked()
            member["alpha"] = widgets["alpha"].value()
            thickness = (self.plate_fields["b"].value()
                         if (self.plate_fields and slot == 0) else widgets["t"].value())
            member["t"] = {"value": thickness, "unit": "mm"}
            member["n"] = widgets["n"].value()
            spacing = widgets["a_1"].value()
            member["a_1"] = {"value": spacing, "unit": "mm"} if spacing else None
            member["plates"] = plates if slot == 0 else None
        s["members"] = members
        self.draft_links(s, members, timber_indices)
        # The members joined, read off the schema -- the positions of the elements the members are -- so the report's «(Bauteile: T001, S001)» is never typed; it is refreshed on every save, not read again at export (periodic audit 260916).
        joined = [self.element_position(m.get("element", "")) for m in members if m.get("role") == "timber"]
        s["elements"] = list(dict.fromkeys(pid for pid in joined if pid))
        return s

    def refresh(self):
        source = self.draft()
        warnings = []
        try:
            self.section_svg.load(QByteArray(connector_svg.section_of(
                source, note=self.section_note(), highlight=getattr(self, "hover_member", None)).encode("utf-8")))
            self.pattern_svg.load(QByteArray(connector_svg.pattern_of(
                source, self.detail(), lang=self.app.lang, highlight=self.marked(),
                positions=connector.known_positions(project.current().data_dir)).encode("utf-8")))
            for widget in (self.section_svg, self.pattern_svg):
                widget.renderer().setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)
        except Exception as exc:  # broad: a drawing that fails must not empty the form
            warnings.append(str(exc))

        self.record, self.reason = None, ""
        self.preview_values = {}
        try:
            connector.check_source(source, "%s.json" % source["id"])
            record, _prefixed = connector.build_record(source, connector.known_positions(project.current().data_dir), self.detail())
            # the record's own list, without the file name in front of each sentence: prefixed, no template of the glossary matches and the window printed them in German (periodic audit 260916)
            warnings.extend(record["warnings"])
            if record["calculated"]:
                self.record = record
            else:
                self.reason = self.t("cn_no_calc", reason=self.tl(record["reason"]))
        except validation.ValidationError as exc:
            self.reason = self.t("cn_invalid", error=str(exc))
        if self.record is None:
            # p (1 einschnittig, 2 zweischnittig) and k_beta depend on no marker: shown before the pattern exists
            self.preview_values = connector.preview(source, connector.known_positions(project.current().data_dir), self.detail())

        self.fill_computed()
        self.fill_member_values()
        self.fill_results()
        # The warnings in the window's own language, through the very glossary the report reads: the
        # sentences are composed in German by connector.py, which knows no language (section 4bis).
        # rich text, so a symbol a warning carries between dollars ($n_"tot"$) reads as the report prints it
        self.message.setText("<br>".join(_prose_html(self.tl(w)) for w in warnings))
        self.message.setVisible(bool(warnings))
        self.fill_commands(source["id"])
        self.update_list_marker()

    def fill_computed(self):
        """The cells the calculation fills -- the formula cells of the classeur, read and never typed into."""
        variables = (self.record or {}).get("vars", {})
        preview = getattr(self, "preview_values", None) or {}
        for name, view in self.computed.items():
            entry = variables.get(name)
            if entry is None:
                # the pieces no marker enters (p, k_beta, p·k_beta, M_u,k), while the connector is not calculated
                view.setText(_n(preview[name]) if preview.get(name) is not None else "—")
                continue
            if isinstance(entry.get("value"), str):
                view.setText(self.tl(entry["value"]))
            else:
                # the number alone: every row sets its unit in a column of its own, and «350 kg/m³ kg/m³» said it twice
                view.setText(_n(entry["value"]))

    def fill_results(self):
        """The numbers, in rich text so a subscript is a subscript, then the minimum spacings of Tabelle 24."""
        if self.record is None:
            self.results.setText(_prose_html(self.reason or self.t("cn_uncalculated")))
            return
        variables = self.record["vars"]
        lit = set(self.box_results.get(self.hot_box, ())) if self.hot_box else set()
        rows = []
        for name in self.RESULT_ORDER:
            if name is None:
                rows.append('<tr><td colspan="3" style="height:6px"></td></tr>')
                continue
            entry = variables.get(name)
            if entry is None:
                continue
            value = ("%s %s" % (_n(entry["value"]), entry.get("unit") or "")).strip()
            # ⚠️ The ink is set with the ground and never left to the palette (the engineer, v0.84:
            # «orange clair sur blanc ne se lit pas bien»): a light ground under the palette's own text
            # is unreadable in a dark theme, where that text is near-white, and barely there in a light
            # one. Lighting a row must make it easier to read, not harder.
            style = (' style="background:%s; color:%s"' % (theme.colour("lit"), theme.colour("lit-ink"))) if name in lit else ""
            weight = " font-weight:bold;" if name in self.ANSWERS else ""
            rows.append(
                '<tr%s><td style="padding-right:10px;%s">%s</td>'
                '<td style="padding-right:6px">=</td>'
                '<td align="right" style="%s">%s</td></tr>'
                % (style, weight, self.RESULT_NAMES.get(name, name), weight, _escape_html(value)))
        html = '<table cellspacing="0">%s</table>' % "".join(rows)
        html += self.record_table("Minimale Abstände", "cn_min_spacings")
        self.results.setText(html)

    def record_table(self, title, heading):
        """A table the export builds, under the numbers -- «Minimale Abstände» and «Verschiebungsmodul», laid out as the report lays them out (v0.77): the group line over its columns, each unit under its name, the totals bold under a rule, and a symbol written between dollars set with its subscript.

        The minimum spacings were in the report and nowhere on screen until v0.70, which is the wrong way round: equation (88) is conditional on them (6.2.1.1), so they belong beside the resistance they qualify. The Verschiebungsmodul joined them in v0.77, the engineer asking for the report's table here too.
        """
        table = next((t for t in (self.record or {}).get("tables", []) if t.get("title") == title), None)
        if table is None:
            return ""
        variables = self.record.get("vars", {})
        results = set(self.record.get("results", []))
        columns = table.get("columns", [])
        pad = "padding:1px 10px 1px 0"
        # A column is aligned by what it holds, exactly as the report aligns it (lib/calc-engine.typ, column-align): a number read from the right so the digits line up, a symbol centred, a word from the left.
        def aligned(kind):
            return "right" if kind in ("number", "value") else "center" if kind == "math" else "left"
        lines = []
        if any("group" in c for c in columns):
            cells, i = [], 0
            while i < len(columns):
                group = columns[i].get("group")
                span = 1
                while group is not None and i + span < len(columns) and columns[i + span].get("group") == group:
                    span += 1
                text = "" if group is None else _prose_html(self.tl(group))
                # the rule under a group's name, spanning what that name covers, as the report draws it
                style = pad if group is None else pad + ";border-bottom:1px solid"
                cells.append('<th colspan="%d" align="%s" style="%s">%s</th>' % (span, "left" if group is None else "center", style, text))
                i += span
            lines.append("<tr>%s</tr>" % "".join(cells))
        head = []
        for column in columns:
            name = _math_html(column["label_math"]) if column.get("label_math") else _prose_html(self.tl(column.get("label", "")))
            unit = column.get("unit") or ""
            if unit:
                name = "[%s]" % _escape_html(unit) if not name else "%s [%s]" % (name, _escape_html(unit))
            head.append('<th align="%s" style="%s">%s</th>' % (aligned(column.get("kind")), pad, name))
        lines.append("<tr>%s</tr>" % "".join(head))

        def cell(value, column, bold, rule=False):
            kind = column.get("kind")
            if kind == "value" and isinstance(value, str) and value:
                entry = variables.get(value) or {}
                text = _n(entry["value"]) if isinstance(entry.get("value"), (int, float)) else _escape_html(value)
                bold = bold or value in results
            elif kind == "math" and isinstance(value, str) and value:
                text = _math_html(value)
            elif isinstance(value, str):
                text = _prose_html(self.tl(value))
            else:
                text = _n(value)
            style = pad + (";font-weight:bold" if bold else "") + (";border-top:1px solid" if rule else "")
            return '<td align="%s" style="%s">%s</td>' % (aligned(kind), style, text)

        # The rules are the report's three: under the headings, above the totals, and nothing else -- a panel needs no rule to close it, the box around it already doing that. The rule is set on the cells rather than on the row: Qt's rich text honours a border on a cell and not on a `tr`.
        for i, row in enumerate(table.get("rows", [])):
            lines.append("<tr>%s</tr>" % "".join(cell(v, c, False, rule=i == 0) for v, c in zip(row, columns)))
        for row in table.get("totals", []):
            lines.append("<tr>%s</tr>" % "".join(cell(v, c, True, rule=True) for v, c in zip(row, columns)))
        return ('<p style="margin-top:10px"><b>%s</b></p><table cellspacing="0">%s</table>'
                % (_escape_html(self.t(heading)), "".join(lines)))

    def fill_commands(self, cid):
        """The «Affichage» view told the connector as it stands (display_view.DisplayTab): the calls to copy left the right pane in v0.117."""
        self.update_display()

    def display_entries(self):
        """What can show the connector open (spec 2026-10-21-commandes-typst-refonte, UI-002): its file written out by the export -- its line, its figures, its resistance -- included where a section prints it, one of its values read by `#var`, and the loop over every connector."""
        cid = self.draft()["id"] or "?"
        here = project.current()
        banner = display_view.saved_state(self.t, cid, self.t("ds_save_first"), self.current_id is None or self.dirty,
                                          here.data_dir / "connectors.json", "connectors", here.connectors_dir / f"{cid}.json")
        return [
            display_view.Entry("file", "domain-file", call=ref.call_include_domain(connector.DOMAIN, cid), banner=banner),
            display_view.Entry("var", "var", call=ref.call_var_domain(connector.DOMAIN, cid, "R_d"), banner=banner),
            self.loop_entry("domain-file", ref.call_domain_loop(connector.DOMAIN)),
        ]

    def tick_all(self):
        self._tick_every(True)

    def tick_none(self):
        self._tick_every(False)

    def _tick_every(self, on):
        self.loading = True
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item is not None:
                item.setCheckState(Qt.CheckState.Checked if on else Qt.CheckState.Unchecked)
        self.loading = False
        self.sync_n_tot()
        self.touch()
        self.refresh()

    def derive_rows(self):
        """n and a_1 for every member, read off the drawing -- a suggestion the engineer may overwrite, because which fasteners count as «hintereinander» is a judgement (dowel.pattern_rows).

        The pattern is the schema's: the markers ticked, at the places the schema puts them, and the grain
        direction is the member's element's rather than a member `angle` that no longer exists.
        """
        source = self.draft()
        detail = self.detail()
        points = [{"x": x, "z": z} for x, z in connector.marker_points(source, detail)]
        if not points:
            return
        timber = [m for m in source["members"] if m.get("role") == "timber"]
        for widgets, member in zip(getattr(self, "member_fields", []), timber):
            n, a_1 = dowel.pattern_rows(points, self.element_angle(member.get("element", ""), detail))
            widgets["n"].setValue(n)
            widgets["a_1"].setValue(a_1 or 0)
        self.touch()
