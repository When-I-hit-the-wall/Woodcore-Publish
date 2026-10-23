# -*- coding: utf-8 -*-
"""The member checks of SIA 265 chapter 4 in Woodcore's window: «Sécurité structurale» and «Aptitude au service» (docs/domain/member-checks.md §3.3undecies, docs/ui/window.md §10quater).

The report writes a member's checks with `#member` and the `verify-*` commands (lib/timber.typ); this is where an engineer sets one up without writing the call. Two navigation groups, in the report alone -- the convention d'utilisation and the base de projet check no member --, nine modules:

| group | modules |
|---|---|
| Sécurité structurale (SIA 265 4.2) | Traction · Compression · Flexion · Effort tranchant · Torsion · Flambage · Déversement |
| Aptitude au service (SIA 265 4.3 and 4.4) | Déformations (fatigue included) · Vibrations |

**«Traction» (`TensionTab`), «Compression» (`CompressionTab`), «Flexion» (`BendingTab`), «Effort tranchant» (`ShearTab`), «Flambage» (`BucklingTab`) and «Déversement» (`LateralTab`) are built** (the last three since issue #38), on one base (`MemberCheckTab`): the other three are placeholders (`SoonTab`) that say what they will hold and which command of the report does the work meanwhile. «Flexion» is bending, alone (4.2.3) or **combined with a normal force** (4.2.4), the section alone; «Effort tranchant» is the shear of 4.2.5.1, shear-off, shear with a stress perpendicular to the grain and torsion staying commands of the report, which its card says; «Flambage» and «Déversement» share one card of buckling lengths (`BucklingLengths`, D-09).

**A check is a source file**, `Woodcore-Datei/checks/<id>.json`, written by these tabs and read by `calc/domains/member_check.py`, which the export turns into `data/checks.json` (the connectors' arrangement, docs/domain/connectors.md §3.3nonies). Each tab lists the checks **of its own kind** and nothing else, while an ID is unique across every kind (the folder is shared). Three panes, the connectors' too: the checks in folders at the left (`grouped_list.py`; «Supprimer» archives, `source_archive.py`); the form in cards in the middle -- Nom · Description · ID (`identity.py`), the position it concerns, the material, the section, the effort --; and at the right the **result**, Python's, instant. Since v0.117 the tab has two views (views.py): **«Calcul»** is those three panes; **«Affichage»** keeps the list and shows in the middle the page the command prints, compiled from the DRAFT as it is typed (display_view.DisplayView, Typst's own message in the pane's banner and never in a modal), and at the right the options of the command and the call to copy.

⚠️ **A value that follows its position says so in its own field** -- «C24 — T001» (the v0.77 rule, its words since v0.117) -- and **a value typed over it stays written over**: an orange line names what the position holds, with «Reprendre» beside it (the connectors' rule, v0.70). The strength class, the section and the moisture class each have a first entry that follows; choosing any other writes the value into the source, and choosing the first again is «Reprendre».

⚠️ **Compression** (SIA 265 4.2.2.1 and 4.2.2.3): the angle α between the force and the grain is 0 for a member compressed along the grain, and then the force is the normal force N; above 0 it is a force F on a bearing surface, and a card «Appui» appears -- the resistance f_c,90,d among five entries (general, with end timber, at an end support, the last two each with or without the bracketed value of Tabelle 8 note 4), the bearing length l and the contact width w, which follows the section's width and is written over in orange with «Reprendre». A grade with no bracketed value (D30) has the two bracketed entries closed.

⚠️ **Bending** (SIA 265 4.2.3 and 4.2.4, the section alone -- «Déversement» and «Flambage» are modules of their own): the card «Effort» holds α, the moments M_y,d and M_z,d and the normal force N_d, **signed** -- tension +, compression −, 0 for none --, which chooses (14), (21) or (22). At an angle α > 0 the field of M_z,d is set to 0 and closed, a line saying why: (17) to (20) read M_y,d alone; a normal force stays, (21) or (22) then taking the strengths at that angle (the engineer's reading of 08.10.2026, member_check.py).

⚠️ **The results are Python's and instant** (the engineer's decision of 07.10.2026): the right pane opens on the card «Résultats» -- each value of the check as the report computes it (`member_check.compute`, the same arithmetic as the Typst commands), the equation, and the verdict -- the ratio of the action to the resistance, `σ/f = 0.41 ⩽ 1`, as the report prints it since issue #12 (in percent `σ/f = 41 %`), never η -- with ✔ in the `ok` colour or ✘ in `danger` -- recomputed at every edit, with no wait; then the call to copy; then two **collapsible** sections, closed by default: the options of the command and the Typst preview. The preview is compiled **only while it is open** (a compile is what made editing wait).

⚠️ **The call needs the check saved.** The preview compiles the draft, whose values are written into the call; the command to copy names the check by its ID, and Typst only knows the checks the last export wrote -- the tab says so under the call until the check is saved.
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

# The five resistances f_c,90,d of a bearing: (the combo's data, the source's `case`, its `larger` -- the bracketed value of Tabelle 8 note 4 --, the key of its words). The keys are literals on purpose: tests/test_i18n.py finds a key by the code that names it.
SUPPORT_CHOICES = (
    ("general", "generell", False, "mc_sup_general"),
    ("vorholz", "mit_vorholz", False, "mc_sup_vorholz"),
    ("vorholz+", "mit_vorholz", True, "mc_sup_vorholz_larger"),
    ("end", "endauflagerung", False, "mc_sup_end"),
    ("end+", "endauflagerung", True, "mc_sup_end_larger"),
)
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


class TensionTab(MemberCheckTab):
    """Traction: SIA 265 4.2.1, `#verify-tension`."""

    KEY = "tab_mc_tension"
    KIND = "tension"
    ID_PREFIX = "Z_"


class CompressionTab(MemberCheckTab):
    """Compression: SIA 265 4.2.2.1 along the grain (α = 0, the force is the normal force N) and 4.2.2.3 at an angle to it (α > 0, the force is a force F on a bearing surface, which a card «Appui» describes: the resistance f_c,90,d, the bearing length l and the contact width w). The source holds `case`, `larger`, `l` and `w` all the time -- the card is only hidden at α = 0, and what it held stays."""

    KEY = "tab_mc_compression"
    KIND = "compression"
    ID_PREFIX = "DR-"
    LIST_KEY = "mc_list_compression"
    EMPTY_KEY = "mc_empty_compression"
    N_KEY = "mc_N_compression"
    w_stated = False     # the contact width is written over (else it follows the section's width)

    def extend_source(self, source):
        source.setdefault("case", "generell")
        source.setdefault("larger", False)
        source.setdefault("l", None)
        source.setdefault("w", None)
        return source

    def build_effort(self):
        self.effort_card(self.N_KEY)
        box = cards.card(self.t("mc_box_support"))
        self.support_card = box
        form = cards.form(box)
        self.support_form = form
        self.support_box = QComboBox()
        self.support_box.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.support_box.setMinimumContentsLength(18)
        self.support_box.view().setMinimumWidth(520)      # the popup is as wide as its longest sentence, the combo only as the column
        for index, (data, _case, _larger, key) in enumerate(SUPPORT_CHOICES):
            self.support_box.addItem(self.t(key), data)
            self.support_box.setItemData(index, self.t(key), Qt.ItemDataRole.ToolTipRole)
        self.support_box.currentIndexChanged.connect(self.on_field)
        form.addRow(self.t("mc_support_resistance"), self.support_box)
        self.support_note = self.orange_note()
        form.addRow("", self.support_note)
        self.l_spin = self.spin(0.0, 100_000.0, 1, 10.0, " mm")
        self.l_spin.setSpecialValueText(self.t("mc_none"))      # 0 is «not stated»: the check is then not calculable, which the page says
        self.l_spin.valueChanged.connect(self.touch)
        form.addRow(self.t("mc_l"), self.linked(self.l_spin, "l", "mm", "l"))
        self.w_spin = self.spin(1.0, 100_000.0, 1, 10.0, " mm")
        self.w_spin.setValue(100.0)
        self.w_spin.valueChanged.connect(self.on_w)
        form.addRow(self.t("mc_w"), self.linked(self.w_spin, "w", "mm", "w"))
        self.w_note = self.orange_note()
        self.w_back = self.take_back_button(self.take_back_w)
        self.w_line = self.row_with_back(form, self.w_note, self.w_back)
        self.form.addWidget(box)

    # --- the form --------------------------------------------------------------

    def support_choice(self):
        """(case, larger) of the resistance chosen."""
        data = self.support_box.currentData()
        for key, case, larger, _words in SUPPORT_CHOICES:
            if key == data:
                return case, larger
        return SUPPORT_CHOICES[0][1:3]

    def fill_effort(self, s):
        super().fill_effort(s)
        wanted = (s.get("case") or "generell", bool(s.get("larger")))
        index = next((i for i, c in enumerate(SUPPORT_CHOICES) if (c[1], c[2]) == wanted),
                     next(i for i, c in enumerate(SUPPORT_CHOICES) if c[1] == wanted[0]))   # an entry the five do not name (generell and larger) keeps the case
        self.support_box.setCurrentIndex(index)
        self.l_spin.setValue(float(s.get("l") or 0))
        width = s.get("w")
        self.w_stated = width is not None
        if width is not None:
            self.w_spin.setValue(float(width))
        self.update_effort_view()

    def draft_effort(self, s):
        super().draft_effort(s)
        s["case"], s["larger"] = self.support_choice()
        s["l"] = self.l_spin.value() or None
        s["w"] = self.w_spin.value() if self.w_stated else None

    def update_effort_view(self):
        """The force's label and the card «Appui» follow α: a normal force along the grain, a force on a surface across it. The card is shown and hidden and nothing is rebuilt, so a field under the pointer stays."""
        across = self.alpha_spin.value() > 0
        self.n_label.setText(self.t("mc_F_support" if across else "mc_N_compression"))
        self.support_card.setVisible(across)

    def on_alpha(self, *_args):
        self.update_effort_view()
        super().on_alpha()

    def on_size(self, *_args):
        if self.loading:
            return
        self.fill_notes()      # a width that follows the section follows its new size
        self.touch()

    def on_w(self, *_args):
        """The contact width typed: it is written over now."""
        if self.loading:
            return
        self.w_stated = True
        self.fill_notes()
        self.touch()

    def take_back_w(self):
        self.w_stated = False
        self.fill_notes()
        self.touch()

    def effective_grade(self):
        """The strength class the check is calculated with: the one written over, else the position's."""
        grade = self.grade_box.currentData()
        if grade:
            return grade
        _pid, record = self.held()
        if record is None:
            return None
        return ((record.get("strength_class") if "strength_class" in record else record.get("material")) or "").strip() or None

    @staticmethod
    def has_bracket(grade, case):
        """Whether Tabelle 8 or 9 gives `grade` a bracketed f_c,90,d for `case` -- True where the grade is unknown: nothing says it has none."""
        try:
            cell = sia265.grade(grade)["f_c_90_d"][case]
        except (validation.ValidationError, KeyError, TypeError):
            return True
        return isinstance(cell, dict) and cell.get("groessere_eindrueckungen") is not None

    def held_width(self):
        """The width the section gives the contact: b of a rectangle, d of a round section -- the one written over in the form, else the position's. None where there is none."""
        kind = self.section_box.currentData()
        if kind == "rec":
            return self.b_spin.value()
        if kind == "cir":
            return self.d_spin.value()
        _pid, record = self.held()
        held = held_section(record) if record else None
        if held is None:
            return None
        return held["b"] if held["type"] == "rec" else held["d"]

    def fill_effort_notes(self):
        override = theme.colour("override")
        # the resistances: a grade without a bracketed value closes the two entries that need one
        grade = self.effective_grade()
        model = self.support_box.model()
        closed_chosen = False
        for index, (data, case, larger, words) in enumerate(SUPPORT_CHOICES):
            usable = not larger or grade is None or self.has_bracket(grade, case)
            model.item(index).setEnabled(usable)
            tip = self.t(words) if usable else self.t("mc_sup_nobracket_tip", grade=grade)
            self.support_box.setItemData(index, tip, Qt.ItemDataRole.ToolTipRole)
            if not usable and self.support_box.currentData() == data:
                closed_chosen = True
        note = self.t("mc_sup_nobracket", grade=grade) if closed_chosen else ""
        self.support_note.setText(note)
        self.support_note.setStyleSheet("color: %s;" % override)
        self.support_form.setRowVisible(self.support_note, bool(note))
        # the contact width: it follows the section's width unless it is written over
        held = self.held_width()
        if self.w_stated:
            self.w_spin.setSpecialValueText("")
            self.w_spin.setSuffix(" mm")
        elif held is not None:
            self.w_spin.setSpecialValueText("")
            self.w_spin.setValue(max(held, self.w_spin.minimum()))
            self.w_spin.setSuffix(self.t("mc_w_followed"))
        else:
            self.w_spin.setValue(self.w_spin.minimum())
            self.w_spin.setSpecialValueText(self.t("mc_none"))
            self.w_spin.setSuffix(" mm")
        text, back = "", False
        if self.w_stated and held is not None:
            text, back = self.t("mc_w_overridden", value=_n(held)), True
        self.w_note.setText(text)
        self.w_note.setStyleSheet("color: %s;" % override)
        self.w_back.setVisible(back)
        self.support_form.setRowVisible(self.w_line, bool(text))
        self.update_effort_view()


