"""The «Métré» tab, under «Positions» (spec docs/requirements/completed/2026-10-21-commandes-typst-refonte.md, UI-003, Q-003: «la carte devient un onglet « Métré » sous Positions, lit data/quantities.json et écrit son fichier .typ»): what the position plans draw, by material then section -- pieces, length, volume -- with a total per material, of everything drawn, of one plan or of chosen positions.

**Read, never measured here**: the rows are the export's (`data/quantities.json`, calc/domains/quantities.py), added up for the scope by `quantities.summary`, the report's own rule -- no plan is read again in the window. The export's date is said, and a banner says when a plan was saved after it (the quantities then lag behind it until the next export). Its file, `Positions/quantities.typ`, is written once and added to (list_file_card.py). Until the spec the card «Métrés» of the «Positions» tab measured the plans itself.
"""

import datetime
import json

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QAbstractItemView, QComboBox, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QTreeWidget, QTreeWidgetItem,
                               QVBoxLayout, QWidget)

import cards
import list_file_card
import project
import theme
from domains import quantities
from i18n import strings as engine_words

STRINGS = {
    "fr": {
        "tab_metre": "Métré",
        "mt_scope": "Portée",
        "mt_scope_all": "Tout ce que les plans dessinent",
        "mt_scope_plans": "Un plan de positions",
        "mt_scope_positions": "Positions choisies",
        "mt_plan": "Plan",
        "mt_positions": "Positions",
        "mt_exported": "Lu de l’export du {date} (data/quantities.json).",
        "mt_not_exported": "Pas encore d’export : exportez le projet pour mesurer ce que les plans dessinent.",
        "mt_stale": "Périmé : {plans} enregistré(s) après l’export — exportez pour mettre le métré à jour.",
        "mt_none_selected": "Choisissez une ou plusieurs positions.",
    },
    "de": {
        "tab_metre": "Ausmass",
        "mt_scope": "Umfang",
        "mt_scope_all": "Alles, was die Pläne zeichnen",
        "mt_scope_plans": "Ein Positionsplan",
        "mt_scope_positions": "Gewählte Positionen",
        "mt_plan": "Plan",
        "mt_positions": "Positionen",
        "mt_exported": "Aus dem Export vom {date} gelesen (data/quantities.json).",
        "mt_not_exported": "Noch kein Export: exportieren Sie das Projekt, um zu messen, was die Pläne zeichnen.",
        "mt_stale": "Veraltet: {plans} nach dem Export gespeichert — exportieren Sie, um das Ausmass nachzuführen.",
        "mt_none_selected": "Wählen Sie eine oder mehrere Positionen.",
    },
    "en": {
        "tab_metre": "Quantities",
        "mt_scope": "Scope",
        "mt_scope_all": "Everything the plans draw",
        "mt_scope_plans": "One position plan",
        "mt_scope_positions": "Chosen positions",
        "mt_plan": "Plan",
        "mt_positions": "Positions",
        "mt_exported": "Read from the export of {date} (data/quantities.json).",
        "mt_not_exported": "No export yet: export the project to measure what the plans draw.",
        "mt_stale": "Out of date: {plans} saved after the export — export to bring the quantities up to date.",
        "mt_none_selected": "Choose one or more positions.",
    },
}

SCOPES = (("all", "mt_scope_all"), ("plans", "mt_scope_plans"), ("positions", "mt_scope_positions"))


