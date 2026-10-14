# -*- coding: utf-8 -*-
"""The loads entered in Woodcore (issues #35, #36, #37): «Poids propre et surcharge», «Neige» and «Vent» in the group «Actions» (docs/ui/window.md §10quater, docs/domain/loads.md).

Each tab lists the cases of one load domain that the project's own sources hold -- `Woodcore-Datei/loads/<kind>/<id>.json` --, edits one in cards, and shows at once what Python computes from it, the drawing included: the domain modules compute (`domains/dead_load_source.py`, `snow_source.py`, `wind_source.py`), the tab shows, edits and calls them and never computes (docs/architecture/principles.md). Saving writes the source and rebuilds `data/calculations.json` beside the sheets of the load workbooks (`registry.export`, decision D-04), so the report's `show-calc` prints the case. «Affichage» shows that call and its page.

**One base, `LoadTab`** -- the list in folders (`grouped_list`), «Supprimer» into «Archives» (`source_archive`), Nom · Description · ID (`identity`), the cards (`cards`), the two views (`views`, `display_view`) -- and a subclass per domain building its own cards (`build_inputs`, `fill_inputs`, `draft_inputs`). The arrangement is the member checks' (member_check_tab.MemberCheckTab), without what a member check reads of a position: a load belongs to no position (docs/domain/loads.md §8).
"""

import copy
import json

from PySide6.QtCore import QByteArray, Qt, QTimer
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDoubleSpinBox, QHBoxLayout, QHeaderView, QLabel, QPushButton, QSizePolicy, QSplitter,
    QTableWidget, QVBoxLayout, QWidget,
)

import autosave
import cards
import display_view
import grouped_list
import identity
import linkable_spin  # the button beside a number that may follow a variable (spec 2026-10-11-variables-liees-champs-et-textes)
import project
import registry
import richtext
import shown_variables
import source_archive
import theme
import validation
import views
from domains import dead_load_source, links, materials, snow_source, wind_source
from i18n import strings
from member_check_tab import NEW_ROW, next_free_id
from norms import sia261_snow, sia261_wind

OPTION_DELAY_MS = 150