class BendingTab(MemberCheckTab):
    """Flexion: SIA 265 4.2.3 and 4.2.4, the section alone -- `#verify-bending(stability: false)` without a normal force, `#verify-bending-normal(stability: false)` with one. The card «Effort» holds α, M_y,d, M_z,d and N_d, signed (tension +, compression −, 0 for none); at α > 0 M_z,d is set to 0 and closed, (17) to (20) reading M_y,d alone. What the check works out is `member_check.compute`'s, as for the other kinds."""

    KEY = "tab_mc_bending"
    KIND = "bending"
    ID_PREFIX = "BI-"
    LIST_KEY = "mc_list_bending"
    EMPTY_KEY = "mc_empty_bending"
    N_KEY = "mc_N_bending"
    ALPHA_KEY = "mc_alpha_bending"
    N_MIN = -1_000_000.0

    def extend_source(self, source):
        source.setdefault("M_y", {"value": 10, "unit": "kNm"})
        source.setdefault("M_z", None)
        return source

    def build_effort(self):
        self.effort_card(self.N_KEY)
        form = self.effort_form
        self.my_spin = self.spin(0.0, 1_000_000.0, 2, 0.5, " kNm")
        self.my_spin.valueChanged.connect(self.touch)
        form.addRow(self.t("mc_My"), self.linked(self.my_spin, "M_y", "kNm", "M_y"))
        self.mz_spin = self.spin(0.0, 1_000_000.0, 2, 0.5, " kNm")
        self.mz_spin.valueChanged.connect(self.touch)
        form.addRow(self.t("mc_Mz"), self.linked(self.mz_spin, "M_z", "kNm", "M_z"))
        self.mz_note = QLabel(self.t("mc_Mz_angle"))
        self.mz_note.setWordWrap(True)
        self.mz_note.setStyleSheet("color: %s;" % theme.colour("muted"))
        form.addRow("", self.mz_note)

    # --- the form --------------------------------------------------------------

    def fill_effort(self, s):
        super().fill_effort(s)
        # a moment's sign says nothing a section check reads: the field holds its magnitude, in kNm as Woodcore writes it
        for key, box in (("M_y", self.my_spin), ("M_z", self.mz_spin)):
            box.setValue(abs(float((s.get(key) or {}).get("value") or 0)))
        self.update_effort_view()

    def draft_effort(self, s):
        super().draft_effort(s)
        across = self.alpha_spin.value() > 0
        for key, box in (("M_y", self.my_spin), ("M_z", self.mz_spin)):
            value = 0.0 if key == "M_z" and across else box.value()
            s[key] = {"value": value, "unit": "kNm"} if value else None

    def update_effort_view(self):
        """At an angle to the grain M_z,d is 0 and closed, and a line says why; along it the field is open. Shown and hidden, nothing rebuilt."""
        across = self.alpha_spin.value() > 0
        if across and self.mz_spin.value():
            self.mz_spin.setValue(0.0)
        self.mz_spin.setEnabled(not across)
        self.effort_form.setRowVisible(self.mz_note, across)

    def on_alpha(self, *_args):
        self.update_effort_view()
        super().on_alpha()


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


