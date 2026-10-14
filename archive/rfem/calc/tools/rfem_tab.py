"""Woodcore's «RFEM» tab (docs/ui/window.md §10quater, docs/open-questions.md §14): the models an RFEM table export holds, the structures they are made of, and what each structure carries.

The engineer's own description, and its shape: «créé un nouvel onglet dans le gui "RFEM" qui liste les structures — les éléments, nœud, schémas statiques, combinaisons de charges par structure», «dans le groupe structure, au-dessus de modèles statiques. Faire un volet vertical à gauche dans ce groupe qui liste les éléments de RFEM (la première fois, il faut manuellement indiquer le chemin vers le fichier rfem). Il est possible d'importer plusieurs modèles rfem».

So: a **vertical pane on the left** listing the RFEM models this project reads and, under each, its structures; on the right what the selected structure is made of. Several models per project, each added by pointing at its export the first time and remembered in the project file (`project.rfem_models`, `gui.rfem_models`) — so a path is stated once and never again.

**It holds no RFEM logic of its own.** Every fact on screen comes from `calc/rfem_import/`: `model_tables.read_model` reads the export, `structure_detection.detect` groups it, `metadata_parser` reads the comments. The window shows and never decides — the rule the loads tab follows for `data/calculations.json` (§10quater), applied to a seventh editor. Nothing here writes into the project but the list of paths.

⚠️ **What it reads is an export, not the `.rf6`.** RFEM's own *Fichier → Exporter → Tableaux* writes either one XLSX of every table or one CSV per table, and this tab takes either; the model file itself is a ZIP of a SQLite database and proprietary result blobs, which nothing here opens. That is the decision the whole import rests on (§14): the exported file is the contract, and the gRPC API — which needs a Dlubal key not every office has — is an optional accelerator.

⚠️ **A structure nobody named is listed and cannot be addressed.** 21 of the engineer's 22 are in that state, which is not a defect: RFEM connects by node, and one static system per element in one file is how a timber engineer works. The tab says so where it lists them and offers the comment to write — `@model "<name>"` in one of the structure's members — since that is the one thing the model cannot tell.
"""

import os
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtGui import QCursor
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import (
    QAbstractItemView, QApplication, QComboBox, QFileDialog, QFormLayout, QHBoxLayout, QHeaderView, QLabel,
    QMessageBox, QPushButton, QSplitter, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)

import cards          # the panels in cards, after the website (cards.py, v0.93)
import project        # where the project this tab works on is (calc/project.py)
import theme          # the colours this tab states itself (theme.py, v0.90)
import notifications  # every error, warning and information, gathered in one place (calc/notifications.py, v0.117)
import notices_ui  # what was a message box is a notice since v0.117 (notices_ui.tell)
from rfem_import import diagram_svg, envelopes, model_tables, results, structure_detection
from rfem_import.csv_tables import RfemCsvError

# What the figure's first selector offers: the system alone, then the six internal forces, in RFEM's own
# order. The system is `None` -- a figure with no diagram over it -- rather than a seventh quantity, so that
# `diagram_svg.render` is given a key or nothing and never a word it has to test for.
QUANTITIES = (None, "N", "V_y", "V_z", "M_T", "M_y", "M_z")

