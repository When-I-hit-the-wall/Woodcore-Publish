"""The views of a tab, chosen in the top bar (docs/ui/window.md §10quater, v0.117).

The engineer's request of 07.10.2026: «il y a pour l'instant trop d'informations dans les onglets. On se perd un peu». A tab that declares views shows one task at a time -- the plans their documents, their drawing, their Typst command («Affichage») and their export sheets; a calculation its inputs and its result, then how the report prints it -- and the window shows, left of FR · DE · EN, one segmented switch (chrome.SegmentedSwitch) holding the views of the tab in front.

**The contract** (ARCH-001 of the spec `docs/requirements/active/2026-10-07-vues-onglets-slider-et-volets.md`). A tab declares `VIEWS`, a tuple of view keys taken from `WORDS` below, the first being its default, and answers `set_view(key, enter=True)`; it keeps the key it shows in `view`. `enter` False is the window being built: the view is a state, and what it opens or compiles waits for the tab's `showEvent`. Where the tab changes its view itself -- a frame of a document opening its plan -- it calls `app.view_changed(self)` and the switch follows. Nothing is compiled while the window is built (review A10). A tab without `VIEWS` shows no switch.

The view a tab shows is remembered in the user's settings (`views`, by tab key), never in the project: it is how the engineer likes to work, not what the project is.
"""

# Every view a tab may declare, and the key of its name in STRINGS. The keys are identifiers, never shown.
WORDS = {
    "import": "view_import",     # a plan's documents
    "draw": "view_draw",         # a plan's or a model's drawing
    "typst": "view_display",     # a plan's #show-plan, compiled: named «Affichage» as every tab's display view (the engineer, 07.10.2026: «renomme en haut dans les 4 affichages "Typst" en "Affichage"»); the key stays `typst`, remembered in the settings
    "export": "view_export",     # a plan's export sheets and their bundles
    "calc": "view_calc",         # a calculation's inputs and its Python result
    "entry": "view_entry",       # what is typed by hand: a position, a revision
    "data": "view_data",         # what the variables tab lists
    "display": "view_display",   # how the report prints it: the compiled call, its options, the call to copy
}
# What each view's button says when the pointer rests on it. Named here and not composed, so tests/test_i18n.py finds every key by the code that names it.
TIPS = {
    "import": "view_import_tip", "draw": "view_draw_tip", "typst": "view_typst_tip", "export": "view_export_tip",
    "calc": "view_calc_tip", "entry": "view_entry_tip", "data": "view_data_tip", "display": "view_display_tip",
}

PLAN_VIEWS = ("draw", "import", "typst", "export")   # «Dessin» first as the default, shown in ORDER below
CALC_VIEWS = ("calc", "display")
DRAW_VIEWS = ("draw", "display")
ENTRY_VIEWS = ("entry", "display")
DATA_VIEWS = ("data", "display")

# The order the switch shows a tab's views in, whatever order the tab declares them in (its first being its default): the engineer's own for the plans, «document import, dessin, typst et document export».
ORDER = ("import", "draw", "typst", "export", "calc", "entry", "data", "display")

STRINGS = {
    "fr": {
        "view_switch": "Vue de l'onglet : une tâche à la fois",
        "view_import": "Import",
        "view_import_tip": "Les documents importés : leurs pages, leurs cadres et leurs calques",
        "view_draw": "Dessin",
        "view_draw_tip": "Le dessin et ses outils",
        "view_typst_tip": "La commande Typst d'un plan, compilée, et toutes ses options",
        "view_export": "Export",
        "view_export_tip": "Les documents d'export : les feuilles et leurs dossiers",
        "view_calc": "Calcul",
        "view_calc_tip": "Les données du calcul et son résultat Python",
        "view_entry": "Saisie",
        "view_entry_tip": "Ce qui est saisi à la main",
        "view_data": "Données",
        "view_data_tip": "Ce que l'export et les documents contiennent",
        "view_display": "Affichage",
        "view_display_tip": "Comme le rapport l'imprime : l'aperçu compilé, les options de la commande et la commande à copier",
        "pane_collapse": "Replier le volet",
        "pane_expand": "Déplier le volet",
    },
    "de": {
        "view_switch": "Ansicht des Registers: eine Aufgabe nach der anderen",
        "view_import": "Import",
        "view_import_tip": "Die importierten Dokumente: ihre Seiten, Rahmen und Ebenen",
        "view_draw": "Zeichnung",
        "view_draw_tip": "Die Zeichnung und ihre Werkzeuge",
        "view_typst_tip": "Der Typst-Befehl eines Plans, kompiliert, mit allen Optionen",
        "view_export": "Export",
        "view_export_tip": "Die Exportdokumente: die Blätter und ihre Ordner",
        "view_calc": "Berechnung",
        "view_calc_tip": "Die Eingaben der Berechnung und ihr Python-Ergebnis",
        "view_entry": "Erfassung",
        "view_entry_tip": "Was von Hand erfasst wird",
        "view_data": "Daten",
        "view_data_tip": "Was der Export und die Dokumente enthalten",
        "view_display": "Darstellung",
        "view_display_tip": "Wie der Bericht es druckt: die kompilierte Vorschau, die Optionen des Befehls und der Befehl zum Kopieren",
        "pane_collapse": "Bereich einklappen",
        "pane_expand": "Bereich ausklappen",
    },
    "en": {
        "view_switch": "The tab's view: one task at a time",
        "view_import": "Import",
        "view_import_tip": "The imported documents: their pages, frames and layers",
        "view_draw": "Drawing",
        "view_draw_tip": "The drawing and its tools",
        "view_typst_tip": "A plan's Typst command, compiled, with all its options",
        "view_export": "Export",
        "view_export_tip": "The export documents: the sheets and their folders",
        "view_calc": "Calculation",
        "view_calc_tip": "The calculation's inputs and its Python result",
        "view_entry": "Entry",
        "view_entry_tip": "What is typed in by hand",
        "view_data": "Data",
        "view_data_tip": "What the export and the documents hold",
        "view_display": "Display",
        "view_display_tip": "As the report prints it: the compiled preview, the command's options and the command to copy",
        "pane_collapse": "Fold the pane",
        "pane_expand": "Unfold the pane",
    },
}


def declared(tab):
    """The views `tab` declares, () for a tab that has none."""
    return tuple(getattr(tab, "VIEWS", ()) or ())


def items(tab, t):
    """The switch's buttons for `tab`: [(key, name, tip)] in ORDER, its words read with the window's `t`."""
    keys = declared(tab)
    return [(key, t(WORDS[key]), t(TIPS[key])) for key in ORDER if key in keys]


def remembered(settings, tab_key, tab):
    """The view `tab` was last left in, as the user's settings keep it by tab key -- or its default, the first it declares, where none is kept or the one kept is not one of its views."""
    keys = declared(tab)
    kept = settings.get("views") if isinstance(settings, dict) else None
    view = kept.get(tab_key) if isinstance(kept, dict) else None
    return view if view in keys else (keys[0] if keys else None)


def with_view(settings, tab_key, view):
    """`settings` with `tab_key`'s view set to `view`, the other tabs' kept: the dict merged, never replaced (review A11)."""
    kept = dict(settings.get("views") or {}) if isinstance(settings, dict) else {}
    kept[tab_key] = view
    return {**(settings or {}), "views": kept}
