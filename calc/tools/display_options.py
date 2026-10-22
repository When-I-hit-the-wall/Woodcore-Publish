"""The option panels of the «Affichage» views, one per command, written by hand (v0.117; docs/ui/window.md §10quater).

The engineer's answer of 07.10.2026 to Q-001 of the spec `docs/requirements/active/2026-10-07-vues-onglets-slider-et-volets.md`: every command a tab can show in its «Affichage» view has its own panel, written for it now -- not generated from its `///` block. A panel here is a declaration: which named arguments of the command it offers, in which order, as what kind of control, under which words, and which control has an effect only once another is set. `display_view.SpecPanel` draws it; no Qt is imported here.

**What a declaration never holds is a default** (review B03): the state a control starts in is read off the command's signature in lib/ (`build_reference.signature_defaults`), and a call writes only what differs from it (`build_reference.call_command`). A default written here would be a second one, and would drift.

**Every named argument is offered or dismissed with its reason** (`DISMISSED`): `tests/test_display_view.py` reads each command's signature and names any argument neither offered here nor dismissed -- a command that gains an argument in lib/ fails the test until its panel says what to do with it.

**What a preview cannot show** (review B05) is said instead of compiled (`NOTES`): a command that prints nothing, and one that reads the whole document a snippet does not hold.

**One declaration, two views** (v0.117, issue #19, spec 2026-10-10-issues-github-19-20-21 ARCH-RISK-W01): the «Formules» tab writes a variable or an equation in «Calcul» -- its label, its description, its citation -- and sets how it is printed in «Affichage» -- its level, its display type, its style. An option says which view it belongs to (`Option.view`), and `Spec.for_view` gives the panel of one view; a command shown in one view only, every other tab's, leaves it empty.

**The level of detail -1** (issue #20): a `detail` control is the level with -1, «Sélection manuelle», where the command takes `shown:` -- read off its signature, never listed here -- and under it a box and a level 1, 2, 3 for every variable the command can print (`Entry.context["shown"]`, calc/shown_variables.py's keys): the engineer never types a name.
"""

import re
from dataclasses import dataclass, field

# The kinds of control (display_view.SpecPanel):
#   bool    a check box
#   width   an editable list of widths: a percentage of the text's width or a length; the default left out
#   level   auto, 0, 1, 2, 3 -- or the subset `choices` names
#   title   auto · none · my text (a heading)
#   caption auto · none · my text (a figure's caption)
#   choice  one of `choices`, each a string the command takes
#   number  a number, `choices` being (minimum, maximum, step)
#   text    a line of text; empty is the default
#   ids     the ids the tab hands over (`context[name]`), ticked: none ticked is the default
#   columns the columns of a table (`choices`, by name), each ticked or not and given a width -- mm or % --: it writes the argument itself (the ticked ones, left out where all are) and, in `also`, the one that holds the widths
#   switch  a part of a figure the level decides -- auto (by the level, the default, not written) · yes · no -- for an argument whose default is `auto` (spec 2026-10-20-indices-et-niveaux, UI-003, ARCH-RISK-609)
#   detail  the level of a command that takes `shown:` (issue #20): auto, 1, 2, 3 -- or the subset `choices` names -- and -1, under which a box and a level for every variable the tab hands over (`context["shown"]`); it writes `level` and, at -1, `also`'s `shown`
KINDS = ("bool", "width", "level", "title", "caption", "choice", "number", "text", "ids", "columns", "detail", "switch")


@dataclass(frozen=True)
class Option:
    name: str            # the argument, as Typst names it (`scale-bar`)
    kind: str            # one of KINDS
    label: str           # the key of its words in STRINGS
    choices: tuple = ()  # a choice's values, a level's subset, a number's (minimum, maximum, step)
    needs: str = ""      # what this one has an effect only with: another option on (a bool) or not empty (ids) -- `name`; another option at one value -- `name=value`; or something the object chosen carries -- `@flag`, from the tab's context
    needs_tip: str = ""  # the key of the words that say why it is greyed
    also: tuple = ()     # the other named arguments the control writes with its own (a `columns` control: the widths; a `detail` control: `shown`) -- offered by it, not to be dismissed (tests/test_display_view.py)
    view: str = ""       # the view it is offered in, where a command is shown in two (the «Formules» tab): "calc", "display", or "" for both


