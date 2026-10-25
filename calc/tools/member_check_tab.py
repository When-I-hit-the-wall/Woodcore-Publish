# -*- coding: utf-8 -*-
"""The base of the member checks' tabs that are not on the type «Calcul» yet, and the placeholders of the navigation (docs/domain/member-checks.md §3.3undecies, docs/ui/tab-member-checks.md).

Since issue #112 (spec docs/requirements/completed/2026-10-24-verifications-elements-v3.md) «Traction», «Compression», «Flexion» and «Cisaillement» are tabs of calculation, check_tabs.py, the stability the last accordion of the compression and of the bending. What stays here is `MemberCheckTab` -- the list, the form in cards, the instant result, «Calcul» and «Affichage» -- which the «Résistance au feu» tab (fire_check_tab.py) and the steel tabs (steel_tab.py) are built on, the card of the buckling lengths the fire tab reads (`BucklingLengths`), and the placeholders of torsion and of the serviceability (`soon_tab`).

⚠️ **A value that follows its position says so in its own field** -- «C24 — T001» -- and **a value typed over it stays written over**: an orange line names what the position holds, with «Reprendre» beside it (the connectors' rule, v0.70).
"""

import copy
import json
import re

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDoubleSpinBox, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton,
    QSplitter, QVBoxLayout, QWidget,
)

import build_reference as ref
import cards  # the form and what is read off it in cards, after the website (cards.py)
import reserved_tab  # the one class of a tab to come (spec 2026-10-19-base-saine-nettoyage, ARCH-001)
from source_editor import SourceEditorTab  # the left pane every editor tab shares (spec 2026-10-19-base-saine-nettoyage, ARCH-001)
import autosave  # saving without a question, and what is never saved without the engineer (autosave.py, v0.117)
import grouped_list
import display_view  # the «Affichage» view: the options, the call and the compiled page (display_view.py, v0.117)
import identity  # Nom · Description · ID (identity.py)
import views  # the two views the top bar's switch chooses between (views.py, v0.117)
import project  # where the project this tab works on is (calc/project.py)
import richtext  # the call coloured as the site's code, «Copié ✓» once copied (richtext.py)
import source_archive  # «Supprimer» archives (source_archive.py)
import structure_preview  # the lines every snippet starts with: the project's conf, the engine, the language
import theme  # the orange of a value written over (theme.py)
import linkable_spin  # the button beside a field that may follow a variable (spec 2026-10-11-variables-liees-champs-et-textes)
import validation
from domains import connector, links, member_check
from i18n import strings
from norms import sia265
from plan_command_builder import CommandField  # the call, its text replaceable: it changes at every option
from member_check_tab_words import STRINGS, _check_strings  # split out of this module (issue #30): every name it had is still importable from it
from member_check_tab_form import KEEP, _n, _value_text, held_section, section_text, MemberCheckFormMixin  # split out of this module (issue #30): every name it had is still importable from it
from member_check_tab_actions import ID_PATTERN, NEW_ROW, next_free_id, MemberCheckActionsMixin  # split out of this module (issue #30): every name it had is still importable from it

OPTION_DELAY_MS = 150

# What the placeholders say: tab key -> (the key of what the module will hold, the commands of the report that do the work meanwhile). The keys are literals on purpose: tests/test_i18n.py finds a key by the code that names it.
SOON = {
    "tab_mc_torsion": ("mc_what_torsion", ("#verify-shear",)),
    "tab_sls_deformation": ("mc_what_deformation", ()),
    "tab_sls_vibration": ("mc_what_vibration", ()),
}


_check_strings()


def soon_tab(app, key):
    """A module of the navigation that is not built yet (reserved_tab.ReservedTab): it says so, what it will hold and which command of the report does the work meanwhile. «Flexion» is bending combined with a normal force and «Effort tranchant» holds the shear and the compression perpendicular to the grain -- said in the sentence each takes its words from."""
    what_key, commands = SOON[key]
    what = app.t(what_key)
    text = app.t("mc_soon", what=what, commands=", ".join(commands)) if commands else app.t("mc_soon_none", what=what)
    return reserved_tab.ReservedTab(app, key, app.t(key), app.t("mc_soon_title"), text)


