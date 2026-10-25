"""The views of a tab, chosen in the top bar (docs/ui/window.md §10quater, v0.117).

The engineer's request of 07.10.2026: «il y a pour l'instant trop d'informations dans les onglets. On se perd un peu». A tab that declares views shows one task at a time -- the plans their documents, their drawing, their Typst command («Affichage») and their export sheets; a calculation its inputs and its result, then how the report prints it -- and the window shows, left of FR · DE · EN, one segmented switch (chrome.SegmentedSwitch) holding the views of the tab in front.

**The contract** (ARCH-001 of the spec `docs/requirements/active/2026-10-07-vues-onglets-slider-et-volets.md`). A tab declares `VIEWS`, a tuple of view keys taken from `WORDS` below, the first being its default, and answers `set_view(key, enter=True)`; it keeps the key it shows in `view`. `enter` False is the window being built: the view is a state, and what it opens or compiles waits for the tab's `showEvent`. Where the tab changes its view itself -- a frame of a document opening its plan -- it calls `app.view_changed(self)` and the switch follows. Nothing is compiled while the window is built (review A10). A tab without `VIEWS` shows no switch.

**Every arrival is on the work** (issue #86, the engineer, 21.10.2026: «lorsque l'on ouvre un onglet, on est toujours en mode calcul et pas en mode affichage»). A tab is in its first view -- «Calcul», «Dessin», «Saisie» or «Données» -- each time it is brought forward, so that arriving compiles nothing; the view chosen holds while the tab stays in front, through a save, an export, a change of language or a rebuild of the window. The window puts a tab back in its first view as it is **left** (`MainWindow.reset_view`), never as it arrives: Qt shows the page before it says the tab changed, and a view put back then would come after the compilation. Until 0.121 the view a tab was left in was kept in the user's settings (`views`, v0.117); it is no longer read nor written, and a key `views` still in a user's settings is left as it is.
"""

# Every view a tab may declare, and the key of its name in STRINGS. The keys are identifiers, never shown.
WORDS = {
    "import": "view_import",     # a plan's documents
    "draw": "view_draw",         # a plan's or a model's drawing
    "typst": "view_display",     # a plan's #show-plan, compiled: named «Affichage» as every tab's display view (the engineer, 07.10.2026: «renomme en haut dans les 4 affichages "Typst" en "Affichage"»); the key stays `typst`
    "export": "view_export",     # a plan's export sheets and their bundles
    "calc": "view_calc",         # a calculation's inputs and its Python result
    "form": "view_form",         # a domain of the «Domaines» tab as a form, a row a line of its file (issue #113)
    "code": "view_code",         # the same domain as its file, coloured, the arguments of the line of the cursor beside it (issue #113)
    "entry": "view_entry",       # what is typed by hand: a position, a revision
    "display": "view_display",   # how the report prints it: the compiled call, its options, the call to copy
    "details": "view_details",   # the «Projet» tab's cards: the title page, the language, the templates, the documents (issue #87)
    "templates": "view_templates",   # the «Projet» tab's preview of a document with the templates chosen (issue #88)
}
# What each view's button says when the pointer rests on it. Named here and not composed, so tests/test_i18n.py finds every key by the code that names it.
TIPS = {
    "import": "view_import_tip", "draw": "view_draw_tip", "typst": "view_typst_tip", "export": "view_export_tip",
    "calc": "view_calc_tip", "form": "view_form_tip", "code": "view_code_tip", "entry": "view_entry_tip", "display": "view_display_tip",
    "details": "view_details_tip", "templates": "view_templates_tip",
}

PLAN_VIEWS = ("draw", "import", "typst", "export")   # «Dessin» first as the default, shown in ORDER below
CALC_VIEWS = ("calc", "display")
DRAW_VIEWS = ("draw", "display")
ENTRY_VIEWS = ("entry", "display")

# The order the switch shows a tab's views in, whatever order the tab declares them in (its first being its default): the engineer's own for the plans, «document import, dessin, typst et document export».
ORDER = ("details", "templates", "import", "draw", "typst", "export", "form", "code", "calc", "entry", "display")

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
        "view_form": "Formulaire",
        "view_form_tip": "Le domaine en rangées, une par ligne de son fichier : symboles, calculs et résultats",
        "view_code": "Code",
        "view_code_tip": "Le fichier .typ du domaine lui-même, coloré, et les arguments de la ligne du curseur",
        "view_entry": "Saisie",
        "view_entry_tip": "Ce qui est saisi à la main",
        "view_display": "Affichage",
        "view_display_tip": "Comme le rapport l'imprime : l'aperçu compilé, les options de la commande et la commande à copier",
        "view_details": "Informations",
        "view_details_tip": "Les données de base du projet, ses templates et ses documents",
        "view_templates": "Templates",
        "view_templates_tip": "Un document avec le template de fond et le template de forme choisis, sans rien du projet que ses données de base",
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
        "view_form": "Formular",
        "view_form_tip": "Der Bereich in Zeilen, eine je Zeile seiner Datei: Symbole, Berechnungen und Ergebnisse",
        "view_code": "Code",
        "view_code_tip": "Die .typ-Datei des Bereichs selbst, eingefärbt, und die Argumente der Zeile des Cursors",
        "view_entry": "Erfassung",
        "view_entry_tip": "Was von Hand erfasst wird",
        "view_display": "Darstellung",
        "view_display_tip": "Wie der Bericht es druckt: die kompilierte Vorschau, die Optionen des Befehls und der Befehl zum Kopieren",
        "view_details": "Angaben",
        "view_details_tip": "Die Grunddaten des Projekts, seine Vorlagen und seine Dokumente",
        "view_templates": "Vorlagen",
        "view_templates_tip": "Ein Dokument mit der gewählten Inhalts- und Formvorlage, ohne etwas vom Projekt ausser seinen Grunddaten",
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
        "view_form": "Form",
        "view_form_tip": "The domain in rows, one a line of its file: symbols, calculations and results",
        "view_code": "Code",
        "view_code_tip": "The domain's .typ file itself, coloured, and the arguments of the line of the cursor",
        "view_entry": "Entry",
        "view_entry_tip": "What is typed in by hand",
        "view_display": "Display",
        "view_display_tip": "As the report prints it: the compiled preview, the command's options and the command to copy",
        "view_details": "Details",
        "view_details_tip": "The project's basic data, its templates and its documents",
        "view_templates": "Templates",
        "view_templates_tip": "A document with the content template and the layout template chosen, and nothing of the project but its basic data",
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


def default(tab):
    """The view `tab` arrives in: the first it declares, None for a tab that has none (issue #86)."""
    keys = declared(tab)
    return keys[0] if keys else None
