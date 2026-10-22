"""Woodcore's «Connecteurs» tab: where a connector is defined and its shear resistance calculated (docs/domain/connectors.md §3.3nonies, docs/ui/window.md §10quater).

The tab lives in its own module rather than in `woodcore_gui.py`, which lists it in its `TABS` and merges the `STRINGS` below into its own -- the arrangement `plan_tab`, `statics_tab` and `commands_tab` already use. Its keys carry a `cn_` prefix of their own: a key defined in two of these modules would be silently taken by whichever merged last, which `_check_strings` cannot see.

Three panes. **Left**, the connectors of the project, and *Nouveau · Dupliquer · Supprimer*. **Middle**, at the top a bar of the kinds of fastener, drawn with the very symbols the figures draw (`connector_svg.SWATCHES`); choosing one folds the bar away, which is what gives the form below it the room. Only *Broche* is live -- every other kind is there, disabled, saying in its tooltip which calculation is still missing, the v0.47 rule that a tool which draws nothing says so. Under the bar the form: the assembly, the diameter, and per member the timber, the thickness, the angle and the fastener row. **Right**, the two figures, the results, the warnings in yellow -- never a pop-up -- the calls to copy, and *Annuler les modifications · Enregistrer*.

Nothing here computes: `domains/dowel.py` does, and the preview calls the very functions the export runs, so the numbers on screen are the numbers in the report.
"""

import copy
import json
import math
from pathlib import Path

from PySide6.QtCore import QByteArray, QEvent, Qt, QTimer
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import (
    QAbstractItemView, QAbstractSpinBox, QApplication, QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout, QGroupBox,
    QHBoxLayout, QLabel, QMessageBox, QPushButton,
    QSizePolicy, QSpinBox, QSplitter, QTableWidget, QTableWidgetItem, QToolButton,
    QVBoxLayout, QWidget,
)

import build_reference as ref
import grouped_list
import source_archive  # «Supprimer» archives (source_archive.py)
import identity
import project  # where the project this tab works on is (calc/project.py)
import theme  # the colours this tab states itself: the orange of a value written over, a lit result (theme.py, v0.90)
import richtext  # symbols as mathematics, the calls coloured as the site's code, «✓» once copied (richtext.py, v0.92)
import cards  # the form and what is read off it in cards, after the website (cards.py)
import display_view  # the «Affichage» view: the command, its options, the call and the page (display_view.py, v0.117)
import shown_variables  # the variables -1 «Sélection manuelle» offers: the connector's own, read off the export (issue #20)
import views  # the views the top bar's switch chooses between (views.py, v0.117)
import autosave  # saving without a question, and what is never saved without the engineer (autosave.py, v0.117)
import validation
import notices_ui  # what a tab says without a message box: a schema left out because it does not read (notices_ui.py)
from shiboken6 import isValid
import engine
from domains import connector, connector_svg, dowel
from domains import schema as schema_model
from i18n import strings
from norms import sia263, sia265, sn_en_14592
from connectors_tab_words import STRINGS, _check_strings  # split out of this module (issue #30): every name it had is still importable from it
from connectors_tab_form import COLUMN_LABEL_WIDTH, ICON_PX, LABEL_WIDTH, SYMBOL_WIDTH, TOOL_HEIGHT, TOOL_MIN_WIDTH, TOOL_TYPES, UNIT_WIDTH, _n, svg_icon, ConnectorsFormMixin  # split out of this module (issue #30): every name it had is still importable from it
from connectors_tab_draft import _escape_html, _math_html, _prose_html, ConnectorsDraftMixin  # split out of this module (issue #30): every name it had is still importable from it

# Every path is the current project's, asked of project.current() when it is needed (v0.81, docs/architecture/layout.md §11): the connectors' sources are its `connectors_dir`, and the detail schemas a connector is drawn on (section 3.3decies) its `details_dir` -- read from the sources, as the export reads them, so that a schema saved in the «Schémas» tab is there the moment this tab is looked at again.
# the row of a connector nobody has saved yet, as every other editor tab lists its draft (periodic audit 260916, AUD-5-8)
from source_editor import NEW_ROW, SourceEditorTab, next_free_id as _next_id  # the left pane every editor tab shares (spec 2026-10-19-base-saine-nettoyage, ARCH-001)