@dataclass(frozen=True)
class Spec:
    command: str                 # the command, as lib/ names it
    options: tuple               # its Options, in the order the panel shows them
    cards: tuple = ()            # ((the key of a card's title, (option names...)), ...): the panel's cards; one card of every option where empty
    positional: tuple = field(default_factory=tuple)   # the names of the positional arguments the tab hands over (`context`)

    def for_view(self, view):
        """The panel of one view: the options offered in `view` and in both, the cards keeping their order and losing what is not offered -- a card left empty goes."""
        options = tuple(option for option in self.options if option.view in ("", view))
        names = {option.name for option in options}
        kept = tuple((title, tuple(name for name in group if name in names)) for title, group in self.cards)
        return Spec(self.command, options, tuple(card for card in kept if card[1]), self.positional)


WIDTHS = ("100%", "80%", "60%", "50%", "40%")

# The columns of the list of the positions, in the order lib/positions.typ prints them (`position-list-columns-all`, held equal by tests/test_position_list.py), and what a width typed for one may be: a number of mm, `30mm`, or a percentage, `20%`.
POSITION_LIST_COLUMNS = ("id", "type", "material", "strength_class", "section_type", "dimension", "units", "moisture_class", "description")
COLUMN_WIDTH = re.compile(r"^\s*(\d+(?:[.,]\d+)?)\s*(mm|%)?\s*$")


def column_width(text):
    """A width typed beside a column as Typst source -- `30mm`, `20%` -- or None where it is not one (an empty text is none). A bare number is millimetres."""
    match = COLUMN_WIDTH.match(text or "")
    if match is None:
        return None
    number = match.group(1).replace(",", ".")
    return number + (match.group(2) or "mm")

LEVELS = ("auto", "0", "1", "2", "3")
# The levels of a command that refuses 0 -- the show-* commands print something or are not called (docs/typst/report-engine.md §4): offering it made the preview fail
LEVELS_SHOWN = ("auto", "1", "2", "3")
# The level that lists the variables printed (calc/shown_variables.SELECTION_LEVEL), offered where the command takes `shown:`
SELECTION = "-1"

TITLE = lambda key="ds_opt_title": Option("title", "title", key)   # noqa: E731 -- one line per command that has a title
LEVEL = Option("level", "level", "ds_opt_level")
LEVEL_SHOWN = Option("level", "level", "ds_opt_level", choices=LEVELS_SHOWN)
DETAIL = Option("level", "detail", "ds_opt_level", also=("shown",))
WIDTH = Option("width", "width", "ds_opt_width")
CAPTION = Option("caption", "caption", "ds_opt_caption")

# The options of the commands the «Formules» tab writes (issue #19): what the line is -- its label, its description, its citation -- is written in «Calcul», how it is printed -- its level, its display type, its style, the summary table -- in «Affichage»
PRINT_LEVEL = Option("level", "level", "ds_opt_level", view="display")
LABEL = Option("label", "text", "ds_opt_label", view="calc")
DESCR = Option("descr", "text", "ds_opt_descr", view="calc")
STYLE = Option("style", "choice", "ds_opt_style", choices=("", "bold", "underline", "double"), view="display")
NORM = Option("norm", "text", "ds_opt_norm", view="calc")
NORM_REF = Option("norm-ref", "text", "ds_opt_norm_ref", view="calc")

SPECS = {
    # the drawings a native figure holds (spec 2026-10-21-commandes-typst-refonte, REQ-013, UI-002): what the figure shows, words of `detail-figure` -- none ticked, the command's own --, its width, the parts lit; no caption, the figure's being the engineer's
    "image-static-model": Spec("image-static-model", (
        WIDTH,
        Option("detail-figure", "ids", "ds_opt_detail_figure"),
        Option("highlight", "ids", "ds_opt_highlight_model"),
    ), cards=(("ds_card_figure", ("width",)), ("ds_card_shown", ("detail-figure",)), ("ds_card_highlight", ("highlight",))),
        positional=("model",)),
    "image-schema": Spec("image-schema", (
        WIDTH,
        Option("detail-figure", "ids", "ds_opt_detail_figure"),
        Option("highlight", "ids", "ds_opt_highlight_schema"),
    ), cards=(("ds_card_figure", ("width",)), ("ds_card_shown", ("detail-figure",)), ("ds_card_highlight", ("highlight",))),
        positional=("schema",)),
    "journal-entries": Spec("journal-entries", (
        Option("document", "choice", "ds_opt_document", choices=("rs", "cu", "bp")),
    )),
    "var": Spec("var", (
        PRINT_LEVEL, LABEL, DESCR, STYLE, NORM, NORM_REF,
    ), cards=(("ds_card_print", ("level", "style")), ("ds_card_texts", ("label", "descr")), ("ds_card_citation", ("norm", "norm-ref"))),
        positional=("key",)),
    "find": Spec("find", (
        Option("type", "choice", "ds_opt_type_find", choices=("val+unit", "name", "val", "unit", "expression")),
    )),
    # The «Formule» tab's commands (v0.117, calc/tools/formula_tab.py): what a block being written offers on the right, its middle filling the rest
    "eq": Spec("eq", (
        PRINT_LEVEL, LABEL, DESCR, STYLE, NORM, NORM_REF,
    ), cards=(("ds_card_print", ("level", "style")), ("ds_card_texts", ("label", "descr")), ("ds_card_citation", ("norm", "norm-ref"))),
        positional=("key",)),
    "verify": Spec("verify", (PRINT_LEVEL,), positional=("relation",)),
}