STRINGS = {
    "fr": {
        "ld_list_dead": "Compositions",
        "ld_empty_dead": "Aucune composition pour l’instant : « Nouveau » en crée une.",
        "ld_new": "Nouveau",
        "ld_duplicate": "Dupliquer",
        "ld_delete": "Supprimer",
        "ld_new_item": "(nouvelle, non enregistrée)",
        "ld_save": "Enregistrer",
        "ld_revert": "Annuler les modifications",
        "ld_saved": "{id} enregistré, calculations.json exporté.",
        "ld_moved": "{count} déplacé(s) dans « {group} ».",
        "ld_export_failed": "L’export des charges a échoué : {error}",
        "ld_invalid": "Saisie incomplète : {error}",
        "ld_taken": "L’ID « {id} » est déjà pris ou n’est pas valable.",
        "ld_rename_title": "Renommer",
        "ld_rename": "Renommer {old} en {new} ? Un appel qui nomme {old} devra être corrigé.",
        "ld_unsaved_title": "Modifications non enregistrées",
        "ld_unsaved": "{id} a des modifications non enregistrées.",
        "ld_results": "Résultats",
        "ld_figure": "Composition",
        "ld_none": "—",
        "ld_link_circle": "Refusé : ce lien fermerait une boucle de charges ({chain}).",
        "ld_save_first": "Enregistrez pour que le rapport imprime ce cas : l’appel nomme ce que le dernier export contient.",
        "ld_warn_above_limit": "Altitude h_0 = {h_0} m : la norme SIA 261 n’autorise pas ce calcul au-dessus de {limit} m ({ref}). La charge est calculée quand même ; le rapport n’en dit rien.",
        "ld_box_layers": "Couches, de haut en bas",
        "ld_col_kind": "Type",
        "ld_col_library": "Bibliothèque",
        "ld_col_material": "Matériau",
        "ld_col_thickness": "Épaisseur [mm]",
        "ld_col_width": "Largeur [mm]",
        "ld_col_spacing": "Entraxe [mm]",
        "ld_col_beside": "À côté",
        "ld_col_load": "Charge [kN/m²]",
        "ld_kind_gk": "g_k — poids propre",
        "ld_kind_ak": "a_k — surcharge",
        "ld_lib_sia261": "SIA 261 annexe A",
        "ld_lib_belastungsannahmen": "Bibliothèque Woodcore",
        "ld_lib_project": "Projet",
        "ld_lib_direct": "Charge saisie",
        "ld_add": "Ajouter une couche",
        "ld_remove": "Retirer",
        "ld_up": "Monter",
        "ld_down": "Descendre",
        "ld_layers_hint": "Chaque couche est un poids propre (g_k) ou une surcharge (a_k). Largeur et entraxe : des lattes, chevrons ou solives espacés ; vides pour une couche continue. « À côté » : la couche partage la bande de celle du dessus (l’isolation entre les chevrons).",
        "ld_box_chosen": "Valeur retenue",
        "ld_chosen": "Charge permanente retenue",
        "ld_chosen_sum": "la somme",
        "ld_box_project": "Bibliothèque du projet",
        "ld_project_hint": "Les poids volumiques que vous ajoutez à la main, dans Woodcore-Datei/materials.json : un matériau que la SIA 261 et la bibliothèque Woodcore n’ont pas, ou celui d’un fabricant.",
        "ld_col_id": "ID",
        "ld_col_name": "Nom",
        "ld_col_value": "Poids",
        "ld_col_unit": "Unité",
        "ld_col_source": "Source",
        "ld_add_material": "Ajouter un matériau",
        "ld_save_materials": "Enregistrer la bibliothèque",
        "ld_materials_saved": "Bibliothèque du projet enregistrée.",
        "ld_list_wind": "Bâtiments",
        "ld_empty_wind": "Aucun bâtiment pour l’instant : « Nouveau » en crée un.",
        "ld_qp0": "Pression dynamique de référence q_p0 (annexe E)",
        "ld_terrain": "Catégorie de terrain (tableau 4)",
        "ld_box_building": "Bâtiment",
        "ld_b": "b (perpendiculaire au vent φ = 0°)",
        "ld_d": "d (parallèle au vent φ = 0°)",
        "ld_h": "Hauteur h",
        "ld_z": "Hauteur z de q_p",
        "ld_z_h": "= h",
        "ld_table": "Coefficients (annexe C, tableau)",
        "ld_cd": "Facteur dynamique c_d",
        "ld_wind_hint": "c_red est calculé d’après la figure 9 pour b·h et d·h, 1.0 pour la toiture (6.3.2). c_d = 1.0 pour les bâtiments jusqu’à 15 m et les bâtiments à parois ou cadres porteurs de moins de 100 m (6.3.5), sinon selon la SIA 261/1.",
        "ld_list_snow": "Toitures",
        "ld_empty_snow": "Aucune toiture pour l’instant : « Nouveau » en crée une.",
        "ld_figure_snow": "Disposition de la charge (figure 3)",
        "ld_box_site": "Lieu",
        "ld_h0": "Altitude h_0",
        "ld_correction": "Correction Δh (annexe D)",
        "ld_exposure": "Exposition au vent",
        "ld_ct": "Coefficient thermique C_T",
        "ld_box_roof": "Toiture",
        "ld_roof": "Forme de la toiture",
        "ld_length": "Longueur",
        "ld_width": "Largeur",
        "ld_alpha1": "Inclinaison α_1",
        "ld_alpha2": "Inclinaison α_2",
        "ld_sliding": "Glissement de la neige",
        "ld_roof_hint": "SIA 261 figure 3 : modèle de charge 1 et 2 ; un toit à un pan est la moitié d’un toit symétrique (5.3.2) ; une toiture cylindrique lit μ_3(α) de la figure 2, α étant l’angle de la corde jusqu’au point de pente 60°. Glissement empêché (arrêts de neige, acrotère) : μ_1 = 0.8 (5.3.4). Au-dessus de 800 m d’altitude, le rapport rappelle la corniche des porte-à-faux (5.3.7).",
        "ld_height_step": "Décrochement : toit étagé ou proche d’un ouvrage plus élevé (5.3.6, figure 5 ; rappelé au rapport, non calculé)",
    },
    "de": {
        "ld_list_dead": "Aufbauten",
        "ld_empty_dead": "Noch kein Aufbau: «Neu» legt einen an.",
        "ld_new": "Neu",
        "ld_duplicate": "Duplizieren",
        "ld_delete": "Löschen",
        "ld_new_item": "(neu, nicht gespeichert)",
        "ld_save": "Speichern",
        "ld_revert": "Änderungen verwerfen",
        "ld_saved": "{id} gespeichert, calculations.json exportiert.",
        "ld_moved": "{count} nach «{group}» verschoben.",
        "ld_export_failed": "Der Export der Lasten ist fehlgeschlagen: {error}",
        "ld_invalid": "Unvollständige Eingabe: {error}",
        "ld_taken": "Die ID «{id}» ist schon vergeben oder ungültig.",
        "ld_rename_title": "Umbenennen",
        "ld_rename": "{old} in {new} umbenennen? Ein Aufruf, der {old} nennt, muss angepasst werden.",
        "ld_unsaved_title": "Nicht gespeicherte Änderungen",
        "ld_unsaved": "{id} hat nicht gespeicherte Änderungen.",
        "ld_results": "Ergebnisse",
        "ld_figure": "Aufbau",
        "ld_none": "—",
        "ld_link_circle": "Abgelehnt: Diese Verknüpfung schlösse einen Kreis von Lasten ({chain}).",
        "ld_save_first": "Speichern Sie, damit der Bericht diesen Fall ausgibt: der Aufruf nennt, was der letzte Export enthält.",
        "ld_warn_above_limit": "Höhe h_0 = {h_0} m: die Norm SIA 261 lässt diese Berechnung über {limit} m nicht zu ({ref}). Die Last wird trotzdem berechnet; der Bericht sagt nichts davon.",
        "ld_box_layers": "Schichten, von oben nach unten",
        "ld_col_kind": "Typ",
        "ld_col_library": "Bibliothek",
        "ld_col_material": "Material",
        "ld_col_thickness": "Dicke [mm]",
        "ld_col_width": "Breite [mm]",
        "ld_col_spacing": "Abstand [mm]",
        "ld_col_beside": "Daneben",
        "ld_col_load": "Last [kN/m²]",
        "ld_kind_gk": "g_k — Eigenlast",
        "ld_kind_ak": "a_k — Auflast",
        "ld_lib_sia261": "SIA 261 Anhang A",
        "ld_lib_belastungsannahmen": "Woodcore-Bibliothek",
        "ld_lib_project": "Projekt",
        "ld_lib_direct": "Eingegebene Last",
        "ld_add": "Schicht hinzufügen",
        "ld_remove": "Entfernen",
        "ld_up": "Nach oben",
        "ld_down": "Nach unten",
        "ld_layers_hint": "Jede Schicht ist Eigenlast (g_k) oder Auflast (a_k). Breite und Abstand: Latten, Sparren oder Balken im Abstand; leer für eine durchgehende Schicht. «Daneben»: die Schicht teilt das Band der Schicht darüber (die Dämmung zwischen den Sparren).",
        "ld_box_chosen": "Gewählter Wert",
        "ld_chosen": "Gewählte ständige Last",
        "ld_chosen_sum": "die Summe",
        "ld_box_project": "Projektbibliothek",
        "ld_project_hint": "Die Raumgewichte, die Sie von Hand ergänzen, in Woodcore-Datei/materials.json: ein Material, das SIA 261 und die Woodcore-Bibliothek nicht führen, oder das eines Herstellers.",
        "ld_col_id": "ID",
        "ld_col_name": "Name",
        "ld_col_value": "Gewicht",
        "ld_col_unit": "Einheit",
        "ld_col_source": "Quelle",
        "ld_add_material": "Material hinzufügen",
        "ld_save_materials": "Bibliothek speichern",
        "ld_materials_saved": "Projektbibliothek gespeichert.",
        "ld_list_wind": "Gebäude",
        "ld_empty_wind": "Noch kein Gebäude: «Neu» legt eines an.",
        "ld_qp0": "Referenzwert des Staudrucks q_p0 (Anhang E)",
        "ld_terrain": "Geländekategorie (Tabelle 4)",
        "ld_box_building": "Gebäude",
        "ld_b": "b (quer zum Wind φ = 0°)",
        "ld_d": "d (längs zum Wind φ = 0°)",
        "ld_h": "Höhe h",
        "ld_z": "Höhe z von q_p",
        "ld_z_h": "= h",
        "ld_table": "Beiwerte (Anhang C, Tabelle)",
        "ld_cd": "Dynamischer Faktor c_d",
        "ld_wind_hint": "c_red wird nach Figur 9 für b·h und d·h berechnet, 1.0 für das Dach (6.3.2). c_d = 1.0 für Gebäude bis 15 m und Gebäude mit tragenden Wänden oder Rahmen unter 100 m (6.3.5), sonst nach SIA 261/1.",
        "ld_list_snow": "Dächer",
        "ld_empty_snow": "Noch kein Dach: «Neu» legt eines an.",
        "ld_figure_snow": "Lastanordnung (Figur 3)",
        "ld_box_site": "Standort",
        "ld_h0": "Höhe h_0",
        "ld_correction": "Korrektur Δh (Anhang D)",
        "ld_exposure": "Windexposition",
        "ld_ct": "Thermischer Beiwert C_T",
        "ld_box_roof": "Dach",
        "ld_roof": "Dachform",
        "ld_length": "Länge",
        "ld_width": "Breite",
        "ld_alpha1": "Neigung α_1",
        "ld_alpha2": "Neigung α_2",
        "ld_sliding": "Abgleiten des Schnees",
        "ld_roof_hint": "SIA 261 Figur 3: Lastmodell 1 und 2; ein Pultdach ist die Hälfte eines symmetrischen Dachs (5.3.2); ein Tonnendach liest μ_3(α) aus Figur 2, α der Winkel der Sehne bis zum Punkt der Neigung 60°. Abgleiten behindert (Schneefang, Brüstung): μ_1 = 0.8 (5.3.4). Über 800 m Meereshöhe erinnert der Bericht an den Schneeüberhang auskragender Dachteile (5.3.7).",
        "ld_height_step": "Höhensprung: abgestuftes Dach oder an ein höheres Bauwerk angrenzend (5.3.6, Figur 5; im Bericht genannt, nicht berechnet)",
    },
    "en": {
        "ld_list_dead": "Build-ups",
        "ld_empty_dead": "No build-up yet: “New” makes one.",
        "ld_new": "New",
        "ld_duplicate": "Duplicate",
        "ld_delete": "Delete",
        "ld_new_item": "(new, not saved)",
        "ld_save": "Save",
        "ld_revert": "Discard changes",
        "ld_saved": "{id} saved, calculations.json exported.",
        "ld_moved": "{count} moved to “{group}”.",
        "ld_export_failed": "The export of the loads failed: {error}",
        "ld_invalid": "Incomplete entry: {error}",
        "ld_taken": "The ID “{id}” is taken or not valid.",
        "ld_rename_title": "Rename",
        "ld_rename": "Rename {old} to {new}? A call naming {old} will need correcting.",
        "ld_unsaved_title": "Unsaved changes",
        "ld_unsaved": "{id} has unsaved changes.",
        "ld_results": "Results",
        "ld_figure": "Build-up",
        "ld_none": "—",
        "ld_link_circle": "Refused: this link would close a circle of loads ({chain}).",
        "ld_save_first": "Save so that the report prints this case: the call names what the last export holds.",
        "ld_warn_above_limit": "Altitude h_0 = {h_0} m: the standard SIA 261 does not allow this calculation above {limit} m ({ref}). The load is computed all the same; the report says nothing of it.",
        "ld_box_layers": "Layers, top to bottom",
        "ld_col_kind": "Type",
        "ld_col_library": "Library",
        "ld_col_material": "Material",
        "ld_col_thickness": "Thickness [mm]",
        "ld_col_width": "Width [mm]",
        "ld_col_spacing": "Spacing [mm]",
        "ld_col_beside": "Beside",
        "ld_col_load": "Load [kN/m²]",
        "ld_kind_gk": "g_k — self-weight",
        "ld_kind_ak": "a_k — superimposed",
        "ld_lib_sia261": "SIA 261 Annex A",
        "ld_lib_belastungsannahmen": "Woodcore library",
        "ld_lib_project": "Project",
        "ld_lib_direct": "Load entered",
        "ld_add": "Add a layer",
        "ld_remove": "Remove",
        "ld_up": "Up",
        "ld_down": "Down",
        "ld_layers_hint": "Each layer is self-weight (g_k) or superimposed load (a_k). Width and spacing: battens, rafters or joists at a spacing; empty for a continuous layer. “Beside”: the layer shares the band of the one above it (the insulation between the rafters).",
        "ld_box_chosen": "Value chosen",
        "ld_chosen": "Permanent load chosen",
        "ld_chosen_sum": "the sum",
        "ld_box_project": "Project library",
        "ld_project_hint": "The unit weights you add by hand, in Woodcore-Datei/materials.json: a material SIA 261 and the Woodcore library lack, or a manufacturer's.",
        "ld_col_id": "ID",
        "ld_col_name": "Name",
        "ld_col_value": "Weight",
        "ld_col_unit": "Unit",
        "ld_col_source": "Source",
        "ld_add_material": "Add a material",
        "ld_save_materials": "Save the library",
        "ld_materials_saved": "Project library saved.",
        "ld_list_wind": "Buildings",
        "ld_empty_wind": "No building yet: “New” makes one.",
        "ld_qp0": "Reference dynamic pressure q_p0 (Annex E)",
        "ld_terrain": "Terrain category (Table 4)",
        "ld_box_building": "Building",
        "ld_b": "b (across the wind φ = 0°)",
        "ld_d": "d (along the wind φ = 0°)",
        "ld_h": "Height h",
        "ld_z": "Height z of q_p",
        "ld_z_h": "= h",
        "ld_table": "Coefficients (Annex C, table)",
        "ld_cd": "Dynamic factor c_d",
        "ld_wind_hint": "c_red is computed from Figure 9 for b·h and d·h, 1.0 for the roof (6.3.2). c_d = 1.0 for buildings up to 15 m and buildings with load-bearing walls or frames under 100 m (6.3.5), else from SIA 261/1.",
        "ld_list_snow": "Roofs",
        "ld_empty_snow": "No roof yet: “New” makes one.",
        "ld_figure_snow": "Load arrangement (Figur 3)",
        "ld_box_site": "Site",
        "ld_h0": "Altitude h_0",
        "ld_correction": "Correction Δh (Annex D)",
        "ld_exposure": "Wind exposure",
        "ld_ct": "Thermal coefficient C_T",
        "ld_box_roof": "Roof",
        "ld_roof": "Roof form",
        "ld_length": "Length",
        "ld_width": "Width",
        "ld_alpha1": "Slope α_1",
        "ld_alpha2": "Slope α_2",
        "ld_sliding": "Sliding of the snow",
        "ld_roof_hint": "SIA 261 Figur 3: load models 1 and 2; a mono-pitch roof is half a symmetric roof (5.3.2); a curved roof reads μ_3(α) of Figur 2, α the angle of the chord up to the point of slope 60°. Sliding hindered (snow guards, a parapet): μ_1 = 0.8 (5.3.4). Above 800 m altitude the report recalls the cornice of overhanging roof parts (5.3.7).",
        "ld_height_step": "Height step: a stepped roof, or one adjoining a taller building (5.3.6, Figur 5; named in the report, not computed)",
    },
}


