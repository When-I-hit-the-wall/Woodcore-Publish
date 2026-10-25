"""«Vent» (issue #37; rethought by issue #100, spec docs/requirements/completed/2026-10-23-onglet-vent-briques.md): the second tab of calculation on the type «Calcul», described by its domain and never copied (docs/ui/calc-tab.md, docs/ui/tab-wind.md).

Everything it shows is its domain's (calc/domains/wind_source.py, which takes its declaration, its blocks, its links and its chart from calc/domains/wind_view.py), drawn by the services of its type (calc/tools/calc_tab.py): the form in four sections -- the basic data, the building of Annexe C with the figure of the norm and the model in 3D, the reduction and force coefficients with the global forces and their result in 3D, the pressure coefficients with the detail per φ, the openings and the result in 3D of the loads --; on the right the state, the results, Figure 9 as a chart, the excerpts of SIA 261 and the blocks pinned; «Affichage» the case's file, `Variable-loads/Wind/<id>.typ`, line by line.

Its words are `wi_` (wind_tab_words.py), the type's `ct_`, the list's `ld_` (load_words.py). What it adds to its type is its key, its domain and its list's words: not one method (REQ-005 of spec 2026-10-23-onglets-types-et-services).
"""

import calc_tab
import load_words
from domains import wind_source

# The words of the list's own menus and dialogs, which the list reads off the tab's module: the loads' (ld_)
STRINGS = load_words.STRINGS


class WindTab(calc_tab.CalcTab):
    """«Vent» -- see the module's docstring."""

    KEY = "tab_ac_wind"
    MODULE = wind_source
    ID_PREFIX = "WL-"
    LIST_KEY = "wi_list"
    EMPTY_KEY = "wi_empty"
