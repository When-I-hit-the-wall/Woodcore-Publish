"""«Poids propre et surcharge» (issue #35, D-08: one tab for the two), built on the type «Calcul» by issue #95 (spec 2026-10-23-onglets-types-et-services, REQ-003; docs/ui/building-a-tab.md).

A build-up of layers top to bottom, each g_k or a_k, weighed with a material of the «Matériaux» tab -- Woodcore's or the engineer's own, the project keeping a copy of his (calc/domains/dead_load_source.py, materials_project.py; issue #110). Its form is not declared: the table of its layers, at the keyboard, takes the declared form's place (layer_table.LayerTable, `calc_tab.swap`; issue #111), and under it the card of the engineer's materials whose library has changed since the project took its copy (material_copies.MaterialCopies); the tab creates no material. On the right, in this order (UI-002): the state of the calculation, «Couche n» -- the options of the line open, given by the table --, «Coupe | Contributions» (layer_section.LayerSection, in the place of its type's drawing: the section at its true proportion, the one the export prints, drawn at the module's width, ⤢ a window that follows its size), then the results. «⊞ Vue d'ensemble» at the head of the list shows every build-up at a glance in the centre (case_overview.Overview); «Nouveau» starts from a Lignum template, one of «Mes modèles» or an empty build-up (template_picker.TemplatePicker). «Affichage» is the case's file, `Permanent-loads/<id>.typ`, line by line, written again at every save (`unfold.AUTO_REGENERATE`, D-21).

Its words are `ld_` (load_words.STRINGS), the type's `ct_`. What it adds to its type is its parameters and the two services in place of the form: not one method (REQ-005).
"""

import calc_tab
import load_words
from calc_form import DeclaredForm
from calc_modules import Modules
from case_list import CaseList
from case_overview import Overview
from domains import dead_load_source
from layer_section import LayerSection
from layer_table import LayerTable
from material_copies import MaterialCopies
from template_picker import TemplatePicker

# The words of the list's own menus and dialogs, which the list reads off the tab's module: the loads' (ld_)
STRINGS = load_words.STRINGS


class DeadLoadTab(calc_tab.CalcTab):
    """«Poids propre et surcharge» -- see the module's docstring."""

    KEY = "tab_ac_selfweight"
    MODULE = dead_load_source
    ID_PREFIX = "AU-"
    LIST_KEY = "ld_list_dead"
    EMPTY_KEY = "ld_empty_dead"
    PREFIX = "ld_"
    SERVICES = calc_tab.before(calc_tab.before(calc_tab.swap(calc_tab.CalcTab.SERVICES, DeclaredForm, LayerTable), Modules, LayerSection), CaseList, Overview) + (MaterialCopies, TemplatePicker)