# The box under the pointer, and the results it produces, are lit together (the engineer's request).
# ONE style sheet for every box of the form, lit or not, so that lighting a box changes the colour of its frame and nothing else -- the window's own since v0.90 (theme.py's STYLE, `QGroupBox[hot="true"]`), where it was this tab's until then. Before v0.77 a lit box took a style sheet and an unlit one the platform's native frame -- two frames laid out differently (the title, the margin, the corner), so a box jumped the moment the pointer entered it; and a selector reaching every QGroupBox INSIDE the lit one is why «Pièce 2» lit with «Pièce 1».
# A box is lit through its own `hot` property, and a flat box (the untitled member of a Stahl-Holz joint) keeps a frame of no colour until it is.
# A value taken from a position and written over says so in the orange the engineer asked for -- theme.colour("override"), the report's own in the light scheme (tests/test_constants.py). A result lit by the box that produces it takes the ground AND the ink, theme.colour("lit") and ("lit-ink"), so that the row reads in a light scheme and a dark one alike (v0.84): #fff3cd under the palette's text was all but invisible in either.


_check_strings()


# The id a name composes -- the rule of every tab of the window now (identity.py), kept importable from here.
slug_id = identity.slug_id


def next_free_id(taken, symbol="SD"):
    """The first free id of a connector: its fastener's symbol, then two digits (SD_01)."""
    return _next_id(taken, symbol + "_")


