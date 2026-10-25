"""«Matériaux» (issue #110, spec docs/requirements/active/2026-10-24-onglet-materiaux.md): the engineer's library of materials for every project of his computer, and the materials Woodcore ships, on the type «Bibliothèque» (library_tab.LibraryTab).

On the left the list by category, searched and filtered (materials_list.MaterialList); in the centre the sheet of the material selected, in folds (materials_sheet.MaterialSheet); on the right its state, its source, where it is offered and where it is saved (materials_pane.MaterialModules) -- the layout A the engineer chose on 24.10.2026. What a material is, its design values, its state and its search are the domain's (calc/domains/materials_*.py); the library lives in `%APPDATA%\\Woodcore\\materials\\` (materials_user), not in the project, which this tab never reads nor writes (`TabSpec.project=False`). Its words are `mat_` (materials_tab_words.py). A thin class of parameters on its type.
"""

import materials_tab_words
from domains import materials_library
from library_tab import LibraryTab
from materials_list import MaterialList
from materials_pane import MaterialModules
from materials_sheet import MaterialSheet

STRINGS = materials_tab_words.STRINGS


class MaterialsTab(LibraryTab):
    """«Matériaux» -- see the module's docstring."""

    KEY = "tab_materials"
    STORE = materials_library
    PREFIX = "mat_"
    SERVICES = (MaterialList, MaterialSheet, MaterialModules)