def read_export(here):
    """The export's quantities -- {rows, plans, …} --, or None where the project was not exported yet or the file does not read."""
    try:
        return json.loads((here.data_dir / "quantities.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def stale_plans(here):
    """The position plans saved after the export's quantities were written, by their file's name -- what makes the tab's banner."""
    written = here.data_dir / "quantities.json"
    if not written.is_file():
        return []
    since = written.stat().st_mtime
    folder = here.plans_dir
    return sorted(p.stem for p in folder.glob("*.json") if p.stat().st_mtime > since) if folder.is_dir() else []


class MetreTab(QWidget):
    """The tab: the scope, the table of the export's quantities for it, the export's date and its banner, and the card of its file."""

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.t = app.t
        self.data = None
        outer = QVBoxLayout(self)
        self.banner = QLabel("")
        self.banner.setWordWrap(True)
        self.banner.setStyleSheet(f"color: {theme.colour('warning')}; font-weight: bold;")
        outer.addWidget(self.banner)
        card = cards.card(engine_words.text("quantities.title", app.lang))
        column = QVBoxLayout(card)
        row = QHBoxLayout()
        row.addWidget(QLabel(self.t("mt_scope")))
        self.scope_combo = QComboBox()
        for scope, key in SCOPES:
            self.scope_combo.addItem(self.t(key), scope)
        self.scope_combo.currentIndexChanged.connect(self.refresh_table)
        row.addWidget(self.scope_combo, 1)
        column.addLayout(row)
        plan_row = QHBoxLayout()
        self.plan_caption = QLabel(self.t("mt_plan"))
        plan_row.addWidget(self.plan_caption)
        self.plan_combo = QComboBox()
        self.plan_combo.currentIndexChanged.connect(self.refresh_table)
        plan_row.addWidget(self.plan_combo, 1)
        column.addLayout(plan_row)
        self.position_caption = QLabel(self.t("mt_positions"))
        column.addWidget(self.position_caption)
        self.position_list = QListWidget()
        self.position_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.position_list.itemSelectionChanged.connect(self.refresh_table)
        self.position_list.setMaximumHeight(8 * self.fontMetrics().height())
        column.addWidget(self.position_list)
        self.table = QTreeWidget()
        words = lambda key: engine_words.text(key, app.lang)
        self.table.setHeaderLabels([words("quantities.material"), words("quantities.section"), words("quantities.pieces"), words("quantities.length"), words("quantities.volume")])
        self.table.setRootIsDecorated(False)
        self.table.setUniformRowHeights(True)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        column.addWidget(self.table, 1)
        self.note = cards.note("")
        column.addWidget(self.note)
        self.exported = cards.note("")
        column.addWidget(self.exported)
        outer.addWidget(card, 1)
        self.file_card = list_file_card.ListFileCard(app, "quantities")
        outer.addWidget(self.file_card.card)
        self.reload()
        self.restore(getattr(app, "views", {}).get("tab_metre"))

    # -- surviving a rebuild: the scope, the plan and the positions chosen ---------------------

    def view_state(self):
        return {"scope": self.scope_combo.currentData(), "plan": self.plan_combo.currentData(), "positions": self.chosen_positions()}

    def restore(self, state):
        if not state:
            return
        index = self.scope_combo.findData(state.get("scope"))
        if index >= 0:
            self.scope_combo.setCurrentIndex(index)
        index = self.plan_combo.findData(state.get("plan"))
        if index >= 0:
            self.plan_combo.setCurrentIndex(index)
        chosen = set(state.get("positions") or ())
        for i in range(self.position_list.count()):
            self.position_list.item(i).setSelected(self.position_list.item(i).text() in chosen)
        self.refresh_table()

    def on_shown(self):
        """The tab brought to the front: the export read again -- an export run meanwhile is what it shows."""
        self.reload()

    def reload(self):
        try:
            here = project.current()
        except project.ProjectError:
            return
        self.data = read_export(here)
        stale = stale_plans(here)
        self.banner.setText(self.t("mt_stale", plans=", ".join(stale)) if stale else "")
        self.banner.setVisible(bool(stale))
        if self.data is None:
            self.exported.setText(self.t("mt_not_exported"))
        else:
            when = datetime.datetime.fromtimestamp((here.data_dir / "quantities.json").stat().st_mtime).strftime("%d.%m.%Y %H:%M")
            self.exported.setText(self.t("mt_exported", date=when))
        rows = (self.data or {}).get("rows", [])
        wanted = self.plan_combo.currentData()
        self.plan_combo.blockSignals(True)
        self.plan_combo.clear()
        for pid in (self.data or {}).get("plans", {}):
            self.plan_combo.addItem(pid, pid)
        index = self.plan_combo.findData(wanted)
        self.plan_combo.setCurrentIndex(max(index, 0))
        self.plan_combo.blockSignals(False)
        chosen = set(self.chosen_positions())
        self.position_list.blockSignals(True)
        self.position_list.clear()
        for pid in sorted({r["position"] for r in rows}):
            item = QListWidgetItem(pid)
            self.position_list.addItem(item)
            item.setSelected(pid in chosen)
        self.position_list.blockSignals(False)
        self.refresh_table()
        self.file_card.refresh()

    def chosen_positions(self):
        return [item.text() for item in self.position_list.selectedItems()]

    def refresh_table(self, *_args):
        """The table for the scope chosen: each group by material and section, then each material's total in bold -- `quantities.summary` of the export's rows, nothing measured here."""
        scope = self.scope_combo.currentData() or "all"
        self.plan_caption.setVisible(scope == "plans")
        self.plan_combo.setVisible(scope == "plans")
        self.position_caption.setVisible(scope == "positions")
        self.position_list.setVisible(scope == "positions")
        rows = (self.data or {}).get("rows", [])
        chosen = self.chosen_positions()
        groups, totals = quantities.summary(rows, scope, plans=[self.plan_combo.currentData()] if scope == "plans" else (), positions=chosen)
        self.table.clear()
        bold = QFont(self.table.font())
        bold.setBold(True)
        for total in totals:
            for group in (g for g in groups if g["material"] == total["material"]):
                self.table.addTopLevelItem(self.item(group["material"], group["section"], group))
            item = self.item(engine_words.text("quantities.total", self.app.lang) + (" " + total["material"] if total["material"] else ""), "", total)
            for column in range(5):
                item.setFont(column, bold)
            self.table.addTopLevelItem(item)
        for column in range(5):
            self.table.resizeColumnToContents(column)
        note = self.t("mt_none_selected") if scope == "positions" and not chosen else engine_words.text("quantities.empty", self.app.lang) if not groups and self.data is not None else ""
        self.note.setText(note)
        self.note.setVisible(bool(note))

    @staticmethod
    def item(material, section_text, values):
        item = QTreeWidgetItem([material or "—", section_text, str(values["pieces"]), quantities.metres(values["length_m"]), quantities.metres(values["volume_m3"], 3)])
        for column in (2, 3, 4):
            item.setTextAlignment(column, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        return item