class BucklingTab(BucklingLengths, MemberCheckTab):
    """Flambage: SIA 265 4.2.8 -- `#verify-compression` with its stability, along the grain: the section (10) and about each axis (29) with k_c of (30), (31). The card «Effort» holds the compressive force's magnitude, α being 0; the card «Longueurs de flambage» the system lengths and their coefficients (issue #38)."""

    KEY = "tab_mc_buckling"
    KIND = "buckling"
    ID_PREFIX = "KN-"
    LIST_KEY = "mc_list_buckling"
    EMPTY_KEY = "mc_empty_buckling"
    N_KEY = "mc_N_buckling"

    def extend_source(self, source):
        for key, value in (("l_y", 3000), ("l_z", 3000), ("beta_y", 1), ("beta_z", 1)):
            source.setdefault(key, value)
        return source

    def build_effort(self):
        self.effort_card(self.N_KEY)
        self.effort_form.setRowVisible(self.row_of(self.alpha_spin), False)    # along the grain: alpha is 0
        self.build_lengths()

    def fill_effort(self, s):
        super().fill_effort(s)
        self.fill_lengths(s)

    def draft_effort(self, s):
        super().draft_effort(s)
        s["alpha"] = 0
        self.draft_lengths(s)


class LateralTab(BucklingLengths, MemberCheckTab):
    """Déversement: SIA 265 4.2.9 -- `#verify-bending` or `#verify-bending-normal` with their stability, along the grain: the moments, N signed (tension +, compression −, 0 for none), and σ_m,crit by (41) from the distance a between the lateral supports, or as a finer calculation gives it. With a compression, (37) also reads the buckling lengths, whose card is shown then (the engineer, 11.10.2026, D-09) -- hidden otherwise, what it holds kept (issue #38)."""

    KEY = "tab_mc_ltb"
    KIND = "lateral-torsional"
    ID_PREFIX = "KI-"
    LIST_KEY = "mc_list_ltb"
    EMPTY_KEY = "mc_empty_ltb"
    N_KEY = "mc_N_bending"
    N_MIN = -1_000_000.0

    def extend_source(self, source):
        source.setdefault("M_y", {"value": 10, "unit": "kNm"})
        source.setdefault("M_z", None)
        source.setdefault("a", 3000)
        source.setdefault("sigma_m_crit", None)
        return source

    def build_effort(self):
        self.effort_card(self.N_KEY)
        form = self.effort_form
        form.setRowVisible(self.row_of(self.alpha_spin), False)    # along the grain: alpha is 0
        self.n_spin.valueChanged.connect(self.update_effort_view)
        self.my_spin = self.spin(0.0, 1_000_000.0, 2, 0.5, " kNm")
        self.my_spin.valueChanged.connect(self.touch)
        form.addRow(self.t("mc_My"), self.linked(self.my_spin, "M_y", "kNm", "M_y"))
        self.mz_spin = self.spin(0.0, 1_000_000.0, 2, 0.5, " kNm")
        self.mz_spin.valueChanged.connect(self.touch)
        form.addRow(self.t("mc_Mz"), self.linked(self.mz_spin, "M_z", "kNm", "M_z"))
        box = cards.card(self.t("mc_box_lateral"))
        lateral = cards.form(box)
        self.lateral_form = lateral
        self.by_box = QComboBox()
        self.by_box.addItem(self.t("mc_lateral_a"), "a")
        self.by_box.addItem(self.t("mc_lateral_crit"), "crit")
        # nothing tips: a round section, or one wider than high bent about y alone -- neither a nor sigma_m,crit (spec 2026-10-12-audit-issues-47-48-49, D-10, D-17)
        self.by_box.addItem(self.t("mc_lateral_none"), "none")
        self.by_box.currentIndexChanged.connect(self.update_effort_view)
        self.by_box.currentIndexChanged.connect(self.touch)
        lateral.addRow(self.t("mc_lateral_by"), self.by_box)
        self.a_spin = self.spin(1.0, 1_000_000.0, 0, 100.0, " mm")
        self.a_spin.setValue(3000.0)
        self.a_spin.valueChanged.connect(self.touch)
        lateral.addRow(self.t("mc_a"), self.linked(self.a_spin, "a", "mm", "a"))
        self.crit_spin = self.spin(0.01, 100_000.0, 2, 1.0, " N/mm²")
        self.crit_spin.setValue(40.0)
        self.crit_spin.valueChanged.connect(self.touch)
        lateral.addRow(self.t("mc_sigma_crit"), self.linked(self.crit_spin, "sigma_m_crit", "N/mm²", "σ_m,crit"))
        lateral.addRow("", cards.note(self.t("mc_ltb_round")))
        self.form.addWidget(box)
        self.build_lengths("mc_lengths_ltb")

    def fill_effort(self, s):
        super().fill_effort(s)
        for key, box in (("M_y", self.my_spin), ("M_z", self.mz_spin)):
            box.setValue(abs(float((s.get(key) or {}).get("value") or 0)))
        given = s.get("sigma_m_crit") is not None
        self.by_box.setCurrentIndex(self.by_box.findData("crit" if given else "a" if s.get("a") is not None else "none"))
        if s.get("a") is not None:
            self.a_spin.setValue(float(s["a"]))
        if given:
            self.crit_spin.setValue(float(s["sigma_m_crit"]))
        self.fill_lengths(s)
        self.update_effort_view()

    def draft_effort(self, s):
        super().draft_effort(s)
        s["alpha"] = 0
        for key, box in (("M_y", self.my_spin), ("M_z", self.mz_spin)):
            s[key] = {"value": box.value(), "unit": "kNm"} if box.value() else None
        by = self.by_box.currentData()
        s["a"] = self.a_spin.value() if by == "a" else None
        s["sigma_m_crit"] = self.crit_spin.value() if by == "crit" else None
        self.draft_lengths(s)

    def update_effort_view(self, *_args):
        """σ_m,crit is computed from a or given, one field shown; the buckling lengths are shown with a compression, which (37) reads. Shown and hidden, nothing rebuilt."""
        by = self.by_box.currentData()
        self.lateral_form.setRowVisible(self.row_of(self.a_spin), by == "a")
        self.lateral_form.setRowVisible(self.row_of(self.crit_spin), by == "crit")
        self.lengths_card.setVisible(self.n_spin.value() < 0)