# The commands whose panel is a widget of their own rather than a declaration (display_view.Entry.panel), and why: what they offer depends on what a declaration cannot know.
OWN_PANELS = {
    "image-positions-plan": "plan_command_builder.CommandOptions: the positions it offers are those the plan's export record carries, the scale bar greyed where it has no scale (v0.114) -- each switch a word of `detail-figure` or `detail-legend` (command_text, spec 2026-10-21-commandes-typst-refonte, ARCH-012)",
    "image-fire-plan": "plan_command_builder.FireCommandOptions: the position plan's, less what a fire plan has none of (v0.115) -- its legend and scale bar words of `detail-legend` (fire_command_text)",
}

# The named arguments a panel does not offer, and why -- every one of a command's signature is either here or in its Spec (tests/test_display_view.py).
# The fine display arguments (spec 2026-10-21-commandes-typst-refonte, REQ-001), the same reason for each.
FINE = "the fine display arguments of the spec 2026-10-21-commandes-typst-refonte (REQ-001): written in the line's file, the copy panel offering the level that presets them until lot 19 (UI-002) gives it their controls"

DISMISSED = {
    "var": {
        "name-calc": FINE,
        "name-visible": FINE,
        "value": FINE,
        "unit": FINE,
        "display": FINE,
        "role": FINE,
        "label-position": FINE,
        "descr-position": FINE,
        "norm-section": FINE,
        "norm-position": FINE,
        "id": FINE,
        "domain": "the place the value is read is the variable's own, chosen in the list on the left",
    },
    "find": {
        "object": "always «variable» here: the tab's list is the listing of the domains",
        "domain": "the domain chosen in the list on the left",
    },
    "eq": {
        "name-calc": FINE,
        "name-visible": FINE,
        "equation": FINE,
        "as-unit": FINE,
        "display-formula": FINE,
        "display-equation": FINE,
        "role": FINE,
        "label-position": FINE,
        "descr-position": FINE,
        "norm-section": FINE,
        "norm-position": FINE,
        "id": FINE,
        "unit": "the output unit, chosen in the «Formules» tab's own list among the units of the result's dimension (lib/units.json's `offered`)",
        "value": "an answer stated for a formula that is displayed and not evaluated: the «Formules» tab computes every formula it writes, and such a line is written by hand in VS Code",
    },
    "verify": {
        "name-calc": FINE,
        "name-visible": FINE,
        "display": FINE,
        "role": FINE,
        "label": FINE,
        "label-position": FINE,
        "descr": FINE,
        "descr-position": FINE,
        "norm": FINE,
        "norm-section": FINE,
        "norm-position": FINE,
        "id": "the relation's name, written by Woodcore when it unfolds a check and kept as the file has it, never an option of the display",
    },
}

# What the preview says instead of compiling (review B05): the key of the words, by command.
NOTES = {
    "journal-entries": "ds_note_prints_nothing",
}