# The keys carry an `rf_` prefix of their own, for the reason the commands tab's carry `ref_`: a key defined in two tab modules would be silently taken by whichever merged last, which woodcore_gui's own check cannot see.
STRINGS = {
    "fr": {
        "tab_rfem": "RFEM",
        "rf_models": "Modèles RFEM",
        "rf_add": "Ajouter un modèle…",
        "rf_reload": "Relire",
        "rf_remove": "Retirer de la liste",
        "rf_none": "Aucun modèle RFEM.\n\nAjoutez l'export des tableaux que RFEM écrit\n(Fichier → Exporter → Tableaux),\nen un classeur .xlsx ou en un dossier de .csv.",
        "rf_pick": "Choisir l'export des tableaux RFEM",
        "rf_pick_filter": "Export RFEM (*.xlsx);;Tous les fichiers (*)",
        "rf_pick_folder": "Choisir un dossier de tableaux .csv",
        "rf_or_folder": "Un dossier de .csv…",
        "rf_gone": "introuvable",
        "rf_unreadable": "illisible",
        "rf_structures": "structures",
        "rf_unnamed": "sans nom",
        "rf_structure": "Structure",
        "rf_name": "Nom",
        "rf_statics_name": "Nom du modèle statique",
        "rf_statics_descr": "Description",
        "rf_contents": "Contenu",
        "rf_members": "Barres",
        "rf_surfaces": "Panneaux",
        "rf_nodes": "Nœuds",
        "rf_supports": "Appuis",
        "rf_loads": "Charges",
        "rf_cases": "Cas de charge",
        "rf_combinations": "Combinaisons",
        "rf_positions": "Positions",
        "rf_sections": "Sections",
        "rf_problems": "Avertissements",
        "rf_model_of": "Modèle",
        "rf_read_in": "lu en %.1f s",
        "rf_write_name": "Pour nommer cette structure, écrivez dans le commentaire d'une de ses barres, dans RFEM :",
        "rf_no_selection": "Choisissez une structure dans le volet de gauche.",
        "rf_remove_title": "Retirer ce modèle ?",
        "rf_remove_text": "Retirer « %s » de la liste des modèles RFEM de ce projet ?\n\nLe fichier exporté n'est pas supprimé.",
        "rf_read_only": "Projet ouvert en lecture seule : la liste des modèles ne peut pas être modifiée.",
        "rf_needs_model": "Ajoutez d'abord un modèle RFEM : l'export des tableaux que RFEM écrit.",
        "rf_orphans": "objets rattachés à aucune structure",
        "rf_no_position": "aucune",
        'rf_figure': 'Figure',
        'rf_quantity': 'Grandeur',
        'rf_system': 'Système',
        'rf_loading': 'Chargement',
        'rf_reading': 'Lecture des efforts de %s…',
        'rf_no_results': "Cet export ne porte pas d'efforts pour ce chargement.",
        'rf_pick_loading': 'Choisissez un chargement pour voir la courbe.',
        'rf_situation_band': "Une situation de projet est une enveloppe : elle porte les extrêmes et "
                             "non un tracé. Choisissez une combinaison (CO…) pour voir la courbe ; les "
                             "extrêmes de %s se lisent avec #rfem-max.",
        'rf_pick_structure': "Choisissez une structure sous ce modèle pour voir son système et ses efforts.",
        'rf_to_statics': "Ajouter aux modèles statiques",
        'rf_to_statics_tip': "Écrit la présentation de cette structure — la grandeur, le chargement et les "
                             "épaisseurs choisis — et réexporte, afin que le rapport puisse l'imprimer.",
        'rf_view_written': "« %s » est présenté dans les modèles statiques.",
        'rf_view_failed': "La présentation n'a pas pu être écrite : %s",
        'rf_combinations_card': 'Combinaisons',
        'rf_situation': 'Situation',
        'rf_all': 'Toutes',
        'rf_formula': 'Formule',
        'rf_duration': 'Durée de charge',
    },
    "de": {
        "tab_rfem": "RFEM",
        "rf_models": "RFEM-Modelle",
        "rf_add": "Modell hinzufügen…",
        "rf_reload": "Neu lesen",
        "rf_remove": "Aus der Liste entfernen",
        "rf_none": "Kein RFEM-Modell.\n\nFügen Sie den Tabellenexport hinzu, den RFEM schreibt\n(Datei → Exportieren → Tabellen),\nals .xlsx-Arbeitsmappe oder als Ordner mit .csv.",
        "rf_pick": "RFEM-Tabellenexport wählen",
        "rf_pick_filter": "RFEM-Export (*.xlsx);;Alle Dateien (*)",
        "rf_pick_folder": "Ordner mit .csv-Tabellen wählen",
        "rf_or_folder": "Ein Ordner mit .csv…",
        "rf_gone": "nicht gefunden",
        "rf_unreadable": "nicht lesbar",
        "rf_structures": "Tragwerke",
        "rf_unnamed": "ohne Namen",
        "rf_structure": "Tragwerk",
        "rf_name": "Name",
        "rf_statics_name": "Name des statischen Systems",
        "rf_statics_descr": "Beschreibung",
        "rf_contents": "Inhalt",
        "rf_members": "Stäbe",
        "rf_surfaces": "Flächen",
        "rf_nodes": "Knoten",
        "rf_supports": "Lager",
        "rf_loads": "Lasten",
        "rf_cases": "Lastfälle",
        "rf_combinations": "Kombinationen",
        "rf_positions": "Positionen",
        "rf_sections": "Querschnitte",
        "rf_problems": "Hinweise",
        "rf_model_of": "Modell",
        "rf_read_in": "gelesen in %.1f s",
        "rf_write_name": "Um dieses Tragwerk zu benennen, schreiben Sie in RFEM in den Kommentar eines seiner Stäbe:",
        "rf_no_selection": "Wählen Sie links ein Tragwerk.",
        "rf_remove_title": "Modell entfernen?",
        "rf_remove_text": "«%s» aus der Liste der RFEM-Modelle dieses Projekts entfernen?\n\nDie exportierte Datei wird nicht gelöscht.",
        "rf_read_only": "Projekt schreibgeschützt geöffnet: die Modellliste kann nicht geändert werden.",
        "rf_needs_model": "Fügen Sie zuerst ein RFEM-Modell hinzu: den Tabellenexport, den RFEM schreibt.",
        "rf_orphans": "Objekte, die zu keinem Tragwerk gehören",
        "rf_no_position": "keine",
        'rf_figure': 'Abbildung',
        'rf_quantity': 'Grösse',
        'rf_system': 'System',
        'rf_loading': 'Belastung',
        'rf_reading': 'Schnittgrössen von %s werden gelesen…',
        'rf_no_results': 'Dieser Export enthält für diese Belastung keine Schnittgrössen.',
        'rf_pick_loading': 'Wählen Sie eine Belastung, um den Verlauf zu sehen.',
        'rf_situation_band': 'Eine Bemessungssituation ist eine Hüllkurve: sie trägt die Extremwerte und '
                             'keinen Verlauf. Wählen Sie eine Kombination (CO…), um den Verlauf zu sehen; '
                             'die Extremwerte von %s liest #rfem-max.',
        'rf_pick_structure': 'Wählen Sie unter diesem Modell ein Tragwerk, um sein System und seine '
                             'Schnittgrössen zu sehen.',
        'rf_to_statics': 'Zu den statischen Systemen hinzufügen',
        'rf_to_statics_tip': 'Schreibt die Darstellung dieses Tragwerks — die gewählte Grösse, Belastung und '
                             'Strichstärke — und exportiert neu, damit der Bericht sie drucken kann.',
        'rf_view_written': '«%s» wird in den statischen Systemen dargestellt.',
        'rf_view_failed': 'Die Darstellung konnte nicht geschrieben werden: %s',
        'rf_combinations_card': 'Kombinationen',
        'rf_situation': 'Situation',
        'rf_all': 'Alle',
        'rf_formula': 'Formel',
        'rf_duration': 'Lasteinwirkungsdauer',
    },
    "en": {
        "tab_rfem": "RFEM",
        "rf_models": "RFEM models",
        "rf_add": "Add a model…",
        "rf_reload": "Read again",
        "rf_remove": "Remove from the list",
        "rf_none": "No RFEM model.\n\nAdd the table export RFEM writes\n(File → Export → Tables),\nas one .xlsx workbook or as a folder of .csv.",
        "rf_pick": "Choose the RFEM table export",
        "rf_pick_filter": "RFEM export (*.xlsx);;All files (*)",
        "rf_pick_folder": "Choose a folder of .csv tables",
        "rf_or_folder": "A folder of .csv…",
        "rf_gone": "not found",
        "rf_unreadable": "not readable",
        "rf_structures": "structures",
        "rf_unnamed": "unnamed",
        "rf_structure": "Structure",
        "rf_name": "Name",
        "rf_statics_name": "Static model's name",
        "rf_statics_descr": "Description",
        "rf_contents": "Contents",
        "rf_members": "Members",
        "rf_surfaces": "Surfaces",
        "rf_nodes": "Nodes",
        "rf_supports": "Supports",
        "rf_loads": "Loads",
        "rf_cases": "Load cases",
        "rf_combinations": "Combinations",
        "rf_positions": "Positions",
        "rf_sections": "Sections",
        "rf_problems": "Warnings",
        "rf_model_of": "Model",
        "rf_read_in": "read in %.1f s",
        "rf_write_name": "To name this structure, write in the comment of one of its members, in RFEM:",
        "rf_no_selection": "Choose a structure in the pane at the left.",
        "rf_remove_title": "Remove this model?",
        "rf_remove_text": "Remove «%s» from this project's list of RFEM models?\n\nThe exported file is not deleted.",
        "rf_read_only": "Project opened read-only: the list of models cannot be changed.",
        "rf_needs_model": "Add an RFEM model first: the table export RFEM writes.",
        "rf_orphans": "objects belonging to no structure",
        "rf_no_position": "none",
        'rf_figure': 'Figure',
        'rf_quantity': 'Quantity',
        'rf_system': 'System',
        'rf_loading': 'Loading',
        'rf_reading': 'Reading the internal forces of %s…',
        'rf_no_results': 'This export carries no internal forces for that loading.',
        'rf_pick_loading': 'Choose a loading to see the diagram.',
        'rf_situation_band': 'A design situation is an envelope: it carries the extremes and no '
                             'distribution. Choose a combination (CO…) to see the diagram; the extremes '
                             'of %s are read with #rfem-max.',
        'rf_pick_structure': 'Choose a structure under this model to see its system and its internal forces.',
        'rf_to_statics': 'Add to the static models',
        'rf_to_statics_tip': "Writes this structure's presentation — the quantity, the loading and the line "
                             'weights chosen — and exports again, so the report can print it.',
        'rf_view_written': '«%s» is presented in the static models.',
        'rf_view_failed': 'The presentation could not be written: %s',
        'rf_combinations_card': 'Combinations',
        'rf_situation': 'Situation',
        'rf_all': 'All',
        'rf_formula': 'Formula',
        'rf_duration': 'Load duration',
    },
}