class ConnectorsTab(ConnectorsDraftMixin, ConnectorsFormMixin, SourceEditorTab, display_view.DisplayTab, QWidget):
    GRAPH_KIND = "connector"   # issue #71
    SYNC_DOMAIN = True   # its sources are domains with a file of their own: every writer is followed by domain_file.sync (tab_guard.py, spec 2026-10-19-base-saine-nettoyage)
    VIEWS = views.CALC_VIEWS   # «Calcul» and «Affichage» (views.py, v0.117)
    KEY = "tab_connections"
    LIST_KEY, EMPTY_KEY, WORDS = "cn_list", "cn_empty", "cn"
    DOMAIN = connector

    def sources_dir(self):
        return project.current().connectors_dir

    def saved_ids(self):
        return self._taken()

    DUPLICATE_FORGETS = ()   # a copy keeps its name: a connector is told apart by its id

    def make_source(self):
        """A new connector, **drawn on the first schema there is** and carrying all of its markers. v0.70's rule -- «Nouveau» must open on something that calculates rather than on a refusal --: with no schema named and no marker ticked, a fresh connector has no pattern. Where the project has no schema at all it still opens empty, which is honest: the detail is drawn first, in the «Schémas» tab, and then calculated."""
        return connector.new_source(next_free_id(self._taken()), schema=self.first_schema())

    def after_new(self):
        self.adopt_schema()
        self.expand_types()

    def duplicate_id(self, source):
        return next_free_id(self._taken(), connector.TYPES.get(source.get("type"), "SD"))

    def fail_title(self):
        return self.t("cn_save")

    def export_sources(self):
        connector.export(project.current().connectors_dir, project.current().data_dir)

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.t = app.t
        self.loading = False
        self.dirty = False
        self.current_id = None
        self.source = connector.new_source(next_free_id(self._taken()))
        self.collapsed = False
        self.empty_folders = list(app.folder_settings(self.KEY))   # folders holding nothing: a view preference, kept in settings.json by the window (grouped_list.py, v0.75)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.addWidget(self.build_list())
        self.splitter.addWidget(self.build_form())
        self.splitter.addWidget(self.build_preview())
        self.install_display(self.KEY)   # «Affichage»: the connector's commands, their options, the call and the page (v0.117)
        for index, stretch in enumerate((2, 5, 4)):
            self.splitter.setStretchFactor(index, stretch)
        layout.addWidget(self.splitter, 1)

        self.refresh_timer = QTimer(self)
        self.refresh_timer.setSingleShot(True)
        self.refresh_timer.setInterval(120)
        self.refresh_timer.timeout.connect(self.refresh)

        self.install_save_shortcut()
        self.restore(app.views.get(self.KEY))

    # --- small helpers ---------------------------------------------------------

    def note(self, text):
        label = QLabel(text)
        label.setWordWrap(True)
        label.setStyleSheet("color: %s;" % self.app.muted)
        return label

    def code_field(self, text):
        return richtext.CodeField(text, self.app.mono_font)   # the call as the site sets a code block, coloured (v0.92)

    def copy_button(self, text):
        # «⧉», then «✓» a moment once copied: the tab's narrow button says it the way the others say «Copié ✓» (v0.92)
        button = richtext.copy_button("⧉", "✓", lambda: self.app.copy(text))
        button.setFixedWidth(30)
        button.setProperty("compact", True)  # a symbol in a 30 px button: the style sheet's side padding would leave it no room (theme.py)
        return button

    def touch(self):
        if self.loading:
            return
        self.dirty = True
        self.update_list_marker()
        self.refresh_timer.start()

    def _taken(self):
        return [p.stem for p in connector.source_paths(project.current().connectors_dir)]

    # --- left: the connectors --------------------------------------------------

    # --- middle: the type bar and the form -------------------------------------


    # --- the shape of one row, and the read-only cells ------------------------------


    # --- the two boxes that depend on the assembly ----------------------------------


    # --- right: the figures, the results and the calls --------------------------


    # --- the draft <-> the form --------------------------------------------------


    # --- the live preview --------------------------------------------------------

    # What each result is called on screen, as rich text: a real subscript, because `R_d` written flat is
    # not what the norm calls it and not what the report prints (the engineer's own point).
    RESULT_NAMES = {
        "f_h_1": "f<sub>h,α,k,1</sub>", "f_h_2": "f<sub>h,α,k,2</sub>",
        "t_1": "t<sub>1</sub>", "t_2": "t<sub>2</sub>",
        "M_u_k": "M<sub>u,k</sub>", "k_beta": "k<sub>β</sub>", "k_beta_2": "k<sub>β,2</sub>",
        "p": "p", "p_k_beta": "p·k<sub>β</sub>", "k_red": "k<sub>red</sub>",
        "n_tot": "n<sub>tot</sub>", "n_quer_1": "n<sub>quer,1</sub>", "n_quer_2": "n<sub>quer,2</sub>",
        "eta_w": "η<sub>w</sub>", "eta_t": "η<sub>t</sub>",
        "R_d_Verb": "R<sub>d,Verb</sub>", "R_d": "R<sub>d</sub>",
        "R_d_Fachwerk": "R<sub>d,Fachwerk</sub>", "R_d_Verb_Fachwerk": "R<sub>d,Verb,Fachwerk</sub>",
        "K_ser": "K<sub>ser</sub>", "K_ser_Verb": "K<sub>ser,Verb</sub>",
    }
    # What is printed, in the classeur's own order: the pieces of equation (88), then the answers.
    RESULT_ORDER = ("f_h_1", "f_h_2", "M_u_k", "k_beta", "k_beta_2", "p", "p_k_beta", "k_red",
                    "eta_w", "eta_t", None, "R_d", "R_d_Verb", "R_d_Fachwerk", "R_d_Verb_Fachwerk",
                    None, "K_ser", "K_ser_Verb")
    # The answers the whole form produces: they belong to no box, being the product of all of them.
    # R_d comes first since v0.84 -- one fastener before the connection, the order the report prints.
    ANSWERS = ("R_d", "R_d_Verb", "R_d_Fachwerk", "R_d_Verb_Fachwerk")


    # --- the table's buttons -------------------------------------------------------


    # --- the schema this connector is drawn on ---------------------------------------

    def schemas(self):
        """{id: source} of every detail schema, read afresh off details/ -- so a schema saved in the «Schémas» tab is offered here the moment this tab is looked at again, without either tab knowing about the other.

        A schema that does not check is left out rather than raising, and said in a warning notice naming the file and why (issue #28): this tab must stay usable while another is being edited.
        """
        out, problems = schema_model.readable_sources(project.current().details_dir)
        notices_ui.tell_unreadable_schemas(problems)   # one that does not read is left out and said, never skipped without a word (issue #28)
        return out

    def first_schema(self):
        """The schema a new connector starts on: the first in file-name order, and "" where there is none."""
        keys = sorted(self.schemas())
        return keys[0] if keys else ""

    def detail(self):
        """The schema in force, or None."""
        return self.schemas().get(self.schema_box.currentData() or "")

    def element_position(self, eid):
        """The position the named element of the schema in force carries, or ""."""
        element = schema_model.entry_of(self.detail() or {}, "elements", eid) if eid else None
        return (element or {}).get("position", "") or ""

    def element_angle(self, eid, detail=None):
        """That element's grain direction, in degrees from the schema's x; 0 where it cannot be found."""
        where = detail if detail is not None else (self.detail() or {})
        element = schema_model.entry_of(where, "elements", eid) if eid else None
        direction = schema_model.element_direction(element) if element else None
        return 0.0 if direction is None else math.degrees(math.atan2(direction[1], direction[0]))

    def fill_schemas(self):
        """The schema combo, and the line under it saying what the schema in force holds."""
        self.loading = True
        wanted = self.source.get("schema", "")
        self.schema_box.clear()
        self.schema_box.addItem("—", "")
        for sid, detail in sorted(self.schemas().items()):
            label = detail.get("label", "")
            self.schema_box.addItem("%s — %s" % (sid, label) if label else sid, sid)
        at = self.schema_box.findData(wanted)
        held = self.schemas().get(wanted)
        if at < 0 and wanted:
            # A schema the folder no longer holds is kept and marked, as an unresolved position is.
            self.schema_box.addItem("%s (?)" % wanted, wanted)
            at = self.schema_box.count() - 1
        self.schema_box.setCurrentIndex(at if at >= 0 else 0)
        if not wanted:
            self.schema_note.setText(self.t("cn_no_schema"))
            self.schema_note.setStyleSheet("color: %s;" % theme.colour("override"))
        elif held is None:
            self.schema_note.setText(self.t("cn_schema_gone", sid=wanted))
            self.schema_note.setStyleSheet("color: %s;" % theme.colour("override"))
        else:
            places = schema_model.fastener_places(held)
            markers = len(held.get("connectors", []))
            self.schema_note.setText(self.t("cn_schema_holds",
                                            n=len(held.get("elements", [])),
                                            m=markers, p=len(places) - markers))
            self.schema_note.setStyleSheet("color: %s;" % self.app.muted)
        self.loading = False

    def fill_elements(self):
        """Each member's element combo, from the schema in force."""
        detail = self.detail()
        for widgets in self.member_fields:
            box = widgets["element"]
            box.blockSignals(True)
            box.clear()
            box.addItem("—", "")
            for element in (detail or {}).get("elements", []):
                pid = element.get("position", "")
                label = element.get("label", "")
                text = " — ".join(p for p in (element["id"], pid or label) if p)
                box.addItem(text, element["id"])
            box.blockSignals(False)

    def fill_markers(self):
        """«Disposition des broches»: every connector marker of the schema **and every point ticked «connecteur»** (schema.fastener_places, v0.77 -- a point is taken by every module, not by «Moments polaires» alone), with a tick against the ones this connector carries and its place beside it, read only. A point says what it is in its tooltip, as in «Moments polaires»."""
        self.loading = True
        detail = self.detail()
        ticked = list(self.source.get("fasteners", []))
        places = schema_model.fastener_places(detail)
        kinds = {m["id"]: m.get("kind", "") for m in (detail or {}).get("connectors", [])}
        self.table.setRowCount(0)
        # A schema with nothing to take at all is the one case the list cannot explain by itself: say where a marker is placed and where a point is ticked.
        if detail is not None and not places:
            self.markers_note.setText(self.t("cn_no_markers", sid=detail.get("id", "")))
        self.markers_note.setVisible(detail is not None and not places)
        # A fastener the schema has lost is still listed, ticked and marked, so that it can be seen and
        # untangled rather than vanishing with the number it carried.
        rows = [(fid, kinds.get(fid), x, z, True) for fid, (x, z) in places.items()]
        rows += [(mid, None, None, None, False) for mid in ticked if mid not in places]
        for mid, kind, x, z, present in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)
            tick = QTableWidgetItem("")
            tick.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled
                          | Qt.ItemFlag.ItemIsSelectable)
            tick.setCheckState(Qt.CheckState.Checked if mid in ticked else Qt.CheckState.Unchecked)
            tick.setData(Qt.ItemDataRole.UserRole, mid)
            self.table.setItem(row, 0, tick)
            name = QTableWidgetItem(mid if present else "%s (?)" % mid)
            if present:
                # a marker says its kind of fastener, a point that it is a point
                name.setToolTip(self.t("cn_kind_point") if kind is None
                                else "%s — %s" % (self.t("cn_kind_marker"), self.tl(kind)) if kind else self.t("cn_kind_marker"))
            for column, item in ((1, name),
                                 (2, QTableWidgetItem("" if x is None else str(x))),
                                 (3, QTableWidgetItem("" if z is None else str(z)))):
                item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                self.table.setItem(row, column, item)
        self.loading = False
        self.sync_n_tot()

    def sync_n_tot(self, _checked=None):
        """«Broches» takes its count from «Disposition des broches» (the engineer, v0.84).

        `draft()` has read n_tot off the ticked markers since v0.74, but the spin box showed whatever was
        loaded, so the form said one thing and the calculation used another. It now shows the count and
        is **read-only while it follows** -- a field one may type into and that is then ignored is worse
        than a field one may not. «Écraser le compte du dessin» is what frees it, which is the one way
        the two ever differ.

        ⚠️ Nothing to set while «Broches» does not stand yet. `fill_form` fills the markers **before**
        `fill_members` builds that box -- the elements and the markers are read off the schema first --
        and `fill_markers` ends here. A tab just built had the box only by accident: loading a connector
        whose assembly is not the one the list opens on changes the list, which runs `on_assembly`, which
        builds it. One carrying that very assembly -- «Holz-Holz einschnittig», the first -- changed
        nothing, and Woodcore did not start (Gian's project, 2026-10-06). `fill_members` syncs again at
        its own end, so the count is set as soon as there is a field to set it in.
        """
        if not hasattr(self, "n_tot_override"):
            return
        override = self.n_tot_override.isChecked()
        self.n_tot_box.setReadOnly(not override)
        self.n_tot_box.setButtonSymbols(
            QAbstractSpinBox.ButtonSymbols.UpDownArrows if override
            else QAbstractSpinBox.ButtonSymbols.NoButtons)
        if override:
            return
        drawn = max(1, len(self.ticked_markers()))
        if self.n_tot_box.value() != drawn:
            blocked = self.n_tot_box.blockSignals(True)
            self.n_tot_box.setValue(drawn)
            self.n_tot_box.blockSignals(blocked)

    def ticked_markers(self):
        """The marker ids ticked, in the table's own order."""
        out = []
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item is not None and item.checkState() == Qt.CheckState.Checked:
                out.append(item.data(Qt.ItemDataRole.UserRole))
        return out

    def marked(self):
        """What the drawing beside the form rings: the marker of the row selected, else the element of the member whose combo was last touched. A (collection, id) pair, which is `show-schema`'s own `highlight` -- so the window and the report mark the same thing."""
        hovered = getattr(self, "hover_marker", None)
        if hovered:
            return ("connectors", hovered)
        if getattr(self, "hover_element", ""):
            return ("elements", self.hover_element)
        rows = {i.row() for i in self.table.selectedIndexes()}
        if rows:
            item = self.table.item(sorted(rows)[0], 0)
            if item is not None:
                return ("connectors", item.data(Qt.ItemDataRole.UserRole))
        eid = getattr(self, "hot_element", "")
        return ("elements", eid) if eid else None

    def on_schema(self, _index=0):
        """A schema chosen: the elements and the markers are its, so both lists are rebuilt."""
        if self.loading:
            return
        self.source["schema"] = self.schema_box.currentData() or ""
        self.fill_elements()
        self.fill_markers()
        self.touch()
        self.fill_material_notes()
        self.refresh()

    def on_element(self, _index=0):
        """An element chosen: the grade follows its position again, unless it has been written over, and the piece is lit on the drawing."""
        if self.loading:
            return
        for widgets in self.member_fields:
            if widgets["element"] is self.sender():
                self.hot_element = widgets["element"].currentData() or ""
        self.touch()
        self.fill_material_notes()
        self.refresh()

    def on_marker_toggled(self, item):
        if self.loading or item.column() != 0:
            return
        self.sync_n_tot()
        self.touch()
        self.refresh()

    def on_marker_selected(self):
        if not self.loading:
            self.refresh()

    # --- new, duplicate, delete, save ------------------------------------------------

    def on_shown(self):
        """The tab brought to the front: the schemas are read again, so one renamed, redrawn or added in «Schémas» is offered here at once, and its markers and elements with it -- without «Recharger». The draft keeps what the form holds."""
        dirty = self.dirty
        self.source = self.draft()
        if not dirty and self.current_id:
            try:
                on_disk = json.loads((project.current().connectors_dir / ("%s.json" % self.current_id)).read_text(encoding="utf-8"))
                self.source["schema"] = on_disk.get("schema", self.source.get("schema", ""))
            except (OSError, ValueError, AttributeError):
                pass
        self.fill_form()
        self.dirty = dirty
        self.refresh()

    def schema_renamed(self, old, new):
        """A schema saved under a new id (schema_tab): the draft follows it, as the saved files already have."""
        source = self.draft()
        if source.get("schema") == old:
            dirty = self.dirty
            self.source = source | {"schema": new}
            self.fill_form()
            self.dirty = dirty
            self.refresh()

    def save(self):
        source = self.draft()
        cid = source["id"]
        if not connector.ID_PATTERN.match(cid or ""):
            return self.fail(self.t("cn_taken", id=cid))
        taken = {t.lower() for t in self._taken()} - ({self.current_id.lower()} if self.current_id else set())
        if cid.lower() in taken:
            return self.fail(self.t("cn_taken", id=cid))
        if self.current_id and self.current_id != cid:
            if not autosave.ask_rename(self, self.t("cn_rename_title"), self.t("cn_rename", old=self.current_id, new=cid)):
                return False
        try:
            connector.check_source(source, "%s.json" % cid)
        except validation.ValidationError as exc:
            return self.fail(str(exc))

        project.current().connectors_dir.mkdir(parents=True, exist_ok=True)
        if self.current_id and self.current_id != cid:
            (project.current().connectors_dir / ("%s.json" % self.current_id)).unlink(missing_ok=True)
        engine.write_json(project.current().connectors_dir / ("%s.json" % cid), source)
        self.source = source
        self.current_id = cid
        self.dirty = False
        self.export(self.t("cn_saved", id=cid))
        self.reload_list(select=cid)
        return True

    # --- state across a rebuild -------------------------------------------------------

    def view_state(self):
        return {
            "draft": copy.deepcopy(self.draft()) if hasattr(self, "id_edit") else None,
            "current_id": self.current_id,
            "dirty": self.dirty,
            "collapsed": self.collapsed,
            "splitter": self.splitter.sizes(),
            "empty_folders": list(self.empty_folders),
        }

    def restore(self, state):
        if not state:
            self.reload_list()
            if self.ids:
                self.list.select(self.ids[0])
                self.load(self.ids[0])
            else:
                self.fill_form()
                self.refresh()
            self.splitter.setSizes([2000, 5000, 4000])
            return
        self.source = state.get("draft") or self.source
        self.current_id = state.get("current_id")
        self.dirty = bool(state.get("dirty"))
        self.empty_folders = list(state.get("empty_folders") or [])
        self.reload_list(self.current_id)
        self.fill_form()
        if state.get("collapsed"):
            self.collapse_types()
        if state.get("splitter"):
            self.splitter.setSizes(state["splitter"])
        self.refresh()