STRINGS = {
    "fr": {
        "ds_command": "Commande",
        "ds_command_tip": "La commande que l'aperçu imprime et que «Copier» copie",
        "ds_call": "Commande à copier",
        "ds_copy": "Copier",
        "ds_copied": "Copié ✓",
        "ds_import_line": "Ligne d'import, une fois en tête du fichier .typ",
        "ds_options": "Options",
        "ds_no_options": "Cette commande n'a pas d'autre option que ce qui est choisi à gauche.",
        "ds_nothing": "Rien de choisi à gauche.",
        "ds_save_first": "Pas encore enregistré : la commande nomme ce que l'export contient. Enregistrer, puis « Import données ».",
        "ds_loop": "{command} — tous (boucle)",
        "ds_no_project": "Aucun projet ouvert.",
        "ds_not_exported": "« {id} » n'est pas encore dans l'export : l'aperçu ne peut pas le montrer. Cliquer « Import données ».",
        "ds_stale": "« {id} » a changé depuis le dernier export : l'aperçu montre l'état exporté. Cliquer « Import données ».",
        "ds_note_prints_nothing": "Cette commande n'imprime rien : elle lit des valeurs dans une variable, pour une section qui les met en forme elle-même. Pas d'aperçu.",
        "ds_note_whole_document": "Cette commande lit tout le document — ce que chaque section a déclaré — qu'un aperçu isolé ne contient pas. L'aperçu se voit dans le PDF.",
        "ds_note_document_variable": "Cette variable est déclarée dans un document : un aperçu isolé ne la connaît pas. L'aperçu se voit dans le PDF.",
        "ds_note_loop": "Une boucle sur tous les objets : elle s'aperçoit dans le PDF.",
        "ds_card_figure": "Figure",
        "ds_card_shown": "Ce qui est montré",
        "ds_card_highlight": "Mis en évidence",
        "ds_card_forces": "Efforts (kN, kNm)",
        "ds_card_print": "Impression",
        "ds_card_value": "Valeur",
        "ds_card_texts": "Textes",
        "ds_card_citation": "Citation",
        "ds_opt_width": "Largeur",
        "ds_opt_width_tip": "Un pourcentage de la largeur du texte (60%) ou une longueur (12cm).",
        "ds_opt_caption": "Légende de la figure",
        "ds_auto": "Automatique",
        "ds_none": "Aucune",
        "ds_custom": "Mon texte",
        "ds_custom_text": "Texte",
        "ds_opt_title": "Titre",
        "ds_opt_level": "Niveau de détail",
        "ds_level_auto": "Celui du rapport",
        "ds_switch_auto": "Selon le niveau",
        "ds_switch_true": "Oui",
        "ds_switch_false": "Non",
        "ds_opt_loads": "Charges",
        "ds_opt_dimensions": "Cotes",
        "ds_opt_highlight_model": "Parties mises en évidence",
        "ds_opt_highlight_schema": "Parties mises en évidence",
        "ds_opt_detail_figure": "Ce que la figure montre (rien de coché : ce que la commande montre d'elle-même)",
        "ds_opt_aids": "Aides de construction cochées « visibles »",
        "ds_opt_description": "Avec la description",
        "ds_opt_N": "N",
        "ds_opt_V": "V",
        "ds_opt_M": "M",
        "ds_opt_form": "Forme",
        "ds_choice_table": "Tableau",
        "ds_choice_list": "Liste",
        "ds_choice_grid": "Cartes",
        "ds_choice_kN/m²": "kN/m² (charges surfaciques)",
        "ds_choice_kN/m": "kN/m (charges linéiques)",
        "ds_opt_document": "Journal du document",
        "ds_choice_rs": "Rapport de statique",
        "ds_choice_cu": "Convention d'utilisation",
        "ds_choice_bp": "Base de projet",
        "ds_opt_scope": "Positions listées",
        "ds_choice_all": "Toutes",
        "ds_choice_plans": "Celles des plans cochés",
        "ds_choice_storey": "Celles d'un étage",
        "ds_opt_plans": "Plans",
        "ds_opt_storey": "Étage (2e lettre de l'ID)",
        "ds_opt_columns": "Colonnes imprimées",
        "ds_opt_columns_tip": "Cochez les colonnes à imprimer. Une largeur en mm (30 ou 30mm) ou en % de la largeur du texte (20%) : vide, la colonne prend ce que demande son contenu. La dernière colonne cochée reste cochée.",
        "ds_opt_legend": "Légende",
        "ds_col_id": "ID",
        "ds_col_type": "Type",
        "ds_col_material": "Matériau",
        "ds_col_strength_class": "Classe de résistance",
        "ds_col_section_type": "Type de section",
        "ds_col_dimension": "Dimension",
        "ds_col_units": "Unités",
        "ds_col_moisture_class": "Classe d'humidité",
        "ds_col_description": "Description",
        "ds_width_placeholder": "largeur",
        "ds_width_bad": "Une largeur : 30, 30mm ou 20%.",
        "ds_card_list": "Liste",
        "ds_card_table": "Tableau",
        "ds_card_columns": "Colonnes",
        "ds_needs_scope_plans": "Pour « Celles des plans cochés ».",
        "ds_needs_scope_storey": "Pour « Celles d'un étage ».",
        "ds_opt_type": "Ce qui est imprimé",
        "ds_opt_type_find": "Colonne des valeurs",
        "ds_choice_val+unit": "Valeur et unité",
        "ds_choice_val": "Valeur",
        "ds_choice_unit": "Unité",
        "ds_choice_expression": "Symbole = valeur unité",
        "ds_choice_name": "Noms seulement",
        "ds_opt_unit": "Unité d'impression",
        "ds_opt_label": "Libellé",
        "ds_opt_descr": "Description",
        "ds_opt_style": "Style",
        "ds_choice_": "Normal",
        "ds_choice_bold": "Gras",
        "ds_choice_underline": "Souligné",
        "ds_choice_double": "Double trait",
        "ds_opt_norm": "Norme",
        "ds_opt_norm_ref": "Article",
        "ds_choice_none": "Aucune",
        "ds_level_manual": "Sélection manuelle",
        "ds_shown": "Variables imprimées",
        "ds_shown_tip": "Choisissez le niveau de détail de chaque variable : 0 ne l'imprime pas, 1 à 3 l'imprime. Le titre s'imprime toujours ; le verdict d'une vérification est une ligne comme les autres.",
        "ds_shown_none": "Aucune variable à choisir pour cet objet.",
        "ds_shown_positions": "Positions des moyens d'assemblage",
        "ds_shown_centre": "Centre de rotation",
        "ds_shown_theta": "Angles entre les éléments",
        "ds_shown_forces": "Efforts intérieurs N, V, M",
        "ds_shown_components": "Composantes de N et V",
        "ds_shown_beta": "Angles force-fil",
        "ds_shown_forces_table": "Tableau des efforts",
        "ds_shown_worst_table": "Tableau de la superposition défavorable",
    },
    "de": {
        "ds_command": "Befehl",
        "ds_command_tip": "Der Befehl, den die Vorschau druckt und «Kopieren» kopiert",
        "ds_call": "Befehl zum Kopieren",
        "ds_copy": "Kopieren",
        "ds_copied": "Kopiert ✓",
        "ds_import_line": "Importzeile, einmal am Anfang der .typ-Datei",
        "ds_options": "Optionen",
        "ds_no_options": "Dieser Befehl hat keine andere Option als das links Gewählte.",
        "ds_nothing": "Links ist nichts gewählt.",
        "ds_save_first": "Noch nicht gespeichert: der Befehl nennt, was der Export enthält. Speichern, dann «Daten importieren».",
        "ds_loop": "{command} — alle (Schleife)",
        "ds_no_project": "Kein Projekt geöffnet.",
        "ds_not_exported": "«{id}» ist noch nicht im Export: die Vorschau kann es nicht zeigen. «Daten importieren» klicken.",
        "ds_stale": "«{id}» hat sich seit dem letzten Export geändert: die Vorschau zeigt den exportierten Stand. «Daten importieren» klicken.",
        "ds_note_prints_nothing": "Dieser Befehl druckt nichts: er liest Werte in eine Variable, für einen Abschnitt, der sie selbst gestaltet. Keine Vorschau.",
        "ds_note_whole_document": "Dieser Befehl liest das ganze Dokument — was jeder Abschnitt deklariert hat —, das eine einzelne Vorschau nicht enthält. Die Vorschau sieht man im PDF.",
        "ds_note_document_variable": "Diese Variable ist in einem Dokument deklariert: eine einzelne Vorschau kennt sie nicht. Die Vorschau sieht man im PDF.",
        "ds_note_loop": "Eine Schleife über alle Objekte: man sieht sie im PDF.",
        "ds_card_figure": "Abbildung",
        "ds_card_shown": "Was gezeigt wird",
        "ds_card_highlight": "Hervorgehoben",
        "ds_card_forces": "Schnittkräfte (kN, kNm)",
        "ds_card_print": "Druck",
        "ds_card_value": "Wert",
        "ds_card_texts": "Texte",
        "ds_card_citation": "Zitat",
        "ds_opt_width": "Breite",
        "ds_opt_width_tip": "Ein Prozentsatz der Textbreite (60%) oder eine Länge (12cm).",
        "ds_opt_caption": "Bildunterschrift",
        "ds_auto": "Automatisch",
        "ds_none": "Keine",
        "ds_custom": "Mein Text",
        "ds_custom_text": "Text",
        "ds_opt_title": "Titel",
        "ds_opt_level": "Detailstufe",
        "ds_level_auto": "Die des Berichts",
        "ds_switch_auto": "Nach Stufe",
        "ds_switch_true": "Ja",
        "ds_switch_false": "Nein",
        "ds_opt_loads": "Lasten",
        "ds_opt_dimensions": "Bemassung",
        "ds_opt_highlight_model": "Hervorgehobene Teile",
        "ds_opt_highlight_schema": "Hervorgehobene Teile",
        "ds_opt_detail_figure": "Was die Abbildung zeigt (nichts angekreuzt: was der Befehl von sich aus zeigt)",
        "ds_opt_aids": "Als «sichtbar» markierte Hilfslinien",
        "ds_opt_description": "Mit Beschreibung",
        "ds_opt_N": "N",
        "ds_opt_V": "V",
        "ds_opt_M": "M",
        "ds_opt_form": "Form",
        "ds_choice_table": "Tabelle",
        "ds_choice_list": "Liste",
        "ds_choice_grid": "Karten",
        "ds_choice_kN/m²": "kN/m² (Flächenlasten)",
        "ds_choice_kN/m": "kN/m (Linienlasten)",
        "ds_opt_document": "Journal des Dokuments",
        "ds_choice_rs": "Statischer Bericht",
        "ds_choice_cu": "Nutzungsvereinbarung",
        "ds_choice_bp": "Projektbasis",
        "ds_opt_scope": "Aufgeführte Positionen",
        "ds_choice_all": "Alle",
        "ds_choice_plans": "Jene der gewählten Pläne",
        "ds_choice_storey": "Jene eines Geschosses",
        "ds_opt_plans": "Pläne",
        "ds_opt_storey": "Geschoss (2. Buchstabe der ID)",
        "ds_opt_columns": "Gedruckte Spalten",
        "ds_opt_columns_tip": "Haken Sie die zu druckenden Spalten an. Eine Breite in mm (30 oder 30mm) oder in % der Textbreite (20%): leer nimmt die Spalte, was ihr Inhalt braucht. Die letzte angehakte Spalte bleibt angehakt.",
        "ds_opt_legend": "Legende",
        "ds_col_id": "ID",
        "ds_col_type": "Typ",
        "ds_col_material": "Material",
        "ds_col_strength_class": "Festigkeitsklasse",
        "ds_col_section_type": "Querschnittstyp",
        "ds_col_dimension": "Abmessung",
        "ds_col_units": "Einheit",
        "ds_col_moisture_class": "Feuchteklasse",
        "ds_col_description": "Beschreibung",
        "ds_width_placeholder": "Breite",
        "ds_width_bad": "Eine Breite: 30, 30mm oder 20%.",
        "ds_card_list": "Liste",
        "ds_card_table": "Tabelle",
        "ds_card_columns": "Spalten",
        "ds_needs_scope_plans": "Für «Jene der gewählten Pläne».",
        "ds_needs_scope_storey": "Für «Jene eines Geschosses».",
        "ds_opt_type": "Was gedruckt wird",
        "ds_opt_type_find": "Wertespalte",
        "ds_choice_val+unit": "Wert und Einheit",
        "ds_choice_val": "Wert",
        "ds_choice_unit": "Einheit",
        "ds_choice_expression": "Symbol = Wert Einheit",
        "ds_choice_name": "Nur Namen",
        "ds_opt_unit": "Druckeinheit",
        "ds_opt_label": "Bezeichnung",
        "ds_opt_descr": "Beschreibung",
        "ds_opt_style": "Stil",
        "ds_choice_": "Normal",
        "ds_choice_bold": "Fett",
        "ds_choice_underline": "Unterstrichen",
        "ds_choice_double": "Doppelt unterstrichen",
        "ds_opt_norm": "Norm",
        "ds_opt_norm_ref": "Ziffer",
        "ds_choice_none": "Keine",
        "ds_level_manual": "Manuelle Auswahl",
        "ds_shown": "Ausgegebene Variablen",
        "ds_shown_tip": "Wählen Sie die Detailstufe jeder Variable: 0 gibt sie nicht aus, 1 bis 3 gibt sie aus. Der Titel wird immer ausgegeben; das Nachweisergebnis ist eine Zeile wie die anderen.",
        "ds_shown_none": "Für dieses Objekt gibt es keine Variable zu wählen.",
        "ds_shown_positions": "Lage der Verbindungsmittel",
        "ds_shown_centre": "Drehpunkt",
        "ds_shown_theta": "Winkel zwischen den Elementen",
        "ds_shown_forces": "Schnittkräfte N, V, M",
        "ds_shown_components": "Komponenten von N und V",
        "ds_shown_beta": "Kraft-Faser-Winkel",
        "ds_shown_forces_table": "Tabelle der Kräfte",
        "ds_shown_worst_table": "Tabelle der ungünstigsten Überlagerung",
    },
    "en": {
        "ds_command": "Command",
        "ds_command_tip": "The command the preview prints and «Copy» copies",
        "ds_call": "Command to copy",
        "ds_copy": "Copy",
        "ds_copied": "Copied ✓",
        "ds_import_line": "Import line, once at the top of the .typ file",
        "ds_options": "Options",
        "ds_no_options": "This command has no other option than what is chosen on the left.",
        "ds_nothing": "Nothing chosen on the left.",
        "ds_save_first": "Not saved yet: the command names what the export holds. Save, then «Import data».",
        "ds_loop": "{command} — every one (loop)",
        "ds_no_project": "No project open.",
        "ds_not_exported": "«{id}» is not in the export yet: the preview cannot show it. Click «Import data».",
        "ds_stale": "«{id}» has changed since the last export: the preview shows what was exported. Click «Import data».",
        "ds_note_prints_nothing": "This command prints nothing: it reads values into a variable, for a section that sets them its own way. No preview.",
        "ds_note_whole_document": "This command reads the whole document — what every section declared — which a preview on its own does not hold. The preview is the PDF.",
        "ds_note_document_variable": "This variable is declared in a document: a preview on its own does not know it. The preview is the PDF.",
        "ds_note_loop": "A loop over every object: it is seen in the PDF.",
        "ds_card_figure": "Figure",
        "ds_card_shown": "What is shown",
        "ds_card_highlight": "Highlighted",
        "ds_card_forces": "Forces (kN, kNm)",
        "ds_card_print": "Printing",
        "ds_card_value": "Value",
        "ds_card_texts": "Texts",
        "ds_card_citation": "Citation",
        "ds_opt_width": "Width",
        "ds_opt_width_tip": "A percentage of the text's width (60%) or a length (12cm).",
        "ds_opt_caption": "Figure caption",
        "ds_auto": "Automatic",
        "ds_none": "None",
        "ds_custom": "My text",
        "ds_custom_text": "Text",
        "ds_opt_title": "Title",
        "ds_opt_level": "Level of detail",
        "ds_level_auto": "The report's",
        "ds_switch_auto": "By the level",
        "ds_switch_true": "Yes",
        "ds_switch_false": "No",
        "ds_opt_loads": "Loads",
        "ds_opt_dimensions": "Dimensions",
        "ds_opt_highlight_model": "Parts highlighted",
        "ds_opt_highlight_schema": "Parts highlighted",
        "ds_opt_detail_figure": "What the figure shows (none ticked: what the command shows of its own)",
        "ds_opt_aids": "Construction aids ticked «visible»",
        "ds_opt_description": "With the description",
        "ds_opt_N": "N",
        "ds_opt_V": "V",
        "ds_opt_M": "M",
        "ds_opt_form": "Form",
        "ds_choice_table": "Table",
        "ds_choice_list": "List",
        "ds_choice_grid": "Cards",
        "ds_choice_kN/m²": "kN/m² (area loads)",
        "ds_choice_kN/m": "kN/m (line loads)",
        "ds_opt_document": "Journal of the document",
        "ds_choice_rs": "Statical report",
        "ds_choice_cu": "Use agreement",
        "ds_choice_bp": "Basis of design",
        "ds_opt_scope": "Positions listed",
        "ds_choice_all": "All",
        "ds_choice_plans": "Those of the plans ticked",
        "ds_choice_storey": "Those of one storey",
        "ds_opt_plans": "Plans",
        "ds_opt_storey": "Storey (2nd letter of the ID)",
        "ds_opt_columns": "Columns printed",
        "ds_opt_columns_tip": "Tick the columns to print. A width in mm (30 or 30mm) or in % of the text width (20%): empty, the column takes what its content needs. The last ticked column stays ticked.",
        "ds_opt_legend": "Legend",
        "ds_col_id": "ID",
        "ds_col_type": "Type",
        "ds_col_material": "Material",
        "ds_col_strength_class": "Strength class",
        "ds_col_section_type": "Section type",
        "ds_col_dimension": "Dimension",
        "ds_col_units": "Units",
        "ds_col_moisture_class": "Moisture class",
        "ds_col_description": "Description",
        "ds_width_placeholder": "width",
        "ds_width_bad": "A width: 30, 30mm or 20%.",
        "ds_card_list": "List",
        "ds_card_table": "Table",
        "ds_card_columns": "Columns",
        "ds_needs_scope_plans": "For «Those of the plans ticked».",
        "ds_needs_scope_storey": "For «Those of one storey».",
        "ds_opt_type": "What is printed",
        "ds_opt_type_find": "Value column",
        "ds_choice_val+unit": "Value and unit",
        "ds_choice_val": "Value",
        "ds_choice_unit": "Unit",
        "ds_choice_expression": "Symbol = value unit",
        "ds_choice_name": "Names only",
        "ds_opt_unit": "Unit printed in",
        "ds_opt_label": "Label",
        "ds_opt_descr": "Description",
        "ds_opt_style": "Style",
        "ds_choice_": "Plain",
        "ds_choice_bold": "Bold",
        "ds_choice_underline": "Underlined",
        "ds_choice_double": "Double rule",
        "ds_opt_norm": "Norm",
        "ds_opt_norm_ref": "Clause",
        "ds_choice_none": "None",
        "ds_level_manual": "Manual selection",
        "ds_shown": "Variables printed",
        "ds_shown_tip": "Choose the level of detail of each variable: 0 leaves it out, 1 to 3 prints it. The title is always printed; a check's verdict is a line like the others.",
        "ds_shown_none": "No variable to choose for this object.",
        "ds_shown_positions": "Positions of the fasteners",
        "ds_shown_centre": "Rotation centre",
        "ds_shown_theta": "Angles between the members",
        "ds_shown_forces": "Internal forces N, V, M",
        "ds_shown_components": "Components of N and V",
        "ds_shown_beta": "Force-grain angles",
        "ds_shown_forces_table": "Table of the forces",
        "ds_shown_worst_table": "Table of the most unfavourable superposition",
    },
}