def clear(layout):
    """Empties a layout of the widgets a refill replaces.

    ⚠️ **A `QFormLayout` is emptied row by row and not item by item.** `takeAt` removes an item and leaves the row it was in, so a card refilled ten times carried ten blank rows above its real ones — measured on the engineer's own export, eleven empty lines over «Barres : 24–29». `removeRow` takes the row, its label and its field together.

    ⚠️ **Hidden before it is detached.** A widget detached while shown is a top-level window and Qt shows it as one — the white windows that flashed each time the connectors tab rebuilt its rows (docs/ui/window.md §10quater, v0.77).
    """
    if isinstance(layout, QFormLayout):
        for row in reversed(range(layout.rowCount())):
            for role in (QFormLayout.ItemRole.LabelRole, QFormLayout.ItemRole.FieldRole):
                item = layout.itemAt(row, role)
                widget = item.widget() if item is not None else None
                if widget is not None:
                    widget.hide()
            layout.removeRow(row)
        return
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
            widget.hide()
            widget.setParent(None)
            widget.deleteLater()


class Export:
    """One RFEM table export this project reads: its path, the model it holds, the structures detected in it, and why it could not be read.

    Read when the tab is built and when «Relire» is pressed, never on a timer: an export is a file the engineer produced deliberately, and re-reading it behind his back would make the list change under his hand.
    """

    __slots__ = ("named", "path", "model", "structures", "error", "seconds", "_loadings", "forces")

    def __init__(self, named, path):
        self.named, self.path = named, Path(path)
        self.model, self.structures, self.error, self.seconds = None, None, None, 0.0
        self._loadings, self.forces = None, {}

    def loadings(self):
        """The loadings this export carries member forces for, read once and kept.

        ⚠️ Resolved from the **sheet names alone** (`results.loadings_in`), which costs no reading: 2.3 s on the
        engineer's 490-sheet export against 105 s to read every one of them.
        """
        if self._loadings is None:
            try:
                self._loadings = results.loadings_in(self.path) if self.path.exists() else []
            except (RfemCsvError, OSError, ValueError):
                self._loadings = []
        return self._loadings

    def table(self, loading):
        """The member forces of one loading, read on the first ask and kept -- the engineer's «à la demande, par structure»."""
        if loading not in self.forces:
            try:
                self.forces[loading] = results.read_loading(self.path, loading)
            except (RfemCsvError, OSError, ValueError):
                self.forces[loading] = None
        return self.forces[loading]

    @property
    def label(self):
        return self.path.name or str(self.path)

    def read(self):
        """Reads the export, or records why it could not be. Never raises: a path that is gone is a line in the list and not a window that will not open."""
        import time

        self.model, self.structures, self.error, self.seconds = None, None, None, 0.0
        self._loadings, self.forces = None, {}
        if not self.path.exists():
            self.error = "gone"
            return self
        start = time.time()
        try:
            self.model = model_tables.read_model(self.path)
            self.structures = structure_detection.detect(
                self.model.items(), combinations=self.model.combination_cases())
        except (RfemCsvError, OSError, ValueError) as exc:
            self.error = str(exc)
        self.seconds = time.time() - start
        return self