class MemberCheckTab(MemberCheckActionsMixin, MemberCheckFormMixin, SourceEditorTab, display_view.DisplayTab, QWidget):
    """The tab of one kind of member check -- the list, the form in cards, the page, the options and the call; see the module's docstring. A kind is a subclass naming itself (`KEY`, `KIND`, `ID_PREFIX`, the keys of its title and of its empty list) and building its «Effort» card (`build_effort`) and the part of the source that card holds (`fill_effort`, `draft_effort`)."""
    SYNC_DOMAIN = True   # its sources are domains with a file of their own: every writer is followed by domain_file.sync (tab_guard.py, spec 2026-10-19-base-saine-nettoyage)

    KEY = ""            # the tab's key: its title, its entry of the window's views and of the empty folders
    KIND = ""           # the kind of the checks it lists: `kind` of their source
    GRAPH_KIND = "check"   # a timber check of the graph of dependencies (issue #71)
    UNFOLDED = True    # every kind is printed unfolded, its domain written out by the export (spec 2026-10-15, D-11; spec 2026-10-21-commandes-typst-refonte, REQ-017): its page is that domain's, its call an #include of its file, and «Ouvrir dans Formules» goes to it
    ID_PREFIX = "Z_"
    LIST_KEY = "mc_list"
    EMPTY_KEY = "mc_empty"
    WORDS = "mc"        # the prefix of its list's words (source_editor.SourceEditorTab)
    N_KEY = "mc_N"      # the label of the force
    ALPHA_KEY = "mc_alpha"   # the label of the angle
    N_MIN = 0.0         # the lowest force the field takes: a magnitude, but a bending's normal force is signed
    # The domain the tab writes and reads (spec 2026-10-12-section-acier ARCH-RISK-205): its source's folder, `new_source`, `read_source`, `check_source`, `stamp_version`, `export` -- member_check for the timber tabs, steel_check for the «Acier» ones, which override what else differs (the material and section cards, the result, the call).
    DOMAIN = member_check
    NORM_PREFIX = "SIA 265 "   # what the results' head writes before a clause given alone, «4.2.2.1»
    POSITION_HINT_KEY = "mc_position_hint"   # what the card «Position» says follows the position
    # «Calcul» -- the checks, the form, the Python result -- and «Affichage» -- the checks, the page the report prints, the options and the call (views.py, the engineer's request of 07.10.2026)
    VIEWS = views.CALC_VIEWS

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.linkables, self.wrappers = {}, {}   # the fields that may follow a variable, by their key in the source (spec 2026-10-11-variables-liees-champs-et-textes)
        self.t = app.t
        self.loading = False
        self.dirty = False
        self.current_id = None
        self.live = False         # the preview is compiled once the tab has been shown: building the window compiles nothing
        self.view = "calc"
        self.record = None
        self.reason = ""
        self.ids = []
        self.empty_folders = list(app.folder_settings(self.KEY))   # folders holding nothing: a view preference, kept in the project file by the window
        self.source = self.make_source()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.addWidget(self.build_list())
        self.splitter.addWidget(self.build_form())
        self.splitter.addWidget(self.build_result())
        self.build_display()
        self.panes = display_view.ViewPanes(self.splitter, self.display)
        for index, stretch in enumerate((2, 5, 5)):
            self.splitter.setStretchFactor(index, stretch)
        layout.addWidget(self.splitter, 1)

        self.refresh_timer = QTimer(self)
        self.refresh_timer.setSingleShot(True)
        self.refresh_timer.setInterval(OPTION_DELAY_MS)
        self.refresh_timer.timeout.connect(self.request_preview)   # the page is asked for a moment after the last edit; the results are not waited for
        self.install_save_shortcut()   # Ctrl+S, as in every editor tab
        self.restore(app.views.get(self.KEY))

    # --- small helpers ---------------------------------------------------------

    def tl(self, text):
        """A word the DATA carries, in the window's language -- through the glossary the report reads (docs/typst/language.md §4bis)."""
        return strings.translate(text, self.app.lang)

    def decimal(self, value):
        """A norm's coefficient as a label writes it in the window's language: 1,4 in French and German, 1.4 in English."""
        text = _n(value)
        return text.replace(".", ",") if self.app.lang in ("fr", "de") else text

    def orange_note(self):
        """A line under a field that exists only while the value is written over or its position is gone: orange, hidden until then."""
        label = QLabel("")
        label.setWordWrap(True)
        label.setStyleSheet("color: %s;" % theme.colour("override"))
        return label

    def row_with_back(self, form, note, back):
        """The line `note` and its «Reprendre» button, one row of `form` that appears only where there is something to say."""
        line = QWidget()
        row = QHBoxLayout(line)
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(note, 1)
        row.addWidget(back)
        form.addRow("", line)
        return line

    def take_back_button(self, slot):
        button = QPushButton(self.t("mc_take_back"))
        button.setVisible(False)
        button.clicked.connect(slot)
        return button

    def touch(self, *_ignored):
        if self.loading:
            return
        self.dirty = True
        self.refresh(preview=False)      # the results and the call, at once
        self.refresh_timer.start()      # the page, a moment after the last edit (and only while the preview is open)

    def spin(self, minimum, maximum, decimals=1, step=1.0, suffix=""):
        box = QDoubleSpinBox()
        box.setRange(minimum, maximum)
        box.setDecimals(decimals)
        box.setSingleStep(step)
        box.setSuffix(suffix)
        box.setMinimumWidth(70)
        return box

    def linked(self, spin, key, unit, label):
        """`spin` with the button beside it that links it to a variable of the export (spec 2026-10-11-variables-liees-champs-et-textes, UI-001): the widget a form row holds in its place. `key` is the field's in the source (member_check.LINKABLE), `unit` what it is written in, `label` what the choosing bar names it."""
        wrapper = linkable_spin.LinkableSpin(spin, unit, label, lambda: self.app, self.app.lang)
        wrapper.changed.connect(self.touch)
        self.linkables[key] = wrapper
        self.wrappers[id(spin)] = wrapper
        return wrapper

    def row_of(self, spin):
        """The widget a form row holds for `spin`: its wrapper where it may follow a variable, else itself -- what `setRowVisible` names."""
        return self.wrappers.get(id(spin), spin)

    def fill_links(self, s):
        """Each field's link, as the source `s` states it, shown against the export's values read once."""
        found = links.links_of(s)
        values = linkable_spin.current_values() if found else {}
        for key, wrapper in self.linkables.items():
            wrapper.set_link(found.get(key), values)

    def draft_links(self, s):
        """The links of the form into the draft `s`, for the fields it holds -- a field the kind or the section does not hold takes none -- and the schema_version that says so (member_check.stamp_version)."""
        found = {}
        for key, wrapper in self.linkables.items():
            link = wrapper.link()
            if link is not None and links.get_path(s, key) is not None:
                found[key] = link
        if found:
            s[links.LINKS] = found
        else:
            s.pop(links.LINKS, None)
        self.DOMAIN.stamp_version(s)

    def positions(self):
        """The positions the export holds, read again only when the export has moved (the index's time): every edit reads them, and an edit must not wait for the disk."""
        data_dir = project.current().data_dir
        index = data_dir / "positions-index.json"
        try:
            key = (str(data_dir), index.stat().st_mtime_ns)
        except OSError:
            key = (str(data_dir), None)
        if getattr(self, "_positions_key", None) != key:
            self._positions_cache = connector.known_positions(data_dir)
            self._positions_key = key
        return self._positions_cache

    def sources_dir(self):
        """The folder the tab's sources are files of: Woodcore-Datei/checks/ for a member check."""
        return project.current().checks_dir

    def _taken(self):
        """Every ID in use, **of every kind**: the checks share one folder, and an ID is the file's name."""
        folder = self.sources_dir()
        return sorted(p.stem for p in folder.glob("*.json")) if folder.is_dir() else []

    def prepare_display(self):
        """Before «Affichage» opens: the call this tab builds itself, its options and its page (display_view.DisplayTab.set_view)."""
        self.fill_command()

    def duplicate_id(self, source):
        return next_free_id(self._taken(), self.ID_PREFIX)   # every kind's checks share checks/: a copy's id is free among all of them

    def export_sources(self):
        self.DOMAIN.export(project.current())

    def saved_ids(self):
        return self._own_ids()

    def archived_entries(self):
        return self._archived_of_kind()

    def _own_ids(self):
        """The IDs of the checks of this tab's kind -- a source without a `kind` is a tension, the first kind there was."""
        folder = self.sources_dir()
        ids = []
        for cid in self._taken():
            try:
                source = json.loads((folder / ("%s.json" % cid)).read_text(encoding="utf-8"))
            except (OSError, ValueError):
                source = {}
            if self.owns(source):
                ids.append(cid)
        return ids

    def owns(self, source):
        """Whether this tab lists `source`: a check of its kind at normal temperature -- one in the fire situation (`fire`) is the «Résistance au feu» tab's, whatever its kind (issue #46)."""
        return (source.get("kind") or "tension") == self.KIND and source.get("fire") is None

    def current_kind(self):
        """The kind the draft is written as: the tab's own -- a tab of several kinds says which is chosen."""
        return self.KIND

    def resolve_draft(self, source):
        """The draft resolved as the export will resolve it: against the positions the last export wrote (and, for a tab that has one, the project's building)."""
        return member_check.resolve(source, self.positions())

    def _archived_of_kind(self):
        """The archived checks of this tab's kind, as the list shows them."""
        folder = source_archive.folder(self.sources_dir())
        rows = []
        for row in source_archive.entries(self.sources_dir(), self.list._t):
            try:
                source = json.loads((folder / row["id"][len(source_archive.KEY_PREFIX):]).read_text(encoding="utf-8"))
            except (OSError, ValueError):
                source = {}
            if self.owns(source):
                rows.append(row)
        return rows

    def make_source(self):
        """A new source of this tab's kind, under the first free ID: the engine's defaults, and what only this kind holds."""
        return self.extend_source(self.DOMAIN.new_source(next_free_id(self._taken(), self.ID_PREFIX), self.KIND))

    def extend_source(self, source):
        """What a kind holds beyond the common fields, set to its defaults where the source lacks it. The engine's `new_source` may already."""
        return source

    # --- left: the checks ----------------------------------------------------------


    # --- middle: the form --------------------------------------------------------


    # --- right: the result ---------------------------------------------------------


    # --- «Affichage»: the options, the call and the page (display_view.py, v0.117) ----------


    # --- the draft <-> the form ----------------------------------------------------


    # --- what is calculated, shown, and the command -------------------------------


    # --- the buttons ----------------------------------------------------------------


    # --- state across a rebuild -----------------------------------------------------------

    def view_state(self):
        return {
            "draft": copy.deepcopy(self.draft()),
            "current_id": self.current_id,
            "dirty": self.dirty,
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
            self.splitter.setSizes([2000, 4500, 4500])
            return
        self.source = state.get("draft") or self.source
        self.current_id = state.get("current_id")
        self.dirty = bool(state.get("dirty"))
        self.empty_folders = list(state.get("empty_folders") or [])
        self.reload_list(self.current_id)
        self.fill_form()
        if state.get("splitter"):
            self.splitter.setSizes(state["splitter"])
        self.refresh()


class BucklingLengths:
    """The card «Longueurs de flambage», one class for the two kinds that read it (the engineer, 11.10.2026, D-09): a buckling, and a lateral torsional buckling with a compression, (37). The source holds `l_y`, `l_z` -- the system lengths, mm, 0 holding the member about that axis -- and `beta_y`, `beta_z`; l_k = beta · l is the report's (`timber-store-lk`)."""

    def build_lengths(self, note_key=None):
        box = cards.card(self.t("mc_box_lengths"))
        self.lengths_card = box
        form = cards.form(box)
        self.l_spins, self.beta_spins = {}, {}
        for axis in ("y", "z"):
            spin = self.spin(0.0, 1_000_000.0, 0, 100.0, " mm")
            spin.valueChanged.connect(self.touch)
            form.addRow(self.t("mc_l_" + axis), self.linked(spin, "l_" + axis, "mm", "l_" + axis))
            self.l_spins[axis] = spin
        for axis in ("y", "z"):
            spin = self.spin(0.0, 10.0, 2, 0.1)
            spin.setValue(1.0)
            spin.valueChanged.connect(self.touch)
            form.addRow(self.t("mc_beta_" + axis), self.linked(spin, "beta_" + axis, "", "β_" + axis))
            self.beta_spins[axis] = spin
        form.addRow("", cards.note(self.t("mc_lengths_hint")))
        if note_key:
            form.addRow("", cards.note(self.t(note_key)))
        self.form.addWidget(box)

    def fill_lengths(self, s):
        for axis in ("y", "z"):
            self.l_spins[axis].setValue(float(s.get("l_" + axis) or 0))
            self.beta_spins[axis].setValue(float(s.get("beta_" + axis) if s.get("beta_" + axis) is not None else 1))

    def draft_lengths(self, s):
        for axis in ("y", "z"):
            s["l_" + axis] = self.l_spins[axis].value()
            s["beta_" + axis] = self.beta_spins[axis].value()
