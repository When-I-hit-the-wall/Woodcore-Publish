"""«Neige» (issue #36; reworked by issue #94, spec 2026-10-22-onglet-neige-type): the first tab of calculation built on the common base, described by its domain and never copied (docs/ui/calc-tab.md, docs/ui/tab-snow.md).

Everything it shows is its domain's declaration (calc/domains/snow_source.py `declaration`, `messages`, `results`, `figure_svg`, `tile_svg`, `chart`) drawn by the base (calc/tools/calc_tab.py): the building first, its length and width with Figur 4 under their ⓘ (T37); the site -- h₀, Δh of Anhang D whose ⓘ opens the map of 261.sia.ch at Ctrl+click, C_e's three buttons and a value of the engineer's own (T38), C_T --; the roof among the five tiles drawn as Figur 3 draws them (T39), its slopes, the sliding, a height step. On the right the modules: the state of the calculation, the results, the column of Figur 3 of the case's roof -- the drawing the export prints at the head of the case's file (D-31, D-32) --, Figur 2 as an interactive chart, and the excerpts of SIA 261 pinned from a bubble. «Affichage» is the case's file, `Variable-loads/Snow/<id>.typ`, line by line (calc/tools/domain_file_display.py).

Its words are `sn_` (snow_tab_words.py), the base's `ct_`. What it adds to the base is its key, its domain and its list's words: nothing of the snow is written in the base, and nothing of the base here.
"""

from PySide6.QtWidgets import QWidget

import calc_tab
import load_tab
from domains import snow_source

# The words of the list's own menus and dialogs, which source_editor.list_words reads off the tab's module: the loads' (ld_), the list of the roofs being a list of loads
STRINGS = load_tab.STRINGS


class SnowTab(calc_tab.DeclaredTabMixin, load_tab.LoadTab):
    """«Neige» -- see the module's docstring."""

    KEY = "tab_ac_snow"
    MODULE = snow_source
    ID_PREFIX = "SN-"
    LIST_KEY = "sn_list"
    EMPTY_KEY = "sn_empty"