class RfemTab(QWidget):
    """Lists the RFEM exports this project reads and, per export, the structures detected in it."""

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.t = app.t
        self.exports = []
        self.current = None          # (export, structure) or (export, None) for a model's own row
        self.quantity = "M_y"        # what the figure draws; None is the bare system
        self.loading = None          # which loading it draws it for
        # ⚠️ Whether a *hand* has picked a loading, which is not the same as `loading is not None`: the
        # first structure looked at defaults to one so that the figure draws by itself, and «—» must stay
        # picked once it is picked, or it could never be chosen at all.
        self.loading_chosen = False
        self.situations = set()      # the SP ids of the export in hand: they have extremes and no curve
        self.filling = False         # true while the selectors are refilled, so their signals draw nothing

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.addWidget(self.build_list())
        self.splitter.addWidget(self.build_detail())
        self.splitter.setStretchFactor(0, 2)
        self.splitter.setStretchFactor(1, 3)
        layout.addWidget(self.splitter, 1)
        self.read_exports()
        self.restore(app.views.get("tab_rfem"))

    # -- building ----------------------------------------------------------------------

    def build_list(self):
        """The vertical pane at the left: the models, and under each its structures."""
        pane = QWidget()
        box = QVBoxLayout(pane)
        box.setContentsMargins(0, 0, 0, 0)

        title = QLabel(self.t("rf_models"))
        title.setFont(self.app.bold_font)
        box.addWidget(title)

        self.tree = QTreeWidget()
        self.tree.setColumnCount(2)
        self.tree.setHeaderHidden(True)
        self.tree.setRootIsDecorated(True)
        self.tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.tree.currentItemChanged.connect(self.on_selected)
        box.addWidget(self.tree, 1)

        self.empty = QLabel(self.t("rf_none"))
        self.empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty.setWordWrap(True)
        self.empty.setStyleSheet(f"color: {theme.colour('muted')};")
        box.addWidget(self.empty, 1)

        buttons = QHBoxLayout()
        self.add_button = QPushButton(self.t("rf_add"))
        self.add_button.clicked.connect(self.add_model)
        # The dialog's two formats are two buttons, not one dialog the engineer has to cancel to reach the other: *Fichier → Exporter → Tableaux* writes either one workbook or a folder of CSVs, and which he has is a fact he knows before he clicks.
        self.folder_button = QPushButton(self.t("rf_or_folder"))
        self.folder_button.clicked.connect(lambda: self.add_model(folder=True))
        self.reload_button = QPushButton(self.t("rf_reload"))
        self.reload_button.clicked.connect(self.reload)
        self.remove_button = QPushButton(self.t("rf_remove"))
        self.remove_button.clicked.connect(self.remove_model)
        for button in (self.add_button, self.folder_button, self.reload_button, self.remove_button):
            buttons.addWidget(button)
        buttons.addStretch(1)
        box.addLayout(buttons)
        return pane

    def build_detail(self):
        """The pane at the right: the structure's figure, what it is made of, its combinations and its problems, in a column of cards (cards.py, v0.93)."""
        scroll, column = cards.column()
        self.figure = self.build_figure()
        self.combinations = self.build_combinations()
        self.identity = cards.card(self.t("rf_structure"))
        self.identity_form = cards.form(self.identity)
        self.contents = cards.card(self.t("rf_contents"))
        self.contents_form = cards.form(self.contents)
        self.problems = cards.card(self.t("rf_problems"))
        self.problems_box = QVBoxLayout(self.problems)
        self.hint = cards.note(self.t("rf_no_selection"))
        for widget in (self.figure, self.identity, self.contents, self.combinations,
                       self.problems, self.hint):
            column.addWidget(widget)
        column.addStretch(1)
        return scroll

    def build_figure(self):
        """The figure and its selector: one drawing, and above it what is drawn and for which loading.

        The engineer's own shape -- «une figure avec un sélecteur» -- rather than one figure per quantity stacked:
        a diagram is read against the system it sits on, and three of them one under the other give each a third
        of the height.
        """
        card = cards.card(self.t("rf_figure"))
        box = QVBoxLayout(card)
        row = QHBoxLayout()
        self.quantity_box = QComboBox()
        for key in QUANTITIES:
            self.quantity_box.addItem(self.t("rf_system") if key is None else key, key)
        self.quantity_box.setCurrentIndex(QUANTITIES.index(self.quantity))
        self.quantity_box.currentIndexChanged.connect(self.on_selector)
        self.loading_box = QComboBox()
        self.loading_box.currentIndexChanged.connect(self.on_selector)
        row.addWidget(QLabel(self.t("rf_quantity")))
        row.addWidget(self.quantity_box)
        row.addSpacing(12)
        row.addWidget(QLabel(self.t("rf_loading")))
        row.addWidget(self.loading_box, 1)
        box.addLayout(row)
        self.view = QSvgWidget()
        self.view.setMinimumHeight(320)
        box.addWidget(self.view, 1)
        self.figure_note = cards.note("")
        box.addWidget(self.figure_note)
        # ⚠️ The one door of `statics_view.py`: nothing else in Woodcore writes a view. It keeps what is on
        # screen -- the quantity, the loading -- so that the report prints the figure the engineer chose.
        self.to_statics = QPushButton(self.t("rf_to_statics"))
        self.to_statics.setToolTip(self.t("rf_to_statics_tip"))
        self.to_statics.clicked.connect(self.add_to_statics)
        under = QHBoxLayout()
        under.addStretch(1)
        under.addWidget(self.to_statics)
        box.addLayout(under)
        return card

    def build_combinations(self):
        """Every combination of the export, with its formula, its design situation and its load duration, filtered by situation.

        ⚠️ **The load duration is why this card carries more than the formula**: SIA 265 reads the strengths at the
        duration of the governing action, and RFEM states it per combination -- «Permanente», «Court terme» -- so
        the one place a report can take it from is here (`model_tables.Combination`).
        """
        card = cards.card(self.t("rf_combinations_card"))
        box = QVBoxLayout(card)
        row = QHBoxLayout()
        self.situation_box = QComboBox()
        self.situation_box.currentIndexChanged.connect(lambda *_: self.fill_combinations())
        row.addWidget(QLabel(self.t("rf_situation")))
        row.addWidget(self.situation_box, 1)
        box.addLayout(row)
        self.combination_list = QTreeWidget()
        self.combination_list.setColumnCount(3)
        self.combination_list.setHeaderLabels(["", self.t("rf_formula"), self.t("rf_duration")])
        self.combination_list.setRootIsDecorated(False)
        self.combination_list.setMinimumHeight(150)
        self.combination_list.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        box.addWidget(self.combination_list)
        return card

    # -- reading -----------------------------------------------------------------------

    def read_exports(self):
        """Reads every export the project names. The paths are the project file's, so this is what «the first time, point at the file» buys: every time after the first, nothing is asked."""
        here = project.current()
        self.exports = [Export(named, path).read()
                        for named, path in zip(here.rfem_models(), here.rfem_model_paths())]
        self.fill_tree()

    def reload(self):
        keep = self.selected_keys()
        self.read_exports()
        self.select_keys(keep)

    # -- the list ----------------------------------------------------------------------

    def fill_tree(self):
        self.tree.clear()
        for export in self.exports:
            item = QTreeWidgetItem([export.label, ""])
            item.setData(0, Qt.ItemDataRole.UserRole, (export, None))
            item.setFont(0, self.app.bold_font)
            if export.error == "gone":
                item.setText(1, self.t("rf_gone"))
                item.setForeground(1, QColor(theme.colour("danger-soft")))
            elif export.error:
                item.setText(1, self.t("rf_unreadable"))
            elif export.structures is not None:
                item.setText(1, f"{len(export.structures)} {self.t('rf_structures')}")
                for structure in export.structures:
                    child = QTreeWidgetItem([
                        structure.name or structure.key,
                        f"{len(structure.members)} {self.t('rf_members').lower()}",
                    ])
                    child.setData(0, Qt.ItemDataRole.UserRole, (export, structure))
                    if not structure.named:
                        child.setToolTip(0, self.t("rf_unnamed"))
                        child.setForeground(0, self.tree.palette().brush(
                            self.tree.foregroundRole()))
                    item.addChild(child)
            self.tree.addTopLevelItem(item)
            item.setExpanded(True)
        self.tree.setVisible(bool(self.exports))
        self.empty.setVisible(not self.exports)
        # ⚠️ A button shown disabled with nothing to say why cannot be told from a broken one (docs/ui/window.md §10quater, v0.47's rule and the periodic audit's AUD-5-6) -- so each says what would make it usable.
        for button in (self.reload_button, self.remove_button):
            button.setEnabled(bool(self.exports))
            button.setToolTip("" if self.exports else self.t("rf_needs_model"))
        if self.exports and self.tree.topLevelItemCount():
            self.tree.setCurrentItem(self.tree.topLevelItem(0))

    def selected_keys(self):
        """What is selected, as names rather than objects, so it survives a re-read."""
        if not self.current:
            return None, None
        export, structure = self.current
        return export.named, (structure.key if structure else None)

    def select_keys(self, keys):
        named, key = keys
        for index in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(index)
            export, _ = item.data(0, Qt.ItemDataRole.UserRole)
            if export.named != named:
                continue
            if key is None:
                self.tree.setCurrentItem(item)
                return
            for child_index in range(item.childCount()):
                child = item.child(child_index)
                _, structure = child.data(0, Qt.ItemDataRole.UserRole)
                if structure is not None and structure.key == key:
                    self.tree.setCurrentItem(child)
                    return
            self.tree.setCurrentItem(item)
            return

    def on_selected(self, item, _previous=None):
        self.current = item.data(0, Qt.ItemDataRole.UserRole) if item is not None else None
        self.fill_detail()

    # -- the detail --------------------------------------------------------------------

    def fill_detail(self):
        for layout in (self.identity_form, self.contents_form, self.problems_box):
            clear(layout)

        if not self.current:
            self.hint.setVisible(True)
            for card in (self.figure, self.identity, self.contents, self.combinations, self.problems):
                card.setVisible(False)
            return
        self.hint.setVisible(False)
        export, structure = self.current
        self.refill_selectors(export)
        self.combinations.setVisible(bool(export.model and export.model.combinations))
        self.fill_combinations()
        if structure is None:
            self.figure.setVisible(False)
            self.fill_model(export)
        else:
            self.figure.setVisible(True)
            self.fill_structure(export, structure)
            self.fill_figure()

    def row(self, form, key, text):
        """One «label value» row of a card, the value selectable so a list of member numbers can be copied out."""
        value = QLabel(str(text))
        value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        value.setWordWrap(True)
        form.addRow(self.app.label(key), value)

    def fill_model(self, export):
        """A model's own row: what the export holds, and what could not be read of it."""
        self.identity.setVisible(True)
        self.identity.setTitle(self.t("rf_model_of"))
        self.row(self.identity_form, "rf_name", export.label)
        self.row(self.identity_form, "rf_contents", str(export.path))
        if export.error == "gone":
            self.row(self.identity_form, "rf_gone", str(export.path))
            self.contents.setVisible(False)
            self.problems.setVisible(False)
            return
        if export.error:
            self.contents.setVisible(False)
            self.problems.setVisible(True)
            self.problems_box.addWidget(cards.note(export.error))
            return

        model, found = export.model, export.structures
        self.contents.setVisible(True)
        self.contents.setTitle(self.t("rf_contents"))
        self.row(self.contents_form, "rf_structures", len(found))
        self.row(self.contents_form, "rf_members", len(model.members))
        self.row(self.contents_form, "rf_surfaces", len(model.surfaces))
        self.row(self.contents_form, "rf_nodes", len(model.nodes))
        self.row(self.contents_form, "rf_sections", len(model.sections))
        self.row(self.contents_form, "rf_supports", len(model.supports))
        self.row(self.contents_form, "rf_cases", ", ".join(case.id for case in model.cases) or "—")
        self.row(self.contents_form, "rf_combinations", len(model.combinations))
        self.row(self.contents_form, "rf_loads", len(model.loads))
        self.row(self.contents_form, "rf_orphans", len(found.orphans))
        self.contents_form.addRow("", cards.note(self.t("rf_read_in") % export.seconds))
        # The figure belongs to a structure, so this row has none -- and a card that is simply hidden says
        # nothing. «Les efforts internes ne s'affichent pas» was, among three causes, this one.
        self.contents_form.addRow("", cards.note(self.t("rf_pick_structure")))
        self.show_problems(list(model.problems) + list(found.problems))

    def fill_structure(self, export, structure):
        """One structure: what the engineer called it, what it is made of, and which loadings act on it."""
        self.identity.setVisible(True)
        self.identity.setTitle(self.t("rf_structure"))
        self.row(self.identity_form, "rf_name", structure.name or f"({self.t('rf_unnamed')})")
        self.row(self.identity_form, "rf_statics_name", structure.statics_name or "—")
        self.row(self.identity_form, "rf_statics_descr", structure.statics_descr or "—")
        if not structure.named:
            self.identity_form.addRow("", cards.note(self.t("rf_write_name")))
            self.identity_form.addRow("", cards.note('@model "…"'))

        self.contents.setVisible(True)
        self.contents.setTitle(self.t("rf_contents"))
        self.row(self.contents_form, "rf_members", self.numbers(structure.numbers("member")))
        if structure.surfaces:
            self.row(self.contents_form, "rf_surfaces", self.numbers(structure.numbers("surface")))
        self.row(self.contents_form, "rf_nodes", self.numbers(structure.nodes))
        self.row(self.contents_form, "rf_supports", self.numbers(structure.numbers("support")) or "—")
        self.row(self.contents_form, "rf_loads", len(structure.loads))
        self.row(self.contents_form, "rf_cases", ", ".join(str(case) for case in structure.cases) or "—")
        self.row(self.contents_form, "rf_combinations",
                 f"{len(structure.combinations)} — {', '.join(str(c) for c in structure.combinations[:8])}"
                 + (" …" if len(structure.combinations) > 8 else "") if structure.combinations else "—")
        positions = structure.positions
        self.row(self.contents_form, "rf_positions",
                 ", ".join(f"{name} ({', '.join(item.where for item in carriers)})"
                           for name, carriers in sorted(positions.items())) or self.t("rf_no_position"))
        sections = sorted({(section.name, section.b, section.h) for section in (
            export.model.section_of(member) for member in export.model.members
            if member.no in set(structure.numbers("member"))) if section is not None})
        self.row(self.contents_form, "rf_sections",
                 ", ".join(name for name, _b, _h in sections) or "—")
        self.show_problems(list(structure.problems))

    def refill_selectors(self, export):
        """The loadings this export carries, and the design situations its combinations fall into.

        ⚠️ Refilled with `filling` set, because a `QComboBox` emits `currentIndexChanged` as it is filled and each
        of those would draw a figure -- and the first draw of a loading reads a sheet. The flag is the plan tab's
        own guard against a signal fired by code rather than by a hand.
        """
        self.filling = True
        try:
            situations = sorted({c.situation for c in (export.model.combinations if export.model else []) if c.situation})
            # ⚠️ The situation's **id** and not the whole text: a combination states «SP1 - ELU Type 2 -
            # Fondamental» where the sheet a result table is named after is «SP1» -- and it is the id the
            # loading box offers. Read by the one function that already knows that shape.
            self.situations = {envelopes.situation_of(text)[0] for text in situations}
            wanted = self.loading
            self.loading_box.clear()
            self.loading_box.addItem("—", None)
            for loading in export.loadings():
                self.loading_box.addItem(loading, loading)
            if wanted is None and not self.loading_chosen:
                # The first structure looked at draws its forces and not its bare system. ⚠️ A design
                # situation is stepped over: it is an envelope and has no curve at all (below).
                wanted = next((l for l in export.loadings() if l not in self.situations), None)
            index = self.loading_box.findData(wanted)
            self.loading_box.setCurrentIndex(index if index >= 0 else 0)
            self.loading = self.loading_box.currentData()

            keep = self.situation_box.currentData()
            self.situation_box.clear()
            self.situation_box.addItem(self.t("rf_all"), None)
            for situation in situations:
                self.situation_box.addItem(situation, situation)
            index = self.situation_box.findData(keep)
            self.situation_box.setCurrentIndex(index if index >= 0 else 0)
        finally:
            self.filling = False

    def on_selector(self, *_):
        """A quantity or a loading chosen: what is drawn changes, and the sheet behind it is read on the first ask."""
        if self.filling:
            return
        self.quantity = self.quantity_box.currentData()
        self.loading = self.loading_box.currentData()
        self.loading_chosen = True
        self.fill_figure()

    def forces_of(self, export, loading):
        """The member forces of one loading, with the window saying it is reading them.

        ⚠️ **One sheet, not the workbook**: 1.4 s against 105 s (`results.read_loading`). It is still long enough
        to be seen, so the cursor waits and the status line names the loading -- the engineer's «une barre de
        chargement doit apparaître afin que le user sache ce qu'il se passe», in the one form a read this short
        deserves.
        """
        if loading is None:
            return None
        if loading in export.forces:
            return export.forces[loading]
        self.app.set_status(self.t("rf_reading") % loading)
        QApplication.setOverrideCursor(QCursor(Qt.CursorShape.BusyCursor))
        QApplication.processEvents()
        try:
            return export.table(loading)
        finally:
            QApplication.restoreOverrideCursor()
            self.app.set_status("")

    def fill_figure(self):
        """Draws the selected structure: its system, and over it the chosen quantity for the chosen loading."""
        if not self.current:
            return
        export, structure = self.current
        if structure is None or export.model is None:
            self.figure.setVisible(False)
            return
        table = self.forces_of(export, self.loading) if self.quantity else None
        note = ""
        if self.quantity and self.loading is None:
            note = self.t("rf_pick_loading")
        elif self.quantity and self.loading in self.situations:
            # ⚠️ Not «this export carries no internal forces»: SP1 is the very table the extremes are read
            # from (`envelopes.py`). What it has not got is a *distribution* -- an envelope is a band, which
            # is docs/open-questions.md §14's -- so the note says which command prints what it does carry.
            note = self.t("rf_situation_band") % self.loading
        elif self.quantity and table is None:
            note = self.t("rf_no_results")
        caption = None
        if self.quantity and table is not None:
            caption = "%s · %s · %s [%s]" % (structure.name or structure.key, self.loading,
                                             self.quantity, diagram_svg.UNITS.get(self.quantity, ""))
        svg = diagram_svg.render(export.model, structure, table, self.quantity or "M_y",
                                 labels=bool(self.quantity), caption=caption)
        self.view.load(svg.encode("utf-8"))
        self.figure_note.setText(note)
        self.figure_note.setVisible(bool(note))

    def add_to_statics(self):
        """This structure presented in «Modèles statiques»: its view written, and the project exported again.

        ⚠️ **It writes a view and never a model.** An imported model stays generated and RFEM stays its source
        (§3.3duodecies) -- a drawing the engineer did not draw has no business in the folder he draws in. What
        is his of it is its *presentation*, which is the whole of `statics_view.py`, and this button is its one
        door: what is kept is what he is looking at, the quantity and the loading.
        """
        if not self.current:
            return
        export, structure = self.current
        if structure is None:
            return
        # Imported late and not at the top: `import_controller` reaches the whole domain chain, and this module
        # is meant to be readable from `rfem_import` alone (the file's own header).
        from domains import statics_view
        from rfem_import import import_controller

        sid = import_controller.model_id(structure)
        view = statics_view.default()
        if self.quantity and self.loading and self.loading not in self.situations:
            view["diagram"] = {"quantity": self.quantity, "loading": self.loading}
        try:
            statics_view.write(project.current().statics_dir, sid, view)
        except Exception as exc:                      # a defective view, a folder that cannot be written
            notices_ui.tell(self.t("rf_view_failed") % exc, notifications.CRITICAL, exc=exc, source="rfem_tab")
            return
        self.app.set_status(self.t("rf_view_written") % sid)
        self.app.reexport()

    def fill_combinations(self):
        """Every combination of the export, filtered by the design situation chosen."""
        self.combination_list.clear()
        if not self.current:
            return
        export, _structure = self.current
        if export.model is None:
            return
        wanted = self.situation_box.currentData()
        for combination in export.model.combinations:
            if wanted and combination.situation != wanted:
                continue
            item = QTreeWidgetItem([combination.id, combination.name, combination.duration or "—"])
            item.setToolTip(1, "%s\n%s" % (combination.name, combination.situation))
            self.combination_list.addTopLevelItem(item)
        self.combination_list.resizeColumnToContents(0)

    def show_problems(self, notes):
        self.problems.setVisible(bool(notes))
        self.problems.setTitle(f"{self.t('rf_problems')} ({len(notes)})")
        for note in notes[:12]:
            self.problems_box.addWidget(cards.note(self.app.note_text(note) if hasattr(self.app, "note_text") else str(note)))
        if len(notes) > 12:
            self.problems_box.addWidget(cards.note("…"))

    @staticmethod
    def numbers(values):
        """«24–29» for a run, «1, 3, 13» otherwise -- the form `show-polar-moment` names a run of fasteners with."""
        values = sorted(values)
        if not values:
            return "—"
        if len(values) > 2 and values == list(range(values[0], values[-1] + 1)):
            return f"{values[0]}–{values[-1]} ({len(values)})"
        shown = ", ".join(str(value) for value in values[:14])
        return shown + (f" … ({len(values)})" if len(values) > 14 else "")

    # -- the list of models ------------------------------------------------------------

    def add_model(self, folder=False):
        """Points at an export: one XLSX, or a folder of CSVs. The path is written into the project file, so it is asked once — «la première fois, il faut manuellement indiquer le chemin»."""
        if not self.writable():
            return
        here = project.current()
        if folder:
            path = QFileDialog.getExistingDirectory(self, self.t("rf_pick_folder"), str(here.root))
        else:
            path, _ = QFileDialog.getOpenFileName(self, self.t("rf_pick"), str(here.root), self.t("rf_pick_filter"))
        if not path:
            return
        paths = list(here.rfem_model_paths()) + [Path(path)]
        project.set_rfem_models(here, paths)
        self.read_exports()
        self.app.set_status(f"{self.t('rf_add')} {os.path.basename(path)}")

    def remove_model(self):
        if not self.writable() or not self.current:
            return
        export, _ = self.current
        answer = QMessageBox.question(
            self, self.t("rf_remove_title"), self.t("rf_remove_text") % export.label,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if answer != QMessageBox.StandardButton.Yes:
            return
        here = project.current()
        kept = [path for path in here.rfem_model_paths() if Path(path) != export.path]
        project.set_rfem_models(here, kept)
        self.read_exports()

    def writable(self):
        """False, with a word, where the project is open read-only -- the guard every editor tab applies (docs/ui/window.md §10quater)."""
        if getattr(self.app, "read_only", False):
            self.app.set_status(self.t("rf_read_only"))
            return False
        return True

    # -- the window's own hooks --------------------------------------------------------

    def on_shown(self):
        """Brought to the front: nothing is re-read. An export is a file the engineer produced deliberately, and «Relire» is the one thing that reads it again."""

    def set_language(self, _lang=None):
        self.rebuild_texts()

    def rebuild_texts(self):
        self.add_button.setText(self.t("rf_add"))
        self.folder_button.setText(self.t("rf_or_folder"))
        self.reload_button.setText(self.t("rf_reload"))
        self.remove_button.setText(self.t("rf_remove"))
        self.to_statics.setText(self.t("rf_to_statics"))
        self.to_statics.setToolTip(self.t("rf_to_statics_tip"))
        self.empty.setText(self.t("rf_none"))
        self.hint.setText(self.t("rf_no_selection"))
        self.figure.setTitle(self.t("rf_figure"))
        self.combinations.setTitle(self.t("rf_combinations_card"))
        self.combination_list.setHeaderLabels(["", self.t("rf_formula"), self.t("rf_duration")])
        self.filling = True
        try:
            for index, key in enumerate(QUANTITIES):
                self.quantity_box.setItemText(index, self.t("rf_system") if key is None else key)
            if self.situation_box.count():
                self.situation_box.setItemText(0, self.t("rf_all"))
        finally:
            self.filling = False
        keep = self.selected_keys()
        self.fill_tree()
        self.select_keys(keep)

    def view_state(self):
        named, key = self.selected_keys()
        return {"splitter": self.splitter.sizes(), "model": named, "structure": key,
                "quantity": self.quantity, "loading": self.loading}

    def restore(self, state):
        if not state:
            return
        if state.get("splitter"):
            self.splitter.setSizes(state["splitter"])
        if state.get("quantity") in QUANTITIES:
            self.quantity = state["quantity"]
            self.quantity_box.setCurrentIndex(QUANTITIES.index(self.quantity))
        self.loading = state.get("loading")
        self.select_keys((state.get("model"), state.get("structure")))