class ShearTab(MemberCheckTab):
    """Effort tranchant: what the list at the head of its card says (spec 2026-10-21-commandes-typst-refonte, REQ-021, UI-005, Q-010: «le user choisit dans un menu déroulant quel type de cisaillement il souhaite calculer») -- the shear of SIA 265 4.2.5.1, the shear forces in the plane of h and of b added as vectors at the centroid and a member cut from the pith; the shear-off of 4.2.6, a force on a sheared length and width; the shear with a stress perpendicular to the grain of 4.2.7.1. Printed unfolded, as every check is since that spec (REQ-017). No normal force and no angle; torsion stays a command of the report."""

    KEY = "tab_mc_shear"
    KIND = "shear"
    ID_PREFIX = "SC-"
    LIST_KEY = "mc_list_shear"
    EMPTY_KEY = "mc_empty_shear"

    def extend_source(self, source):
        source.pop("N", None)
        source.setdefault("V_z", {"value": 10, "unit": "kN"})
        source.setdefault("V_y", None)
        source.setdefault("pith", False)
        source.setdefault("variant", "shear")
        return source

    def build_effort(self):
        self.effort_card(self.N_KEY)
        form = self.effort_form
        form.setRowVisible(self.row_of(self.alpha_spin), False)    # along the grain: alpha is 0
        form.setRowVisible(self.row_of(self.n_spin), False)        # a shear reads no normal force
        self.v_spins = {}
        for key, label in (("V_z", "mc_Vz"), ("V_y", "mc_Vy")):
            spin = self.spin(0.0, 1_000_000.0, 2, 1.0, " kN")
            spin.valueChanged.connect(self.touch)
            form.addRow(self.t(label), self.linked(spin, key, "kN", key))
            self.v_spins[key] = spin
        self.pith_box = QCheckBox(self.t("mc_pith"))
        self.pith_box.toggled.connect(self.touch)
        form.addRow("", self.pith_box)
        # what the check checks: the list at the head of the card, each variant showing its own fields (REQ-021, UI-005)
        from domains import member_check
        self.variant_box = QComboBox()
        for variant in member_check.SHEAR_VARIANTS:
            self.variant_box.addItem(self.t("mc_shear_" + variant.replace("-", "_")), variant)
        self.variant_box.currentIndexChanged.connect(self.variant_changed)
        form.insertRow(0, self.t("mc_shear_variant"), self.variant_box)
        self.f_off = self.spin(0.0, 1_000_000.0, 2, 1.0, " kN")
        self.l_off = self.spin(0.0, 100_000.0, 0, 10.0, " mm")
        self.w_off = self.spin(0.0, 100_000.0, 0, 10.0, " mm")
        self.w_off.setSpecialValueText(self.t("mc_w_off_auto"))     # 0: the member's width
        self.s90 = self.spin(-1000.0, 1000.0, 3, 0.1, " N/mm²")
        for spin, label in ((self.f_off, "mc_F_off"), (self.l_off, "mc_l_off"), (self.w_off, "mc_w_off"), (self.s90, "mc_sigma_90")):
            spin.valueChanged.connect(self.touch)
            form.addRow(self.t(label), spin)
        form.addRow("", cards.note(self.t("mc_shear_hint")))
        self.show_variant()

    def variant(self):
        return self.variant_box.currentData() or "shear"

    def variant_changed(self, *_ignored):
        """Another variant chosen: its fields shown, and the draft computed again."""
        self.show_variant()
        self.touch()

    def show_variant(self):
        """The fields of the variant chosen, and none of the others."""
        variant = self.variant()
        form = self.effort_form
        form.setRowVisible(self.row_of(self.v_spins["V_z"]), variant in ("shear", "shear-perp"))
        form.setRowVisible(self.row_of(self.v_spins["V_y"]), variant == "shear")
        form.setRowVisible(self.pith_box, variant == "shear")
        for spin in (self.f_off, self.l_off, self.w_off):
            form.setRowVisible(spin, variant == "shear-off")
        form.setRowVisible(self.s90, variant == "shear-perp")

    def fill_effort(self, s):
        self.alpha_spin.setValue(0.0)
        for key, spin in self.v_spins.items():
            spin.setValue(abs(float((s.get(key) or {}).get("value") or 0)))
        self.pith_box.setChecked(bool(s.get("pith")))
        index = self.variant_box.findData(s.get("variant") or "shear")
        self.variant_box.setCurrentIndex(max(index, 0))
        self.f_off.setValue(abs(float((s.get("F") or {}).get("value") or 0)))
        self.l_off.setValue(float(s.get("l") or 0))
        self.w_off.setValue(float(s.get("w") or 0))
        self.s90.setValue(float(s.get("sigma_90") or 0))
        self.show_variant()

    def draft_effort(self, s):
        s["alpha"] = 0
        s.pop("N", None)
        variant = self.variant()
        s["variant"] = variant
        for key, spin in self.v_spins.items():
            s[key] = {"value": spin.value(), "unit": "kN"} if spin.value() and (variant == "shear" or key == "V_z" and variant == "shear-perp") else None
        s["pith"] = self.pith_box.isChecked() and variant == "shear"
        s["F"] = {"value": self.f_off.value(), "unit": "kN"} if variant == "shear-off" and self.f_off.value() else None
        s["l"] = self.l_off.value() or None if variant == "shear-off" else None
        s["w"] = self.w_off.value() or None if variant == "shear-off" else None
        s["sigma_90"] = self.s90.value() if variant == "shear-perp" else None