def _n(value):
    text = ("%.3f" % value).rstrip("0").rstrip(".")
    return "0" if text in ("", "-0") else text


class LoadTab(QWidget):
    """The tab of one load domain entered in Woodcore -- see the module's docstring. A subclass names its module (`MODULE`: `FOLDER`, `DOMAIN`, `new_source`, `check_source`, `read_source`, `build_instance`, and where it has them `warnings` -- what the tab says and the report does not -- and `sketch` -- a drawing the tab shows and the export does not carry), its key, its ID prefix and its list's words, and builds its cards."""

    KEY = ""
    MODULE = None
    ID_PREFIX = "L-"
    LIST_KEY = ""
    EMPTY_KEY = ""
    VIEWS = views.CALC_VIEWS

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.t = app.t
        self.loading = False
        self.dirty = False
        self.current_id = None
        self.live = False
        self.view = "calc"
        self.instance = None
        self.reason = ""
        self.ids = []
        self.empty_folders = list(app.folder_settings(self.KEY))
        self.source = self.make_source()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.addWidget(self.build_list())
        self.splitter.addWidget(self.build_form())
        self.splitter.addWidget(self.build_result())
        self.display = display_view.DisplayView(self.t, mono_font=self.app.mono_font, copy=self.app.copy, cache_key=self.KEY, lang=self.app.lang,
                                                import_fn=lambda: self.app.reexport(), import_text=self.t("reexport"), parent=self)
        self.panes = display_view.ViewPanes(self.splitter, self.display)
        for index, stretch in enumerate((2, 6, 4)):
            self.splitter.setStretchFactor(index, stretch)
        layout.addWidget(self.splitter, 1)
        self.refresh_timer = QTimer(self)
        self.refresh_timer.setSingleShot(True)
        self.refresh_timer.setInterval(OPTION_DELAY_MS)
        self.refresh_timer.timeout.connect(self.request_preview)
        shortcut = QShortcut(QKeySequence(QKeySequence.StandardKey.Save), self)
        shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        shortcut.activated.connect(self.save)
        self.restore(app.views.get(self.KEY))

    # --- helpers ---------------------------------------------------------------

    def tl(self, text):
        return strings.translate(text, self.app.lang)

    def heading(self, text):
        label = QLabel(text)
        label.setFont(self.app.bold_font)
        return label

    def spin(self, minimum, maximum, decimals=1, step=1.0, suffix=""):
        box = QDoubleSpinBox()
        box.setRange(minimum, maximum)
        box.setDecimals(decimals)
        box.setSingleStep(step)
        box.setSuffix(suffix)
        box.setMinimumWidth(70)
        return box

    # --- a field that follows a variable (spec 2026-10-11-variables-liees-champs-et-textes, issue #42) ---------------

    def linked(self, spin, key, unit, label, store=True):
        """`spin` with the button that links it to a variable -- of another load or of a «Formule» domain only, the loads being computed first (links.LOADS, D-11) --; the widget the form or the table holds in its place. A link that would close a circle of loads is refused as it is chosen (REQ-007)."""
        wrapper = linkable_spin.LinkableSpin(spin, unit, label, lambda: self.app, self.app.lang, links.LOADS, refuse=self.refuse_link)
        wrapper.changed.connect(self.touch)
        if store:
            if not hasattr(self, "linkables"):
                self.linkables, self.wrappers = {}, {}
            self.linkables[key] = wrapper
            self.wrappers[id(spin)] = wrapper
        return wrapper

    def row_of(self, spin):
        """The widget a form row holds for `spin`: its wrapper where it may follow a variable -- what `setRowVisible` names."""
        return getattr(self, "wrappers", {}).get(id(spin), spin)

    def link_values(self):
        """The export's values, read once per filling of the form."""
        if getattr(self, "_link_values", None) is None:
            self._link_values = linkable_spin.current_values()
        return self._link_values

    def fill_links(self, s):
        found = links.links_of(s)
        for key, wrapper in getattr(self, "linkables", {}).items():
            wrapper.set_link(found.get(key), self.link_values() if found else {})

    def draft_links(self, s):
        """The form's links into the draft -- the load's own, and each layer's (`_layer_of`) --, those of a field the draft does not hold taken off, and the schema_version that says whether any is left."""
        found = {key: w.link() for key, w in getattr(self, "linkables", {}).items() if w.link() is not None}
        if found:
            s[links.LINKS] = found
        else:
            s.pop(links.LINKS, None)
        links.drop_unheld(s, self.MODULE.LINKABLE)
        self.MODULE.stamp_version(s)

    def refuse_link(self, link):
        """A sentence where `link` would make this load follow, through others, a variable of its own (REQ-007), else None."""
        if link.get("origin") == links.FORMULAS:
            return None
        node = (self.MODULE.DOMAIN, (self.identity.values()[2] or "").strip())
        graph = registry.load_graph(project.current())
        draft = self.draft()
        graph[node] = registry.load_targets(draft, self.MODULE.DOMAIN) | {(link["domain"], link["instance"])}
        chain = links.find_cycle(graph, node)
        if chain:
            return self.t("ld_link_circle", chain=" → ".join("%s/%s" % pair for pair in chain))
        return None

    def folder(self):
        return project.current().sources_dir / self.MODULE.FOLDER

    def _taken(self):
        folder = self.folder()
        return sorted(p.stem for p in folder.glob("*.json")) if folder.is_dir() else []

    def make_source(self):
        return self.MODULE.new_source(next_free_id(self._taken(), self.ID_PREFIX))

    def touch(self, *_ignored):
        if self.loading:
            return
        self.dirty = True
        self.refresh(preview=False)
        self.refresh_timer.start()

    # --- left: the cases --------------------------------------------------------

    def build_list(self):
        box = QWidget()
        column = QVBoxLayout(box)
        self.list = grouped_list.GroupedList(STRINGS.get(self.app.lang, STRINGS["fr"]), lang=self.app.lang)
        self.archive = source_archive.Actions(self, self.folder, self.export, lambda select: self.reload_list(select), self._after_archive)
        self.archive.connect()
        column.addWidget(grouped_list.title_row(self.heading(self.t(self.LIST_KEY)), self.list))
        self.list.setIconSize(self.app.mark_size)
        self.list.currentIdChanged.connect(self.on_list_change)
        self.list.moved.connect(self.on_moved)
        self.list.foldersChanged.connect(self.on_folders_changed)
        self.list.attach_order(self.KEY, self.app.list_store)
        self.list.reordered.connect(lambda: self.reload_list(self.current_id))
        column.addWidget(self.list, 1)
        self.empty_hint = cards.note(self.t(self.EMPTY_KEY))
        column.addWidget(self.empty_hint)
        row = QHBoxLayout()
        for key, slot in (("ld_new", self.new), ("ld_duplicate", self.duplicate), ("ld_delete", self.delete)):
            button = QPushButton(self.t(key))
            button.clicked.connect(slot)
            row.addWidget(button)
        column.addLayout(row)
        return box

    def _group_of(self, cid):
        try:
            source = json.loads((self.folder() / ("%s.json" % cid)).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return grouped_list.ROOT_GROUP
        return grouped_list.group_of(source)

    def reload_list(self, select=None):
        self.loading = True
        self.ids = self._taken()
        entries = [{"id": cid, "text": cid, "group": self._group_of(cid)} for cid in self.ids]
        if self.current_id is None:
            entries.append({"id": NEW_ROW, "text": "%s %s" % ((self.source or {}).get("id") or "?", self.t("ld_new_item")), "group": grouped_list.ROOT_GROUP})
        target = select if select in self.ids else (NEW_ROW if self.current_id is None else None)
        self.list.set_entries(entries, self.empty_folders, target, archived=source_archive.entries(self.folder(), self.list._t))
        self.empty_folders = self.list.empty_folders()
        self.app.save_folder_settings(self.KEY, self.empty_folders)
        self.empty_hint.setVisible(not self.ids)
        self.loading = False
        self.update_list_marker()

    def on_folders_changed(self):
        self.empty_folders = self.list.empty_folders()
        self.reload_list(select=self.current_id)

    def update_list_marker(self):
        for cid in self.list.ids():
            mine = cid == self.current_id or (self.current_id is None and cid == NEW_ROW)
            self.list.set_mark(cid, self.app.dirty_mark(mine and self.dirty))
        self.app.update_tab_marks()

    def on_list_change(self, cid):
        if self.loading or not cid or cid not in self.ids:
            return
        if not self.confirm_leave():
            self.loading = True
            if self.current_id in self.ids:
                self.list.select(self.current_id)
            self.loading = False
            return
        self.load(cid)
        if NEW_ROW in self.list.ids():
            self.reload_list(cid)

    def on_moved(self, ids, group):
        if not self.confirm_leave():
            self.reload_list(self.current_id)
            return
        for cid in ids:
            if cid == NEW_ROW:
                continue
            path = self.folder() / ("%s.json" % cid)
            try:
                source = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            source["group"] = group or ""
            path.write_text(json.dumps(source, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            if cid == self.current_id:
                self.source["group"] = group or ""
        self.export(self.t("ld_moved", count=len(ids), group=group or "—"))
        self.reload_list(self.current_id)

    def load(self, cid):
        path = self.folder() / ("%s.json" % cid)
        try:
            source = self.MODULE.read_source(path)
        except validation.ValidationError:
            source = json.loads(path.read_text(encoding="utf-8"))
        self.source = source
        self.current_id = cid
        self.dirty = False
        self.fill_form()
        self.refresh()

    # --- middle: the form ------------------------------------------------------------

    def build_form(self):
        panel = QWidget()
        column = QVBoxLayout(panel)
        column.setContentsMargins(0, 0, 0, 0)
        scroll, self.form = cards.column()
        column.addWidget(scroll, 1)
        box = cards.card()
        form = cards.form(box)
        self.identity = identity.IdentityRows(form, self.t, self.touch)
        self.form.addWidget(box)
        self.build_inputs()
        self.form.addStretch(1)
        actions = QHBoxLayout()
        revert = QPushButton(self.t("ld_revert"))
        revert.clicked.connect(self.revert)
        save = QPushButton(self.t("ld_save"))
        save.setDefault(True)
        save.clicked.connect(self.save)
        actions.addStretch(1)
        actions.addWidget(revert)
        actions.addWidget(save)
        column.addLayout(actions)
        return panel

    def build_inputs(self):
        """A domain's cards, added to `self.form`."""

    def fill_inputs(self, s):
        """The source `s` in the domain's cards."""

    def draft_inputs(self, s):
        """The domain's cards in the draft `s`."""

    def fill_form(self):
        self.loading = True
        s = self.source
        self.identity.fill(s.get("name", ""), s.get("label", ""), s.get("id", ""), saved=self.current_id is not None)
        self._link_values = None   # the export's values read again for this filling
        self.fill_inputs(s)
        self.fill_links(s)
        self.loading = False

    def draft(self):
        s = copy.deepcopy(self.source)
        name, description, sid = self.identity.values()
        s["id"], s["name"], s["label"] = sid, name, description
        self.draft_inputs(s)
        self.draft_links(s)
        return s

    # --- right: what Python computes, and the drawing ----------------------------------

    def build_result(self):
        scroll, details = cards.column(margins=(0, 10, 4, 0), hold=False)
        self.message = QLabel("")
        self.message.setTextFormat(Qt.TextFormat.RichText)
        self.message.setWordWrap(True)
        self.message.setProperty("callout", "warning")
        self.message.setVisible(False)
        details.addWidget(self.message)
        results = cards.card(self.t("ld_results"))
        box = QVBoxLayout(results)
        self.results_label = QLabel("")
        self.results_label.setTextFormat(Qt.TextFormat.RichText)
        self.results_label.setWordWrap(True)
        self.results_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        box.addWidget(self.results_label)
        details.addWidget(results)
        figure = cards.card(self.t(self.FIGURE_KEY) if hasattr(self, "FIGURE_KEY") else self.t("ld_figure"))
        fv = QVBoxLayout(figure)
        self.figure_svg = QSvgWidget()
        self.figure_svg.setMinimumHeight(160)
        self.figure_svg.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        fv.addWidget(self.figure_svg)
        self.figure_card = figure
        details.addWidget(figure)
        details.addStretch(1)
        return scroll

    def refresh(self, preview=True):
        """The draft computed at once: its results, its drawing, its call -- or why it cannot be, in the warning callout."""
        source = self.draft()
        self.instance, self.reason, self.warning, self.drawing = None, "", "", None
        try:
            self.MODULE.check_source(source, "%s/%s.json" % (self.MODULE.FOLDER, source.get("id") or "?"))
            self.instance = self.MODULE.build_instance(source, project.current())
            # what the domain says of a valid case and the report never prints -- a snow site above 5.1.4's limit (spec 2026-10-14-neige-vent-affichage-altitude, REQ-004, D-04): worded here, judged there
            self.warning = "\n".join(self.t("ld_warn_" + code, **{k: _n(v) if isinstance(v, (int, float)) else v for k, v in params.items()})
                                      for code, params in getattr(self.MODULE, "warnings", lambda _s: [])(source))
            # a drawing the tab shows and the export does not carry: the snow's (D-03); the others' is the instance's own `_files`
            self.drawing = self.MODULE.sketch(source) if hasattr(self.MODULE, "sketch") else None
        except (validation.ValidationError, ValueError, KeyError, TypeError, ZeroDivisionError) as exc:
            self.reason = self.t("ld_invalid", error=str(exc))
        said = self.reason or self.warning
        self.message.setText(richtext.prose_html(said))
        self.message.setVisible(bool(said))
        self.fill_results()
        self.fill_figure()
        self.fill_command()
        self.update_list_marker()
        if preview:
            self.request_preview()

    def fill_results(self):
        """Every var of the instance, the symbol as mathematics, its value and unit; the results in bold."""
        if not self.instance:
            self.results_label.setText("<span style='color:%s'>%s</span>" % (theme.colour("muted"), richtext.prose_html(self.reason or self.t("ld_none"))))
            return
        results = set(self.instance.get("results") or ())
        body = []
        for name, var in self.instance["vars"].items():
            value = var.get("value")
            text = _n(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else self.tl(str(value))
            unit = (" " + richtext.escape(var["unit"])) if var.get("unit") else ""
            weight = "font-weight:600;" if name in results else ""
            label = richtext.escape(self.tl(var.get("label") or ""))
            body.append("<tr style='%s'><td style='padding-right:8px'>%s</td><td style='padding-right:6px'>=</td><td align='right'>%s%s</td><td style='padding-left:10px;color:%s'>%s</td></tr>"
                        % (weight, richtext.math_html(var.get("symbol") or name), richtext.escape(text), unit, theme.colour("muted"), label))
        html = '<table cellspacing="0" cellpadding="1">' + "".join(body) + "</table>"
        # the instance's tables after its values: a build-up's layers, the wind's global and local forces -- a value cell names its var
        vars_ = self.instance["vars"]
        muted = theme.colour("muted")
        for table in self.instance.get("tables") or ():
            groups = [c.get("group") for c in table["columns"]]
            group_row = ("<tr>%s</tr>" % "".join("<th style='padding:0 6px;color:%s'>%s</th>" % (muted, richtext.escape(self.tl(g or ""))) for g in groups)) if any(groups) else ""
            head = "".join("<th style='padding:0 6px'>%s</th>" % richtext.escape(self.tl(c.get("label") or "")) for c in table["columns"])
            rows = []
            for row in table["rows"]:
                cells = []
                for column, value in zip(table["columns"], row):
                    if column.get("kind") == "value" and value in vars_:
                        value = vars_[value]["value"]
                    text = _n(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else self.tl(str(value or ""))
                    cells.append("<td align='right' style='padding:0 6px'>%s</td>" % richtext.escape(text))
                rows.append("<tr>%s</tr>" % "".join(cells))
            html += "<p style='margin:8px 0 2px 0;font-weight:600'>%s</p><table cellspacing='0' cellpadding='1'>%s<tr>%s</tr>%s</table>" % (
                richtext.escape(self.tl(table.get("title") or "")), group_row, head, "".join(rows))
        self.results_label.setText(html)

    def fill_figure(self):
        drawing = self.drawing or next(iter(((self.instance or {}).get("_files") or {}).values()), None)
        self.figure_card.setVisible(bool(drawing))
        if drawing:
            try:
                self.figure_svg.load(QByteArray(drawing.encode("utf-8")))
                self.figure_svg.renderer().setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)
            except Exception:  # broad: a drawing that fails must not empty the form
                pass

    # --- «Affichage» --------------------------------------------------------------

    def shown_choices(self, cid):
        """What the level -1 offers to tick: the case's vars, tables and drawings as the last export holds them (shown_variables.export_choices) -- read again only when the export changed, not at every keystroke (ARCH-RISK-002 of spec 2026-10-14-neige-vent-affichage-altitude)."""
        data = project.current().data_dir
        try:
            stamp = (data / "calculations.json").stat().st_mtime_ns
        except OSError:
            stamp = None
        key = (str(data), cid, stamp)
        if getattr(self, "_choices", (None, None))[0] != key:
            self._choices = (key, shown_variables.export_choices(data, self.MODULE.DOMAIN, cid) if cid else [])
        return self._choices[1]

    def display_entries(self):
        """show-calc with its panel -- the level, -1 «Sélection manuelle» among them, and the title -- for the three loads alike (issues #56, #57; spec 2026-10-14-neige-vent-affichage-altitude, REQ-001, D-05), the polar moments' and the variables' own pattern."""
        unsaved = self.current_id is None or self.dirty
        cid = self.draft().get("id") or ""
        return [display_view.Entry("calc", "show-calc", "show-calc", positional=(self.MODULE.DOMAIN, cid), note_text=self.reason,
                                   banner=self.t("ld_save_first") if unsaved else "", context={"shown": self.shown_choices(cid)})]

    def fill_command(self):
        self.display.set_project(project.current(), self.app.current_document())
        self.display.set_entries(self.display_entries())

    def set_view(self, key, enter=True):
        if key not in self.VIEWS:
            return
        self.view = key
        self.panes.show(key == "display", enter and self.live)
        if key == "display":
            self.fill_command()

    def request_preview(self):
        if not self.live or self.view != "display":
            return
        try:
            if not self.display.active:
                self.display.activate(True)
            else:
                self.display.refresh()
        except Exception as exc:  # broad: a malformed case is said in the form, not raised into the event loop
            self.message.setText(richtext.prose_html(self.t("ld_invalid", error=str(exc))))
            self.message.setVisible(True)

    def on_shown(self):
        self.live = True
        dirty = self.dirty
        self.source = self.draft()
        self.reload_list(self.current_id)
        self.fill_form()
        self.dirty = dirty
        self.refresh()

    def showEvent(self, event):
        super().showEvent(event)
        if not self.live:
            self.live = True
            self.panes.show(self.view == "display")

    def stop(self):
        self.display.pane.stop() if getattr(self.display, "pane", None) is not None else None

    # --- the buttons --------------------------------------------------------------

    def new(self):
        if not self.confirm_leave():
            return
        self.source = self.make_source()
        self.current_id = None
        self.dirty = True
        self.fill_form()
        self.refresh()
        self.reload_list()

    def duplicate(self):
        if not self.confirm_leave():
            return
        source = self.draft()
        source["id"] = next_free_id(self._taken(), self.ID_PREFIX)
        source.pop("name", None)
        self.source = source
        self.current_id = None
        self.dirty = True
        self.fill_form()
        self.refresh()
        self.reload_list()

    def revert(self):
        if self.current_id:
            self.load(self.current_id)
        else:
            self.new()

    def delete(self):
        if self.archive.delete():
            return
        self.dirty = False
        self.reload_list()
        if self.ids:
            self.load(self.ids[0])
            self.reload_list(self.ids[0])
        else:
            self.new()

    def _after_archive(self):
        self.reload_list()
        self.new()

    def fail(self, message):
        return autosave.refuse(self, self.t(self.KEY), message)

    def save(self):
        source = self.draft()
        cid = source["id"]
        if not self.MODULE.ID_PATTERN.match(cid or ""):
            return self.fail(self.t("ld_taken", id=cid))
        taken = {t.lower() for t in self._taken()} - ({self.current_id.lower()} if self.current_id else set())
        if cid.lower() in taken:
            return self.fail(self.t("ld_taken", id=cid))
        if self.current_id and self.current_id != cid:
            if not autosave.ask_rename(self, self.t("ld_rename_title"), self.t("ld_rename", old=self.current_id, new=cid)):
                return False
        try:
            self.MODULE.check_source(source, "%s/%s.json" % (self.MODULE.FOLDER, cid))
        except (validation.ValidationError, ValueError) as exc:
            return self.fail(self.t("ld_invalid", error=str(exc)))
        folder = self.folder()
        folder.mkdir(parents=True, exist_ok=True)
        if self.current_id and self.current_id != cid:
            (folder / ("%s.json" % self.current_id)).unlink(missing_ok=True)
        (folder / ("%s.json" % cid)).write_text(json.dumps(source, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        self.source = source
        self.current_id = cid
        self.dirty = False
        self.export(self.t("ld_saved", id=cid))
        self.reload_list(select=cid)
        self.fill_command()
        return True

    def export(self, done):
        """calculations.json rebuilt with the case saved (registry.export): a failure is said, the source stays saved."""
        try:
            registry.export(project.current())
        except Exception as exc:  # broad: the exporter's own message is what helps, said in the status bar
            self.app.set_status(self.t("ld_export_failed", error=str(exc)))
            return
        self.app.set_status(done)

    def confirm_leave(self):
        return autosave.confirm(self.app, self, self.t("ld_unsaved_title"), self.t("ld_unsaved", id=self.identity.id.text().strip() or "?"))

    # --- state across a rebuild ---------------------------------------------------

    def view_state(self):
        return {"draft": copy.deepcopy(self.draft()), "current_id": self.current_id, "dirty": self.dirty,
                "splitter": self.splitter.sizes(), "empty_folders": list(self.empty_folders)}

    def restore(self, state):
        if not state:
            self.reload_list()
            if self.ids:
                self.list.select(self.ids[0])
                self.load(self.ids[0])
            else:
                self.fill_form()
                self.refresh()
            self.splitter.setSizes([2000, 6000, 4000])
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


# --- «Poids propre et surcharge» ----------------------------------------------------

LAYER_COLUMNS = ("kind", "library", "material", "thickness", "width", "spacing", "beside", "load")


class DeadLoadTab(LoadTab):
    """Poids propre et surcharge (issue #35, D-08: one tab for the two): a build-up of layers top to bottom, each g_k or a_k, weighed with SIA 261 Anhang A, Woodcore's materials library or the project's own -- whose card is here too -- and drawn as it is entered (dead_load_source, dead_load_svg)."""

    KEY = "tab_ac_selfweight"
    MODULE = dead_load_source
    ID_PREFIX = "AU-"
    LIST_KEY = "ld_list_dead"
    EMPTY_KEY = "ld_empty_dead"

    def build_inputs(self):
        box = cards.card(self.t("ld_box_layers"))
        column = QVBoxLayout(box)
        self.table = QTableWidget(0, len(LAYER_COLUMNS))
        self.table.setHorizontalHeaderLabels([self.t("ld_col_" + c) for c in LAYER_COLUMNS])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setMinimumHeight(220)
        column.addWidget(self.table)
        row = QHBoxLayout()
        for key, slot in (("ld_add", self.add_layer), ("ld_remove", self.remove_layer), ("ld_up", lambda: self.move_layer(-1)), ("ld_down", lambda: self.move_layer(1))):
            button = QPushButton(self.t(key))
            button.clicked.connect(slot)
            row.addWidget(button)
        row.addStretch(1)
        column.addLayout(row)
        column.addWidget(cards.note(self.t("ld_layers_hint")))
        self.form.addWidget(box)
        box = cards.card(self.t("ld_box_chosen"))
        form = cards.form(box)
        self.chosen_spin = self.spin(0.0, 1000.0, 3, 0.05, " kN/m²")
        self.chosen_spin.setSpecialValueText(self.t("ld_chosen_sum"))
        self.chosen_spin.valueChanged.connect(self.touch)
        form.addRow(self.t("ld_chosen"), self.linked(self.chosen_spin, "chosen", "kN/m²", "g_k+a_k"))
        self.form.addWidget(box)
        self.build_project_library()

    # the layers' table: one row per layer, each cell a widget that says what it holds
    def _material_items(self, library):
        if library == "sia261":
            return [((("%s, %s" % (e["group"], e["name"])) if e.get("group") else e["name"]) + " — %s %s" % (_n(e["value"]), e["unit"]), (e["id"], "")) for e in materials.norm_entries()]
        if library == "belastungsannahmen":
            return [("%s — %s (%s %s)" % (e["ebene"], e["material"], _n(e["mass"]), e["unit"]), (e["material"], e["ebene"])) for e in materials.workbook_library()["materials"]]
        if library == "project":
            try:
                entries = materials.read_project()["materials"]
            except validation.ValidationError:
                entries = []
            return [("%s — %s %s" % (e.get("name") or e["id"], _n(e["value"]), e["unit"]), (e["id"], "")) for e in entries]
        return []

    def _spin_cell(self, value, maximum=100_000.0, decimals=1, special=True, suffix=""):
        box = self.spin(0.0, maximum, decimals, 1.0, suffix)
        if special:
            box.setSpecialValueText(self.t("ld_none"))
        box.setValue(float(value or 0))
        box.valueChanged.connect(self.touch)
        return box

    def _set_row(self, row, layer):
        kind = QComboBox()
        for k in ("gk", "ak"):
            kind.addItem(self.t("ld_kind_" + k), k)
        kind.setCurrentIndex(max(kind.findData(layer.get("kind")), 0))
        kind.currentIndexChanged.connect(self.touch)
        library = QComboBox()
        for lib in dead_load_source.LIBRARIES:
            library.addItem(self.t("ld_lib_" + lib), lib)
        library.setCurrentIndex(max(library.findData(layer.get("library")), 0))
        material = QComboBox()
        material.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        material.setMinimumContentsLength(18)      # the column stretches; the popup is as wide as its longest line
        material.view().setMinimumWidth(460)
        material.setEditable(layer.get("library") == "direct")
        self._fill_materials(material, layer.get("library"), (layer.get("material") or "", layer.get("ebene") or ""))
        material.currentIndexChanged.connect(self.touch)
        material.editTextChanged.connect(self.touch)
        library.currentIndexChanged.connect(lambda _i, m=material, l=library: self._library_changed(m, l))
        beside = QCheckBox()
        beside.setChecked(bool(layer.get("beside")))
        beside.toggled.connect(self.touch)
        # the four numbers of a layer, each with its button (issue #42): its links are the layer's own, carried by its row
        found = links.links_of(layer)
        numbers = {}
        for key, unit, cell in (("thickness", "mm", self._spin_cell(layer.get("thickness"))), ("width", "mm", self._spin_cell(layer.get("width"))),
                                ("spacing", "mm", self._spin_cell(layer.get("spacing"))), ("load", "kN/m²", self._spin_cell(layer.get("load"), 1000.0, 3))):
            numbers[key] = self.linked(cell, key, unit, self.t("ld_col_" + key), store=False)
            numbers[key].set_link(found.get(key), self.link_values() if found else {})
        cells = (kind, library, material, numbers["thickness"], numbers["width"], numbers["spacing"], beside, numbers["load"])
        for column, widget in enumerate(cells):
            self.table.setCellWidget(row, column, widget)

    def _fill_materials(self, combo, library, wanted):
        combo.blockSignals(True)
        combo.clear()
        if library == "direct":
            combo.setEditable(True)
            combo.setEditText(wanted[0])
        else:
            combo.setEditable(False)
            for text, data in self._material_items(library):
                combo.addItem(text, data)
            index = combo.findData(wanted)
            if index < 0:
                index = next((i for i in range(combo.count()) if combo.itemData(i)[0] == wanted[0]), -1)
            if index < 0 and wanted[0]:
                combo.addItem("%s (?)" % wanted[0], wanted)      # a material no library lists any more is kept, and the result says why
                index = combo.count() - 1
            combo.setCurrentIndex(max(index, 0))
        combo.blockSignals(False)

    def _library_changed(self, material, library):
        self._fill_materials(material, library.currentData(), ("", ""))
        self.touch()

    def _layer_of(self, row):
        w = [self.table.cellWidget(row, c) for c in range(len(LAYER_COLUMNS))]
        library = w[1].currentData()
        if library == "direct":
            material, ebene = w[2].currentText().strip(), ""
        else:
            material, ebene = w[2].currentData() or ("", "")
        number = lambda box: getattr(box, "spin", box).value() or None
        layer = {"kind": w[0].currentData(), "library": library, "material": material, "ebene": ebene,
                 "thickness": number(w[3]), "width": number(w[4]), "spacing": number(w[5]), "beside": w[6].isChecked(),
                 "load": number(w[7]) if library == "direct" else None}
        found = {key: w[c].link() for key, c in (("thickness", 3), ("width", 4), ("spacing", 5), ("load", 7))
                 if hasattr(w[c], "link") and w[c].link() is not None}
        if found:
            layer[links.LINKS] = found
        return layer

    def add_layer(self):
        layers = self.current_layers()
        layers.append(dead_load_source.new_layer())
        self.fill_layers(layers)
        self.touch()

    def remove_layer(self):
        row = self.table.currentRow()
        layers = self.current_layers()
        if 0 <= row < len(layers):
            del layers[row]
            self.fill_layers(layers)
            self.touch()

    def move_layer(self, step):
        row = self.table.currentRow()
        layers = self.current_layers()
        target = row + step
        if 0 <= row < len(layers) and 0 <= target < len(layers):
            layers[row], layers[target] = layers[target], layers[row]
            self.fill_layers(layers)
            self.table.setCurrentCell(target, 0)
            self.touch()

    def current_layers(self):
        return [self._layer_of(r) for r in range(self.table.rowCount())]

    def fill_layers(self, layers):
        was, self.loading = self.loading, True
        self.table.setRowCount(len(layers))
        for row, layer in enumerate(layers):
            self._set_row(row, layer)
        self.loading = was

    def fill_inputs(self, s):
        self.fill_layers(s.get("layers") or [])
        self.chosen_spin.setValue(float(s.get("chosen") or 0))
        self.fill_project_library()

    def draft_inputs(self, s):
        s["layers"] = self.current_layers()
        s["chosen"] = self.chosen_spin.value() or None

    # the project's own library: a card of its own, saved apart from the build-up (materials.json is the project's, every build-up reads it)
    def build_project_library(self):
        box = cards.card(self.t("ld_box_project"))
        column = QVBoxLayout(box)
        column.addWidget(cards.note(self.t("ld_project_hint")))
        self.project_table = QTableWidget(0, 5)
        self.project_table.setHorizontalHeaderLabels([self.t("ld_col_" + c) for c in ("id", "name", "value", "unit", "source")])
        self.project_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.project_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.project_table.setMinimumHeight(120)
        column.addWidget(self.project_table)
        row = QHBoxLayout()
        add = QPushButton(self.t("ld_add_material"))
        add.clicked.connect(self.add_project_material)
        save = QPushButton(self.t("ld_save_materials"))
        save.clicked.connect(self.save_project_library)
        row.addWidget(add)
        row.addWidget(save)
        row.addStretch(1)
        column.addLayout(row)
        self.form.addWidget(box)

    def fill_project_library(self):
        from PySide6.QtWidgets import QTableWidgetItem
        try:
            entries = materials.read_project()["materials"]
        except validation.ValidationError:
            entries = []
        self.project_table.setRowCount(len(entries))
        for r, e in enumerate(entries):
            for c, key in enumerate(("id", "name", "value", "unit", "source")):
                if key == "unit":
                    combo = QComboBox()
                    for unit in materials.UNITS:
                        combo.addItem(unit, unit)
                    combo.setCurrentIndex(max(combo.findData(e.get("unit")), 0))
                    self.project_table.setCellWidget(r, c, combo)
                else:
                    self.project_table.setItem(r, c, QTableWidgetItem(str(e.get(key, "")) if e.get(key) is not None else ""))

    def add_project_material(self):
        from PySide6.QtWidgets import QTableWidgetItem
        r = self.project_table.rowCount()
        self.project_table.setRowCount(r + 1)
        self.project_table.setItem(r, 0, QTableWidgetItem("M%d" % (r + 1)))
        self.project_table.setItem(r, 1, QTableWidgetItem(""))
        self.project_table.setItem(r, 2, QTableWidgetItem("500"))
        combo = QComboBox()
        for unit in materials.UNITS:
            combo.addItem(unit, unit)
        self.project_table.setCellWidget(r, 3, combo)
        self.project_table.setItem(r, 4, QTableWidgetItem(""))

    def project_entries(self):
        out = []
        for r in range(self.project_table.rowCount()):
            text = lambda c: (self.project_table.item(r, c).text().strip() if self.project_table.item(r, c) else "")
            try:
                value = float(text(2).replace(",", "."))
            except ValueError:
                value = 0.0
            entry = {"id": text(0), "name": text(1) or text(0), "value": value, "unit": self.project_table.cellWidget(r, 3).currentData()}
            if text(4):
                entry["source"] = text(4)
            out.append(entry)
        return out

    def save_project_library(self):
        data = {"schema_version": materials.PROJECT_SCHEMA_VERSION, "materials": self.project_entries()}
        try:
            materials.check_project(data)
        except validation.ValidationError as exc:
            return self.fail(self.t("ld_invalid", error=str(exc)))
        path = materials.project_file()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        layers = self.current_layers()
        self.fill_layers(layers)            # the project's materials offered at once in the layers
        self.app.set_status(self.t("ld_materials_saved"))
        self.refresh()
        return True


# --- «Neige» ---------------------------------------------------------------------


class SnowTab(LoadTab):
    """Neige (issue #36): the site, the exposure, the roof of Figur 3 and whether the snow can slide off; the loads of the two models computed at once (snow_source), and their sketch, shown here and never printed (snow_source.sketch, spec 2026-10-14-neige-vent-affichage-altitude, D-03); a site above 5.1.4's limit is warned of in the callout (REQ-004). The curved roof is the third column of Figur 3 (D-01)."""

    KEY = "tab_ac_snow"
    MODULE = snow_source
    ID_PREFIX = "SN-"
    LIST_KEY = "ld_list_snow"
    EMPTY_KEY = "ld_empty_snow"
    FIGURE_KEY = "ld_figure_snow"

    def build_inputs(self):
        c = sia261_snow.clause()
        box = cards.card(self.t("ld_box_site"))
        form = cards.form(box)
        self.h0_spin = self.spin(0.0, 3000.0, 0, 10.0, " m")
        self.h0_spin.valueChanged.connect(self.touch)
        form.addRow(self.t("ld_h0"), self.linked(self.h0_spin, "h_0", "m", "h_0"))
        self.correction_box = QComboBox()
        for value in c["corrections"]["values"]:
            self.correction_box.addItem("± 0 m" if value == 0 else "%+g m" % value, value)
        self.correction_box.currentIndexChanged.connect(self.touch)
        form.addRow(self.t("ld_correction"), self.correction_box)
        self.exposure_box = QComboBox()
        for e in c["exposure"]["choices"]:
            self.exposure_box.addItem("%s — C_e = %s" % (self.tl(e["label"]), _n(e["value"])), e["id"])
        self.exposure_box.currentIndexChanged.connect(self.touch)
        form.addRow(self.t("ld_exposure"), self.exposure_box)
        self.ct_spin = self.spin(0.1, 1.0, 2, 0.05)
        self.ct_spin.valueChanged.connect(self.touch)
        form.addRow(self.t("ld_ct"), self.linked(self.ct_spin, "c_t", "", "C_t"))
        self.form.addWidget(box)
        box = cards.card(self.t("ld_box_roof"))
        self.roof_form = cards.form(box)
        self.roof_box = QComboBox()
        for roof in snow_source.ROOFS:
            self.roof_box.addItem(self.tl(snow_source.ROOF_WORDS[roof]), roof)
        self.roof_box.currentIndexChanged.connect(self.on_roof)
        self.roof_form.addRow(self.t("ld_roof"), self.roof_box)
        self.length_spin = self.spin(0.1, 1000.0, 1, 1.0, " m")
        self.width_spin = self.spin(0.1, 1000.0, 1, 1.0, " m")
        self.alpha1_spin = self.spin(0.0, 90.0, 1, 1.0, " °")
        self.alpha2_spin = self.spin(0.0, 90.0, 1, 1.0, " °")
        for key, spin, field, unit in (("ld_length", self.length_spin, "length", "m"), ("ld_width", self.width_spin, "width", "m"),
                                       ("ld_alpha1", self.alpha1_spin, "alpha_1", "°"), ("ld_alpha2", self.alpha2_spin, "alpha_2", "°")):
            spin.valueChanged.connect(self.touch)
            self.roof_form.addRow(self.t(key), self.linked(spin, field, unit, field))
        self.sliding_box = QComboBox()
        for sliding in snow_source.SLIDING:
            self.sliding_box.addItem(self.tl(snow_source.SLIDING_WORDS[sliding]), sliding)
        self.sliding_box.currentIndexChanged.connect(self.touch)
        self.roof_form.addRow(self.t("ld_sliding"), self.sliding_box)
        # SIA 261 5.3.6: a stepped roof -- said by the report, not computed (spec 2026-10-12-audit-issues-47-48-49, D-04)
        self.step_box = QCheckBox(self.t("ld_height_step"))
        self.step_box.toggled.connect(self.touch)
        self.roof_form.addRow("", self.step_box)
        self.roof_form.addRow("", cards.note(self.t("ld_roof_hint")))
        self.form.addWidget(box)

    def on_roof(self, *_args):
        self.update_roof_rows()
        self.touch()

    def update_roof_rows(self):
        fields = snow_source.ROOF_FIELDS[self.roof_box.currentData() or "duo"]
        for key, spin in (("length", self.length_spin), ("width", self.width_spin), ("alpha_1", self.alpha1_spin), ("alpha_2", self.alpha2_spin)):
            self.roof_form.setRowVisible(self.row_of(spin), key in fields)

    def fill_inputs(self, s):
        self.h0_spin.setValue(float(s.get("h_0") or 0))
        self.correction_box.setCurrentIndex(max(self.correction_box.findData(s.get("correction")), 0))
        self.exposure_box.setCurrentIndex(max(self.exposure_box.findData(s.get("exposure")), 0))
        self.ct_spin.setValue(float(s.get("c_t") or 1.0))
        self.roof_box.setCurrentIndex(max(self.roof_box.findData(s.get("roof")), 0))
        for key, spin, default in (("length", self.length_spin, 10.0), ("width", self.width_spin, 10.0), ("alpha_1", self.alpha1_spin, 0.0), ("alpha_2", self.alpha2_spin, 0.0)):
            spin.setValue(float(s.get(key) if s.get(key) is not None else default))
        self.sliding_box.setCurrentIndex(max(self.sliding_box.findData(s.get("sliding")), 0))
        self.step_box.setChecked(bool(s.get("height_step")))
        self.update_roof_rows()

    def draft_inputs(self, s):
        roof = self.roof_box.currentData()
        fields = snow_source.ROOF_FIELDS[roof]
        s.update(h_0=self.h0_spin.value(), correction=self.correction_box.currentData(), exposure=self.exposure_box.currentData(),
                 c_t=self.ct_spin.value(), roof=roof, sliding=self.sliding_box.currentData())
        for key, spin in (("length", self.length_spin), ("width", self.width_spin), ("alpha_1", self.alpha1_spin), ("alpha_2", self.alpha2_spin)):
            s[key] = spin.value() if key in fields else None
        # written only when true (D-19): a roof without a step keeps its file and its schema 1.0 / 1.1
        if self.step_box.isChecked():
            s["height_step"] = True
        else:
            s.pop("height_step", None)


# --- «Vent» ----------------------------------------------------------------------


class WindTab(LoadTab):
    """Vent (issue #37): the site's q_p0 and terrain category, the building's b, d, h and z, the table of SIA 261 Annexe C its coefficients are read from -- any building's (D-06) -- and c_d; q_p, c_red of Figur 9 and the global and local forces computed at once (wind_source)."""

    KEY = "tab_ac_wind"
    MODULE = wind_source
    ID_PREFIX = "WI-"
    LIST_KEY = "ld_list_wind"
    EMPTY_KEY = "ld_empty_wind"

    def build_inputs(self):
        clause = sia261_wind.clause()
        box = cards.card(self.t("ld_box_site"))
        form = cards.form(box)
        self.qp0_spin = self.spin(0.1, 10.0, 2, 0.05, " kN/m²")
        self.qp0_spin.valueChanged.connect(self.touch)
        form.addRow(self.t("ld_qp0"), self.linked(self.qp0_spin, "q_p0", "kN/m²", "q_p0"))
        self.terrain_box = QComboBox()
        for t in clause["terrain"]["categories"]:
            self.terrain_box.addItem("%s — z_g = %s m, α_r = %s" % (t["id"], _n(t["z_g"]), _n(t["alpha_r"])), t["id"])
        self.terrain_box.currentIndexChanged.connect(self.touch)
        form.addRow(self.t("ld_terrain"), self.terrain_box)
        self.form.addWidget(box)
        box = cards.card(self.t("ld_box_building"))
        form = cards.form(box)
        self.b_spin, self.d_spin, self.h_spin = (self.spin(0.1, 1000.0, 2, 0.5, " m") for _ in range(3))
        self.z_spin = self.spin(0.0, 200.0, 2, 0.5, " m")
        self.z_spin.setSpecialValueText(self.t("ld_z_h"))
        for key, spin, field in (("ld_b", self.b_spin, "b"), ("ld_d", self.d_spin, "d"), ("ld_h", self.h_spin, "h"), ("ld_z", self.z_spin, "z")):
            spin.valueChanged.connect(self.touch)
            form.addRow(self.t(key), self.linked(spin, field, "m", field))
        self.table_box = QComboBox()
        self.table_box.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.table_box.setMinimumContentsLength(24)
        self.table_box.view().setMinimumWidth(520)
        for number in sia261_wind.NUMBERS:
            table = sia261_wind.table(number)
            self.table_box.addItem("%s — h : b : d = %s, %s" % (number, table["ratio"], table["roof"]), number)
        self.table_box.currentIndexChanged.connect(self.touch)
        form.addRow(self.t("ld_table"), self.table_box)
        self.cd_spin = self.spin(0.5, 3.0, 2, 0.05)
        self.cd_spin.valueChanged.connect(self.touch)
        form.addRow(self.t("ld_cd"), self.linked(self.cd_spin, "c_d", "", "c_d"))
        form.addRow("", cards.note(self.t("ld_wind_hint")))
        self.form.addWidget(box)

    def fill_inputs(self, s):
        self.qp0_spin.setValue(float(s.get("q_p0") or 0))
        self.terrain_box.setCurrentIndex(max(self.terrain_box.findData(s.get("terrain")), 0))
        for key, spin in (("b", self.b_spin), ("d", self.d_spin), ("h", self.h_spin)):
            spin.setValue(float(s.get(key) or 0))
        self.z_spin.setValue(float(s.get("z") or 0))
        self.table_box.setCurrentIndex(max(self.table_box.findData(s.get("table")), 0))
        self.cd_spin.setValue(float(s.get("c_d") or 1.0))

    def draft_inputs(self, s):
        s.update(q_p0=self.qp0_spin.value(), terrain=self.terrain_box.currentData(), b=self.b_spin.value(), d=self.d_spin.value(),
                 h=self.h_spin.value(), z=self.z_spin.value() or None, table=self.table_box.currentData(), c_d=self.cd_spin.value())