def spec(command):
    """The panel of `command`, or an empty one: a command offered with no option of its own (a loop, a binding)."""
    return SPECS.get(command) or Spec(command, ())


def card_layout(spec_):
    """The panel's cards: [(title key or None, [Option, ...])], every option in exactly one."""
    by_name = {option.name: option for option in spec_.options}
    if not spec_.cards:
        return [(None, list(spec_.options))] if spec_.options else []
    cards = [(title, [by_name[name] for name in names]) for title, names in spec_.cards]
    placed = {name for _title, names in spec_.cards for name in names}
    rest = [option for option in spec_.options if option.name not in placed]
    if rest:
        cards.append((None, rest))
    return cards


def initial(option, default):
    """The state a control starts in, from the argument's default as the signature writes it (Typst source): the one source of it (review B03)."""
    text = (default or "").strip()
    unquoted = text[1:-1] if len(text) >= 2 and text[0] == text[-1] == '"' else text
    kind = option.kind
    if kind == "bool":
        return text == "true"
    if kind == "switch":
        return text if text in ("true", "false") else "auto"
    if kind == "number":
        try:
            return float(text)
        except ValueError:
            return 0.0
    if kind in ("level",):
        return unquoted if unquoted in (option.choices or LEVELS) else (option.choices or LEVELS)[0]
    if kind == "detail":
        # (the level, {key: its level}): nothing chosen until the engineer ticks
        return (unquoted if unquoted in (option.choices or LEVELS_SHOWN) else "auto", {})
    if kind in ("title", "caption"):
        return ("none", "") if text == "none" else ("auto", "") if text in ("auto", "") else ("custom", unquoted)
    if kind == "choice":
        return unquoted if unquoted in option.choices else ("" if text == "none" and "" in option.choices else option.choices[0])
    if kind == "width":
        return text or WIDTHS[0]
    if kind == "ids":
        return []
    if kind == "columns":
        # `auto` -- the command's own default -- is every column; a default that names columns is those
        named = [name for name in re.findall(r'"([a-z_]+)"', text) if name in option.choices]
        return (named or list(option.choices), {})
    return "" if text in ("none", '""') else unquoted
