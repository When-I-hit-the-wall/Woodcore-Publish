"""Woodcore's «Variables» tab (docs/project/purpose.md §1, docs/ui/window.md §10quater, docs/typst/formulas.md §10quinquies): every value of the project, by domain, with where it comes from and the calls that print it.

The engineer: «un nouvel onglet dans Woodcore "Variables" qui liste toutes les valeurs calculés dans typst
[…] Les variables serait listées par domaine. Possibilité de filtrer par unité, par nom, etc… Possibilité de
copier des commandes var, val ou autre pour ces variables» (v0.100) -- and, in issue 13 (v0.117): «trois
colonnes : domaines | variables | détail», «filtrer toutes les variables et pas seulement celles du domaine
sélectionné», «présenter toutes les variables, avec leur provenance affichée» from the three sources, Excel,
Woodcore and Typst, and the loads tab removed once none of its variables was missing here
(spec 2026-10-08-onglet-variables-trois-colonnes).

**It holds no arithmetic of its own.** The documents' values were computed by Typst and are read back by
`calc/variables.py`, which asks a compiled document what its `var-registry` holds; the export's values are read
from the files the export wrote by `calc/variable_sources.py`, which also says where each one comes from. The
window shows and never decides: a number here is the number the page prints, because it *is* that number.

**Shared by the three documents** (the engineer's decision of 30.09.2026): one registry per document, each read
from its own compile (`variables.best(here, mode=…)`), listed with the export's values -- the documents' first, the
one the window shows leading, the export's last.

⚠️ **What a document's registry holds exists nowhere but in a compile.** `#var`, `#eq`, `#var-unit`, what
`show-polar-moment` publishes and what every `verify-*` publishes live in a Typst state and reach no `data/`
file, which is §1's standing condition on everything computed in Typst. So a read is a full compile (8-10 s
on the example project) where a document's own PDF does not carry it already.

⚠️ **That measurement is why it does not read on every `on_shown`.** The engineer asked for «mieux encore,
automatiquement importer depuis typst à l'ouverture de l'onglet», and automatic on *every* opening would be
ten seconds of a hung tab per switch. So the documents are read **once**, the first time the tab is opened, in
a thread with the tab usable meanwhile, and then from the cache until a document, the engine or the export has
moved under it (`variables.stamp`); a banner says when it has, and *Relire* is the one thing that reads again.
The export's four files, some tens of kilobytes, are read again at every showing.

⚠️ **The name and the symbol are two columns**, and that is the whole reason this tab is worth more than a
listing: `q_k11` is what one types into a call and q_(k,11) is what the page prints (§10bis, v0.85).

The tab lives in its own module, which woodcore_gui.py lists in its TABS and whose STRINGS it merges into its
own: the keys carry a `vr_` prefix of their own, for the reason the commands tab's carry `ref_` -- a key
defined in two tab modules would be silently taken by whichever merged last.
"""

from PySide6.QtCore import Qt, QThread, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QPushButton, QSplitter, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)

import build_reference as ref  # the one place a Typst call is spelled out (docs/typst/reference-workbook.md §10ter)
import cards                  # the panels in cards, after the website (cards.py, v0.93)
import display_options        # the words a preview says instead of a page (NOTES)
import display_view  # the «Affichage» view: the command, its options, the call and the page (display_view.py, v0.117)
import views  # the views the top bar's switch chooses between (views.py, v0.117)
import documents              # what each of the three documents is called (calc/documents.py)
import project
import shown_variables
import richtext               # a symbol as mathematics, a call coloured as the site's code (richtext.py, v0.92)
import theme
import variable_sources as sources   # the export's variables and where each comes from (calc/variable_sources.py, v0.117)
import variables as model     # the one module that reads a document's registry (calc/variables.py)

EXPORT = sources.EXPORT

# The variable list's columns. `Name` first because it is what one types into a call, `Symbol` beside it because
# it is what the page prints and the two are not the same word; the unit is a column of its own rather than
# written after the value, so that a column of values lines its digits up as the report's own tables do (§3.3).
# Where a value comes from next, and the domain last, shown only while the filter reaches every domain (D-005).
COLUMNS = ("vr_col_name", "vr_col_symbol", "vr_col_value", "vr_col_unit", "vr_col_label", "vr_col_provenance", "vr_col_domain")
NAME, SYMBOL, VALUE, UNIT, LABEL, PROVENANCE, DOMAIN = range(len(COLUMNS))

# The domain pane's columns: the domain, how many variables it holds, where they come from.
DOMAIN_COLUMNS = ("vr_col_domain", "vr_col_count", "vr_col_provenance")

# A document's letters, the same in every language (the engineer, 30.09.2026), its whole name in the tooltip.
DOCUMENT_CODES = {"cu": "CU", "bp": "BP", "rs": "RS"}
# The origin of a calculation domain of the «Formule» tab (v0.117): listed beside the export's, computed by Woodcore from its own file, and named in a call as a document's named domain is
FORMULAS = sources.formula_domain.ORIGIN

# A result of its calculation, marked before its name as the loads tab marked it (D-007).
RESULT_MARK = "★ "

# What the unit and provenance filters offer above their values: everything.
ANY_UNIT = None
ANY_PROVENANCE = None

STRINGS = {
    "fr": {
        "tab_variables": "Variables",
        "vr_domains": "Domaines",
        "vr_list": "Variables",
        "vr_col_name": "Nom",
        "vr_col_symbol": "Symbole",
        "vr_col_value": "Valeur",
        "vr_col_unit": "Unité",
        "vr_col_label": "Désignation",
        "vr_col_provenance": "Provenance",
        "vr_col_domain": "Domaine",
        "vr_col_count": "Var.",
        "vr_search": "Filtrer par nom, symbole, désignation, valeur…",
        "vr_all_domains": "Tous les domaines",
        "vr_all_domains_hint": "Coché, le filtre porte sur toutes les variables de tous les domaines et non sur le seul domaine choisi.",
        "vr_results_only": "Résultats seulement",
        "vr_results_only_hint": "Ne garde que les résultats d'un calcul, marqués ★.",
        "vr_any_unit": "Toutes les unités",
        "vr_no_unit": "sans unité",
        "vr_any_provenance": "Toutes les provenances",
        "vr_prov_excel": "Excel",
        "vr_prov_woodcore": "Woodcore",
        "vr_prov_typst": "Typst",
        "vr_prov_unknown": "inconnue",
        "vr_reload": "Relire les documents",
        "vr_pick_import": "Importer",
        "vr_pick_cancel": "Annuler",
        "vr_pick_none": "Choisissez une variable dans la liste, puis « Importer ».",
        "vr_reload_hint": "Compile les documents et relit leurs variables — quelques secondes chacun.",
        "vr_reading": "Lecture des documents…",
        "vr_never": "Les documents n'ont pas encore été lus.",
        "vr_count": "{count} variables dans {domains} domaines",
        "vr_stale": "Un document a changé depuis sa lecture : « Relire » pour la refaire.",
        "vr_empty": "Aucune variable.\n\nCe sont les valeurs des classeurs Excel et celles que Woodcore calcule\n(charges, connecteurs, moments polaires, scripts), lues dans l'export,\net celles que les documents calculent dans Typst (#var, #eq, verify-*…).",
        "vr_no_export": "Le projet n'a pas encore été exporté : « Import données » écrit les variables des classeurs et de Woodcore.",
        "vr_filtered": "Aucune variable ne correspond au filtre.",
        "vr_choose_domain": "Choisissez un domaine à gauche, ou cochez « Tous les domaines ».",
        "vr_domain_report": "Document",
        "vr_kind_report": "les variables du document lui-même",
        "vr_kind_check": "un nachweis",
        "vr_kind_named": "un domaine nommé",
        "vr_kind_export": "un calcul de l'export",
        "vr_variable": "Variable",
        "vr_provenance": "Provenance",
        "vr_domain": "Domaine",
        "vr_key": "Nom à écrire",
        "vr_symbol": "Symbole imprimé",
        "vr_value": "Valeur",
        "vr_unit": "Unité",
        "vr_label": "Désignation",
        "vr_description": "Description",
        "vr_citation": "Référence",
        "vr_source": "Source",
        "vr_level": "Niveau de détail",
        "vr_workbook": "Classeur",
        "vr_sheet": "Feuille",
        "vr_cell": "Cellule",
        "vr_formula": "Formule",
        "vr_choices": "Choix possibles",
        "vr_open_workbook": "Ouvrir le classeur",
        "vr_open_workbook_tip": "Ouvre dans Excel le classeur d'où vient la variable ou le cas choisi ; grisé quand il n'y en a pas (une valeur de Woodcore, d'une norme ou de Typst) ou qu'il est introuvable.",
        "vr_no_selection": "Choisissez un domaine ou une variable pour voir ce qu'il porte et les commandes qui l'impriment.",
        "vr_untraced": "Ces valeurs sont calculées dans Typst et ne sont dans aucun fichier : elles ne sont pas tracées (docs/project/purpose.md §1).",
        "vr_busy": "Un export est en cours ; « Relire » sera possible ensuite.",
        "vr_failed": "« {document} » n'a pas pu être lu : {reason}",
        "vr_err_no_report": "ce document n'a pas de fichier d'entrée.",
        "vr_err_no_typst": "Typst est introuvable.",
        "vr_err_compile_failed": "le document ne compile pas.",
        "vr_err_file_busy": "un fichier du document est ouvert dans un autre programme (NextCloud le synchronise ?). Réessayez dans un instant.",
        "vr_err_timeout": "la lecture a dépassé {seconds} s.",
        "vr_err_not_json": "Typst n'a pas répondu en JSON.",
        "vr_err_not_registry": "la réponse n'est pas le registre des variables ; le moteur de ce projet est-il à jour ?",
        "vr_err_bad_file": "data/{file} ne peut pas être lu ; ses variables manquent ici. {field}",
    },
    "de": {
        "tab_variables": "Variablen",
        "vr_domains": "Domänen",
        "vr_list": "Variablen",
        "vr_col_name": "Name",
        "vr_col_symbol": "Symbol",
        "vr_col_value": "Wert",
        "vr_col_unit": "Einheit",
        "vr_col_label": "Bezeichnung",
        "vr_col_provenance": "Herkunft",
        "vr_col_domain": "Domäne",
        "vr_col_count": "Var.",
        "vr_search": "Nach Name, Symbol, Bezeichnung, Wert filtern…",
        "vr_all_domains": "Alle Domänen",
        "vr_all_domains_hint": "Angekreuzt gilt der Filter für alle Variablen aller Domänen und nicht nur für die gewählte Domäne.",
        "vr_results_only": "Nur Ergebnisse",
        "vr_results_only_hint": "Zeigt nur die Ergebnisse einer Berechnung, mit ★ markiert.",
        "vr_any_unit": "Alle Einheiten",
        "vr_no_unit": "ohne Einheit",
        "vr_any_provenance": "Alle Herkünfte",
        "vr_prov_excel": "Excel",
        "vr_prov_woodcore": "Woodcore",
        "vr_prov_typst": "Typst",
        "vr_prov_unknown": "unbekannt",
        "vr_reload": "Dokumente neu lesen",
        "vr_pick_import": "Importieren",
        "vr_pick_cancel": "Abbrechen",
        "vr_pick_none": "Wählen Sie eine Variable in der Liste, dann «Importieren».",
        "vr_reload_hint": "Kompiliert die Dokumente und liest ihre Variablen neu — je einige Sekunden.",
        "vr_reading": "Dokumente werden gelesen…",
        "vr_never": "Die Dokumente wurden noch nicht gelesen.",
        "vr_count": "{count} Variablen in {domains} Domänen",
        "vr_stale": "Ein Dokument hat sich seit seiner Lesung geändert: «Dokumente neu lesen».",
        "vr_empty": "Keine Variablen.\n\nDas sind die Werte der Excel-Arbeitsmappen und die, die Woodcore berechnet\n(Lasten, Verbindungsmittel, polare Momente, Skripte), aus dem Export gelesen,\nund die, die die Dokumente in Typst berechnen (#var, #eq, verify-*…).",
        "vr_no_export": "Das Projekt wurde noch nicht exportiert: «Daten importieren» schreibt die Variablen der Arbeitsmappen und von Woodcore.",
        "vr_filtered": "Keine Variable entspricht dem Filter.",
        "vr_choose_domain": "Wählen Sie links eine Domäne, oder kreuzen Sie «Alle Domänen» an.",
        "vr_domain_report": "Dokument",
        "vr_kind_report": "die Variablen des Dokuments selbst",
        "vr_kind_check": "ein Nachweis",
        "vr_kind_named": "eine benannte Domäne",
        "vr_kind_export": "eine Berechnung des Exports",
        "vr_variable": "Variable",
        "vr_provenance": "Herkunft",
        "vr_domain": "Domäne",
        "vr_key": "Zu schreibender Name",
        "vr_symbol": "Gedrucktes Symbol",
        "vr_value": "Wert",
        "vr_unit": "Einheit",
        "vr_label": "Bezeichnung",
        "vr_description": "Beschreibung",
        "vr_citation": "Verweis",
        "vr_source": "Quelle",
        "vr_level": "Detailstufe",
        "vr_workbook": "Arbeitsmappe",
        "vr_sheet": "Tabellenblatt",
        "vr_cell": "Zelle",
        "vr_formula": "Formel",
        "vr_choices": "Auswahl",
        "vr_open_workbook": "Arbeitsmappe öffnen",
        "vr_open_workbook_tip": "Öffnet die Arbeitsmappe der gewählten Variable oder des gewählten Falls in Excel; grau, wenn es keine gibt (ein Wert von Woodcore, aus einer Norm oder aus Typst) oder sie nicht gefunden wird.",
        "vr_no_selection": "Wählen Sie eine Domäne oder eine Variable, um zu sehen, was sie trägt, und die Befehle, die sie drucken.",
        "vr_untraced": "Diese Werte werden in Typst berechnet und stehen in keiner Datei: sie sind nicht nachverfolgt (docs/project/purpose.md §1).",
        "vr_busy": "Ein Export läuft; «Dokumente neu lesen» ist danach möglich.",
        "vr_failed": "«{document}» konnte nicht gelesen werden: {reason}",
        "vr_err_no_report": "dieses Dokument hat keine Einstiegsdatei.",
        "vr_err_no_typst": "Typst wurde nicht gefunden.",
        "vr_err_compile_failed": "das Dokument kompiliert nicht.",
        "vr_err_file_busy": "eine Datei des Dokuments ist in einem anderen Programm offen (synchronisiert NextCloud gerade?). Versuchen Sie es gleich nochmals.",
        "vr_err_timeout": "die Lesung hat {seconds} s überschritten.",
        "vr_err_not_json": "Typst hat nicht mit JSON geantwortet.",
        "vr_err_not_registry": "die Antwort ist nicht das Variablenregister; ist der Motor dieses Projekts aktuell?",
        "vr_err_bad_file": "data/{file} kann nicht gelesen werden; seine Variablen fehlen hier. {field}",
    },
    "en": {
        "tab_variables": "Variables",
        "vr_domains": "Domains",
        "vr_list": "Variables",
        "vr_col_name": "Name",
        "vr_col_symbol": "Symbol",
        "vr_col_value": "Value",
        "vr_col_unit": "Unit",
        "vr_col_label": "Label",
        "vr_col_provenance": "Provenance",
        "vr_col_domain": "Domain",
        "vr_col_count": "Var.",
        "vr_search": "Filter by name, symbol, label, value…",
        "vr_all_domains": "Every domain",
        "vr_all_domains_hint": "Ticked, the filter reaches every variable of every domain rather than the chosen domain's alone.",
        "vr_results_only": "Results only",
        "vr_results_only_hint": "Keeps only the results of a calculation, marked ★.",
        "vr_any_unit": "Every unit",
        "vr_no_unit": "no unit",
        "vr_any_provenance": "Every provenance",
        "vr_prov_excel": "Excel",
        "vr_prov_woodcore": "Woodcore",
        "vr_prov_typst": "Typst",
        "vr_prov_unknown": "unknown",
        "vr_reload": "Read the documents again",
        "vr_pick_import": "Import",
        "vr_pick_cancel": "Cancel",
        "vr_pick_none": "Choose a variable in the list, then «Import».",
        "vr_reload_hint": "Compiles the documents and reads their variables again — some seconds each.",
        "vr_reading": "Reading the documents…",
        "vr_never": "The documents have not been read yet.",
        "vr_count": "{count} variables in {domains} domains",
        "vr_stale": "A document has changed since it was read: «Read the documents again».",
        "vr_empty": "No variables.\n\nThose are the values of the Excel workbooks and the ones Woodcore computes\n(loads, connectors, polar moments, scripts), read from the export,\nand the ones the documents compute in Typst (#var, #eq, verify-*…).",
        "vr_no_export": "The project has not been exported yet: “Import data” writes the variables of the workbooks and of Woodcore.",
        "vr_filtered": "No variable matches the filter.",
        "vr_choose_domain": "Choose a domain on the left, or tick “Every domain”.",
        "vr_domain_report": "Document",
        "vr_kind_report": "the document's own variables",
        "vr_kind_check": "a member check",
        "vr_kind_named": "a named domain",
        "vr_kind_export": "a calculation of the export",
        "vr_variable": "Variable",
        "vr_provenance": "Provenance",
        "vr_domain": "Domain",
        "vr_key": "Name to write",
        "vr_symbol": "Printed symbol",
        "vr_value": "Value",
        "vr_unit": "Unit",
        "vr_label": "Label",
        "vr_description": "Description",
        "vr_citation": "Reference",
        "vr_source": "Source",
        "vr_level": "Level of detail",
        "vr_workbook": "Workbook",
        "vr_sheet": "Sheet",
        "vr_cell": "Cell",
        "vr_formula": "Formula",
        "vr_choices": "Choices",
        "vr_open_workbook": "Open the workbook",
        "vr_open_workbook_tip": "Opens in Excel the workbook the chosen variable or case comes from; greyed out where there is none (a value of Woodcore, of a norm or of Typst) or it cannot be found.",
        "vr_no_selection": "Choose a domain or a variable to see what it carries and the commands that print it.",
        "vr_untraced": "These values are computed in Typst and are in no file: they are untraced (docs/project/purpose.md §1).",
        "vr_busy": "An export is running; «Read the documents again» will be possible afterwards.",
        "vr_failed": "“{document}” could not be read: {reason}",
        "vr_err_no_report": "this document has no entry file.",
        "vr_err_no_typst": "typst was not found.",
        "vr_err_compile_failed": "the document does not compile.",
        "vr_err_file_busy": "a file of the document is open in another program (is NextCloud syncing?). Try again in a moment.",
        "vr_err_timeout": "the reading took longer than {seconds} s.",
        "vr_err_not_json": "typst did not answer with JSON.",
        "vr_err_not_registry": "the answer is not the variable registry; is this project's engine up to date?",
        "vr_err_bad_file": "data/{file} cannot be read; its variables are missing here. {field}",
    },
}

# The details shown of a variable, in this order; a row with nothing in it is hidden rather than shown empty.
DETAIL_ROWS = ("vr_provenance", "vr_domain", "vr_key", "vr_symbol", "vr_value", "vr_unit", "vr_label", "vr_description",
               "vr_citation", "vr_level", "vr_formula", "vr_choices", "vr_workbook", "vr_sheet", "vr_cell", "vr_source")


class Read(QThread):
    """The documents read, one after the other, off the main thread, so a compile of eight seconds does not hold the window.

    A thread rather than the `QProcess` the export and the compile use, because the command that reads a
    registry is spelled in `calc/variables.py` and nowhere else (§10ter's rule about a Typst call, applied to
    this one): a QProcess here would be a second place that knows the expression, the `--root` and the
    `--in`. The project is resolved on the main thread and handed over, so a project switched meanwhile
    cannot be read by a thread that started before it.
    """

    done = Signal(str, object)     # a document, and its variables.Registry
    failed = Signal(str, object)   # a document, and a variables.VariablesError

    def __init__(self, parent, here, modes):
        super().__init__(parent)
        self.here = here
        self.modes = list(modes)

    def run(self):
        for mode in self.modes:
            try:
                # `best` and not `read`: a document's own PDF carries its variables since v0.110, so where that PDF
                # is newer than every source there is nothing to recompute and the answer comes back in under a
                # second instead of eight. Which route it took is the module's business, not this tab's -- both
                # give the same registry (calc/variables.py).
                self.done.emit(mode, model.best(self.here, mode=mode))
            except model.VariablesError as exc:
                self.failed.emit(mode, exc)
            except Exception as exc:                     # broad: handed to the tab, which says it -- never leave it saying «reading» for ever
                self.failed.emit(mode, model.VariablesError(str(exc), "not_json"))


class VariablesTab(display_view.DisplayTab, QWidget):
    """Three panes since v0.117 (issue 13): the domains of every source, the variables of the one chosen -- or of every one, the filter reaching them all --, and what the chosen variable carries; the calls that print it are the «Affichage» view's (v0.117), whose page takes the detail's place.

    ⚠️ **The contract another tab builds on** (the Formule tab of spec 2026-10-08-onglet-formule-domaines picks a
    variable here): `selected_key()` is (origin, domain, name) -- origin EXPORT or a document's mode, name None
    for a domain chosen alone --, `variable(key)` the `variables.Variable`, `address(key)` the (calculation,
    instance) an export's domain is called by, and `select_key(key)` chooses one again.
    """

    VIEWS = views.DATA_VIEWS   # «Données» and «Affichage» (views.py, v0.117)

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.t = app.t
        # ⚠️ No `dirty`, deliberately: it is what tells an **editor** from a browser here. `update_tab_marks`
        # reads it with `getattr(..., "dirty", False)` and says so -- «a browser and a reserved tab have
        # nothing to save and keep the blank» -- and `tests/test_window.py` takes every tab that has one for
        # an editor, calling `update_list_marker()` on it. A `dirty` that is always False would therefore not
        # be a harmless field: it would put this tab in that walk and owe it a marker it has no list to mark.
        # The commands tab is a browser the same way.
        self.readings = {}            # document -> the last read, from the cache or from a read of our own
        self.errors = {}              # document -> why its last read did not happen
        self.reader = None            # the thread while one runs
        self.opened = False           # whether on_shown has already decided about the first read
        self.export = sources.read_export()   # the export's four files, read now and at every showing (D-014)
        self.domains = {}             # (origin, name) -> variable_sources.Domain, every domain listed
        self.domain_key = None        # (origin, name) of the domain chosen on the left
        self.workbook_path = None     # the workbook «Ouvrir le classeur» opens, None where there is none

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.addLayout(self.build_bar())
        self.banner = QLabel("")
        self.banner.setWordWrap(True)
        self.banner.setProperty("callout", "warning")
        self.banner.setVisible(False)
        layout.addWidget(self.banner)
        layout.addWidget(self.build_pick_bar())
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.addWidget(self.build_domains())
        self.splitter.addWidget(self.build_list())
        self.splitter.addWidget(self.build_detail())
        # «Affichage»: the page takes the detail's place, and its options are a fourth pane shown in that view
        # alone -- the domains and the variables stay, so another variable can be chosen without leaving it (D-011)
        self.install_display("tab_variables", centre=2, right=None)
        self.chosen = (None, None)   # the variable and the key «Affichage» shows the commands of
        for index, stretch in enumerate((1, 3, 2)):
            self.splitter.setStretchFactor(index, stretch)
        layout.addWidget(self.splitter, 1)

        here = project.current()
        for mode in here.modes:
            found = model.cached(here, mode)
            if found is not None:
                self.readings[mode] = found
        self.refresh()
        self.restore(app.views.get("tab_variables"))

    # -- the sources ------------------------------------------------------------------

    def modes(self):
        """The documents of the current project, the one the window shows first -- what the domains are listed in."""
        here = project.current()
        current = getattr(self.app, "current_document", None)
        first = current() if callable(current) else "rs"
        return sorted(here.modes, key=lambda mode: (mode != first, here.modes.index(mode)))

    def all_domains(self):
        """[Domain]: every document's read, the one shown first, and the export's last."""
        found = []
        for mode in self.modes():
            found += sources.registry_domains(mode, self.readings.get(mode))
        return found + list(self.export.domains)

    def document_name(self, mode):
        if mode == FORMULAS:
            return self.t("tab_formula")   # a domain of the «Formule» tab: no document, the tab it is written in
        return documents.mode_name(mode, getattr(self.app, "lang", documents.DEFAULT_LANGUAGE))

    def stale(self):
        """The documents whose reading no longer answers for them as they stand."""
        here = project.current()
        return [mode for mode, found in self.readings.items() if mode in here.modes and not model.is_current(found, here, mode)]

    def provenance_code(self, var, domain):
        """What the provenance filter compares: EXCEL, WOODCORE, UNKNOWN, or `typst:<mode>`."""
        found = sources.provenance(var, domain.origin)
        return f"{model.TYPST}:{domain.origin}" if found == model.TYPST else found

    def provenance_text(self, var, domain):
        """«Excel», «Woodcore», «Typst · RS» -- a document's letters after Typst, the same in every language."""
        found = sources.provenance(var, domain.origin)
        if found == model.TYPST:
            return f"{self.t('vr_prov_typst')} · {DOCUMENT_CODES.get(domain.origin, domain.origin.upper())}"
        return self.t(f"vr_prov_{found}")

    def domain_provenance_text(self, domain):
        """A domain's provenance: a document's own, or every provenance its variables have, in a fixed order (an export's case can mix Excel cells and values Woodcore computed)."""
        if domain.origin not in (EXPORT, FORMULAS):
            return f"{self.t('vr_prov_typst')} · {DOCUMENT_CODES.get(domain.origin, domain.origin.upper())}"
        kinds = {sources.provenance(var, domain.origin) for var in domain.variables}
        return " + ".join(self.t(f"vr_prov_{kind}") for kind in (model.EXCEL, model.WOODCORE, model.UNKNOWN) if kind in kinds)

    def domain_caption(self, domain):
        return self.t("vr_domain_report") if domain.name == model.REPORT_DOMAIN and domain.origin != EXPORT else domain.name

    def kind_text(self, domain):
        return self.t(f"vr_kind_{domain.kind}")

    # -- building ----------------------------------------------------------------------

    def build_bar(self):
        """The line above the panes: what the last read found, and the one button that reads again."""
        bar = QHBoxLayout()
        self.state = QLabel("")
        self.state.setStyleSheet(f"color: {theme.colour('muted')};")
        bar.addWidget(self.state)
        bar.addStretch(1)
        self.reload_button = QPushButton(self.t("vr_reload"))
        self.reload_button.clicked.connect(self.reload)
        bar.addWidget(self.reload_button)
        self.set_reading(False)
        return bar

    def set_reading(self, reading, reason=None):
        """Whether a reading runs: the button and its tooltip are set **together**, so a button shown disabled always says why (v0.47's rule, which `tests/test_window.py` holds for every tab) and an enabled one says what it will cost -- a compile of some seconds, which is worth saying before it is paid."""
        self.reload_button.setEnabled(not reading)
        self.reload_button.setToolTip(self.t(reason or ("vr_reading" if reading else "vr_reload_hint")))

    def heading(self, key):
        label = QLabel(self.t(key))
        label.setFont(self.app.bold_font)
        return label

    def build_domains(self):
        """The left pane: every domain of every source, one flat row each -- the tree of v0.100 is gone (issue 13: «remplacer l'arbre actuel par ce volet de domaines»)."""
        pane = QWidget()
        box = QVBoxLayout(pane)
        box.setContentsMargins(0, 0, 6, 0)
        self.domains_title = self.heading("vr_domains")
        box.addWidget(self.domains_title)
        self.domain_list = QTreeWidget()
        self.domain_list.setColumnCount(len(DOMAIN_COLUMNS))
        self.domain_list.setHeaderLabels([self.t(key) for key in DOMAIN_COLUMNS])
        self.domain_list.setRootIsDecorated(False)
        self.domain_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.domain_list.setAlternatingRowColors(True)
        header = self.domain_list.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.domain_list.currentItemChanged.connect(self.on_domain_chosen)
        # a click on the domain already chosen takes the choice back from a variable to the domain itself, whose own calls are «Affichage»'s
        self.domain_list.itemClicked.connect(lambda item, _column: self.on_domain_chosen(item))
        box.addWidget(self.domain_list, 1)
        return pane

    def build_list(self):
        """The centre pane: the filters, and the variables of the domain chosen -- a flat list, no row under another."""
        pane = QWidget()
        box = QVBoxLayout(pane)
        box.setContentsMargins(0, 0, 6, 0)
        self.list_title = self.heading("vr_list")
        box.addWidget(self.list_title)

        filters = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText(self.t("vr_search"))
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self.fill_list)
        filters.addWidget(self.search, 1)
        # The units the project actually uses, commonest first, rather than every unit the algebra can read:
        # a filter offering «kN/m³» on a report that has none is a filter that says nothing.
        self.unit_box = QComboBox()
        self.unit_box.currentIndexChanged.connect(self.fill_list)
        filters.addWidget(self.unit_box)
        # Where a value comes from: Excel, Woodcore, or one document's Typst (D-004) -- the export holds every value of the load sheets, which would otherwise drown a document's own few.
        self.provenance_box = QComboBox()
        self.provenance_box.currentIndexChanged.connect(self.fill_list)
        filters.addWidget(self.provenance_box)
        box.addLayout(filters)

        scope = QHBoxLayout()
        self.all_domains_box = QCheckBox(self.t("vr_all_domains"))
        self.all_domains_box.setToolTip(self.t("vr_all_domains_hint"))
        self.all_domains_box.toggled.connect(self.fill_list)
        scope.addWidget(self.all_domains_box)
        self.results_box = QCheckBox(self.t("vr_results_only"))
        self.results_box.setToolTip(self.t("vr_results_only_hint"))
        self.results_box.toggled.connect(self.fill_list)
        scope.addWidget(self.results_box)
        scope.addStretch(1)
        box.addLayout(scope)

        self.tree = QTreeWidget()
        self.tree.setColumnCount(len(COLUMNS))
        self.tree.setHeaderLabels([self.t(key) for key in COLUMNS])
        self.tree.setRootIsDecorated(False)
        self.tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tree.setAlternatingRowColors(True)
        # The symbol as the page sets it -- q with its subscript, not `q_(k,11)` -- while the item keeps the
        # Typst source, which the search reads and a copy takes (richtext.MathDelegate, v0.92).
        self.tree.setItemDelegateForColumn(SYMBOL, richtext.MathDelegate(self.tree, [SYMBOL]))
        header = self.tree.header()
        header.setStretchLastSection(False)
        for column in (NAME, SYMBOL, VALUE, UNIT, PROVENANCE, DOMAIN):
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(LABEL, QHeaderView.ResizeMode.Stretch)
        self.tree.currentItemChanged.connect(self.on_selected)
        box.addWidget(self.tree, 1)

        self.empty = QLabel("")
        self.empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty.setWordWrap(True)
        self.empty.setStyleSheet(f"color: {theme.colour('muted')};")
        box.addWidget(self.empty, 1)
        return pane

    def build_detail(self):
        """The pane at the right: what the chosen variable carries -- since v0.117 what the loads tab showed of one too: its level, its formula, its choices, the workbook, sheet and cell it was read from (D-006).

        `hold=False` because this is a column of what is **read** and not of a form to be typed into (cards.py):
        it may be dragged narrower than its cards, where a form's column may not.
        """
        scroll, column = cards.column(hold=False)
        self.identity = cards.card(self.t("vr_variable"))
        self.identity_form = cards.form(self.identity)
        self.rows = {}
        for key in DETAIL_ROWS:
            caption = QLabel(self.t(key))
            cell = QLabel("")
            cell.setWordWrap(True)
            cell.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            self.identity_form.addRow(caption, cell)
            self.rows[key] = (caption, cell)
        self.rows["vr_formula"][1].setFont(self.app.mono_font)
        column.addWidget(self.identity)

        self.open_button = QPushButton(self.t("vr_open_workbook"))
        self.open_button.setToolTip(self.t("vr_open_workbook_tip"))   # a disabled button says why (v0.47's rule)
        self.open_button.setEnabled(False)
        self.open_button.clicked.connect(self.open_workbook)
        opener = QHBoxLayout()
        opener.addStretch(1)
        opener.addWidget(self.open_button)
        column.addLayout(opener)

        self.untraced = cards.note(self.t("vr_untraced"))
        column.addWidget(self.untraced)

        self.hint = QLabel(self.t("vr_no_selection"))
        self.hint.setWordWrap(True)
        self.hint.setStyleSheet(f"color: {theme.colour('muted')};")
        column.addWidget(self.hint)
        column.addStretch(1)
        return scroll

    # -- reading ----------------------------------------------------------------------

    def unread(self, free_only=False):
        """The documents whose reading does not answer for them -- none kept, or one kept that something has moved under since -- and, `free_only`, only those whose own PDF is current, so that reading them costs the half-second of opening it rather than a compile (variables.pdf_is_current, v0.110)."""
        here = project.current()
        out = []
        for mode in here.modes:
            if model.is_current(self.readings.get(mode), here, mode):
                continue
            if free_only and not model.pdf_is_current(here, mode):
                continue
            out.append(mode)
        return out

    def on_shown(self):
        """Brought to the front. The export's files are read again every time -- they are small, and a polar moment saved on another tab must be here when one comes back (D-014). The **first** time, the documents are read where no current reading is cached, so the tab fills without a button being pressed -- which is what the engineer asked for. Every time after that, only where it is **free**: since v0.110 a document's PDF carries its own variables, so a PDF exported since is picked up by coming back to this tab, while a reading that would cost a compile waits for «Relire» (see the module's own warning)."""
        first = not self.opened
        self.opened = True
        self.export = sources.read_export()
        if model.auto_enabled():
            wanted = self.unread(free_only=not first)
            if wanted:
                self.reload(automatic=True, modes=wanted)
                return
        self.refresh()

    def reload(self, automatic=False, modes=None):
        """Reads the documents again -- `modes`, else every document of the project -- in a thread. Refused while an export or a compilation runs -- `data/` is in what a read reads, and one written half-way through would be read half-way through."""
        if self.reader is not None:
            return
        # ⚠️ The two are not the same refusal: a click is answered with `app.busy()`, which says so in a
        # message box, and the first automatic read with a line in the bar -- a modal nobody asked for, put up
        # by a tab merely being opened, is worse than a tab that fills a moment later.
        if automatic:
            if self.app.process is not None:
                self.state.setText(self.t("vr_busy"))
                return
        elif self.app.busy():
            return
        here = project.current()
        modes = [mode for mode in (modes or self.modes()) if mode in here.modes]
        for mode in modes:
            self.errors.pop(mode, None)
        self.set_reading(True)
        self.state.setText(self.t("vr_reading"))
        self.banner.setVisible(False)
        self.reader = Read(self, here, modes)
        self.reader.done.connect(self.read_done)
        self.reader.failed.connect(self.read_failed)
        self.reader.finished.connect(self.read_finished)
        self.reader.start()

    def read_done(self, mode, registry):
        self.readings[mode] = registry
        self.errors.pop(mode, None)

    def read_failed(self, mode, error):
        self.errors[mode] = error

    def read_finished(self):
        reader, self.reader = self.reader, None
        if reader is not None:
            reader.deleteLater()
        self.set_reading(False)
        self.export = sources.read_export()   # an export the reading waited on has written data/ since
        self.refresh()
        if self.errors:
            mode, error = next(iter(self.errors.items()))
            self.app.set_status(self.failure(mode, error))

    def confirm_leave(self):
        """The window is closing. A reading is a `subprocess.run` in a thread and cannot be cut short, so it is waited for rather than left to be destroyed while it runs -- which is what Qt warns about, and what can take the process down with it.

        ⚠️ It always answers **True**: this is not an editor and there is nothing to lose, so the close is never refused. It is the one hook the window offers a tab on its way out (`closeEvent`), which is why a tab that saves nothing has one.
        """
        if self.reader is not None:
            self.reader.wait(model.TIMEOUT_S * 1000 * max(1, len(self.reader.modes)))
        return True

    def reason(self, error):
        """A failure in the window's own language, from the code the module gave it -- never by parsing its English sentence, which is `engine.Note`'s own rule (§4bis)."""
        key = f"vr_err_{error.code}"
        try:
            return self.t(key, **error.detail)
        except (KeyError, IndexError):
            return str(error)

    def failure(self, mode, error):
        """One document's failure, named: «« Base de projet » n'a pas pu être lu : le document ne compile pas.»"""
        return self.t("vr_failed", document=self.document_name(mode), reason=self.reason(error))

    # -- filling ----------------------------------------------------------------------

    def refresh(self):
        """The bar, the banner, the filters, the domains and the variables, from whatever the last reads left."""
        listed = self.all_domains()
        self.domains = {(domain.origin, domain.name): domain for domain in listed}
        if self.reader is None:
            # The bar says what is **on screen**, the banner what went wrong: a failed reading keeps the
            # values of the last good one listed below, so repeating the failure here would spend the one
            # line that can say where those values come from. The bar carries the failure only when there is
            # nothing else to say, which is a first reading that failed.
            count = sum(len(domain.variables) for domain in listed)
            if self.readings or (count and not self.errors):
                text = self.t("vr_count", count=count, domains=len(listed))
                if not self.readings and not self.errors:
                    text += " · " + self.t("vr_never")
                self.state.setText(text)
            elif self.errors:
                self.state.setText(self.failure(*next(iter(self.errors.items()))))
            else:
                self.state.setText(self.t("vr_never"))
        # The banner carries whichever there is to say, a failure before a staleness: a document that could not be
        # read, or a file of the export that could not, is the more urgent, and its own message is what says *where*
        # -- «ne compile pas» alone leaves the engineer to find the line himself, and Typst names it.
        stale = self.stale()
        failures = []
        if self.reader is None:
            for mode, error in self.errors.items():
                failures.append(self.failure(mode, error))
                output = (error.detail.get("output") or "").strip()
                if output:
                    failures.append(output)
        failures += [self.reason(error) for error in self.export.errors]
        if failures:
            self.banner.setText("\n\n".join(failures))
            self.banner.setProperty("callout", "danger")
            self.banner.setVisible(True)
        else:
            self.banner.setText(self.t("vr_stale"))
            self.banner.setProperty("callout", "warning")
            self.banner.setVisible(bool(stale) and self.reader is None)
        # a property the style sheet reads is only honoured once the widget is polished again
        self.banner.style().unpolish(self.banner)
        self.banner.style().polish(self.banner)
        self.fill_units()
        self.fill_provenances()
        self.fill_domains()

    def fill_units(self):
        """The unit filter, keeping what was chosen where the new reading still has it."""
        chosen = self.unit_box.currentData()
        counted = {}
        for domain in self.domains.values():
            for var in domain.variables:
                counted[var.unit] = counted.get(var.unit, 0) + 1
        self.unit_box.blockSignals(True)
        try:
            self.unit_box.clear()
            self.unit_box.addItem(self.t("vr_any_unit"), ANY_UNIT)
            for unit, _n in sorted(counted.items(), key=lambda kv: (-kv[1], kv[0])):
                self.unit_box.addItem(unit if unit else self.t("vr_no_unit"), unit)
            index = self.unit_box.findData(chosen)
            self.unit_box.setCurrentIndex(index if index >= 0 else 0)
        finally:
            self.unit_box.blockSignals(False)

    def fill_provenances(self):
        """The provenance filter: every provenance, Excel, Woodcore, and Typst for each document of the project -- keeping what was chosen."""
        chosen = self.provenance_box.currentData()
        self.provenance_box.blockSignals(True)
        try:
            self.provenance_box.clear()
            self.provenance_box.addItem(self.t("vr_any_provenance"), ANY_PROVENANCE)
            self.provenance_box.addItem(self.t("vr_prov_excel"), model.EXCEL)
            self.provenance_box.addItem(self.t("vr_prov_woodcore"), model.WOODCORE)
            for mode in self.modes():
                self.provenance_box.addItem(f"{self.t('vr_prov_typst')} · {DOCUMENT_CODES.get(mode, mode.upper())} — {self.document_name(mode)}",
                                            f"{model.TYPST}:{mode}")
            index = self.provenance_box.findData(chosen)
            self.provenance_box.setCurrentIndex(index if index >= 0 else 0)
        finally:
            self.provenance_box.blockSignals(False)

    def fill_domains(self):
        """One row per domain, the documents' first and the export's last; the number beside each is its whole count, which the filter does not change (D-015). The domain chosen stays chosen where it is still listed."""
        keep = self.domain_key
        self.domain_list.blockSignals(True)
        try:
            self.domain_list.clear()
            current = None
            for (origin, name), domain in self.domains.items():
                if self.pick_accept is not None and not any(self.pick_accept(var, domain) for var in domain.variables):
                    continue   # choosing for a field: a domain with nothing it could take is not offered (UI-003)
                row = QTreeWidgetItem(self.domain_list, [self.domain_caption(domain), str(len(domain.variables)), self.domain_provenance_text(domain)])
                row.setData(0, Qt.ItemDataRole.UserRole, (origin, name))
                row.setTextAlignment(1, int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter))
                tip = self.kind_text(domain) if not domain.label else f"{domain.label} — {self.kind_text(domain)}"
                row.setToolTip(0, tip)
                if origin != EXPORT:
                    row.setToolTip(2, self.document_name(origin))
                if (origin, name) == keep:
                    current = row
            if current is not None:
                self.domain_list.setCurrentItem(current)
            else:
                self.domain_key = None
        finally:
            self.domain_list.blockSignals(False)
        self.fill_list()

    def on_domain_chosen(self, item, _previous=None):
        self.domain_key = tuple(item.data(0, Qt.ItemDataRole.UserRole)) if item is not None else None
        self.tree.setCurrentItem(None)
        self.fill_list()
        self.show_selected()

    def matches(self, var, domain, needle, unit, provenance, results_only):
        if self.pick_accept is not None and not self.pick_accept(var, domain):
            return False
        if unit != ANY_UNIT and var.unit != unit:
            return False
        if provenance != ANY_PROVENANCE and self.provenance_code(var, domain) != provenance:
            return False
        if results_only and var.key not in domain.results:
            return False
        if not needle:
            return True
        haystack = " ".join((
            var.key, var.symbol, var.label, var.description, self.domain_caption(domain),
            var.unit, var.norm, var.norm_ref, model.fmt_value(var.value),
        )).lower()
        # every word of the filter, in any order: «kn max» finds F_max in kN
        return all(word in haystack for word in needle.lower().split())

    def fill_list(self, *_args):
        """The variables of the domain chosen -- or, «Tous les domaines» ticked, of every domain, each row then naming its own (D-005) -- that the filters keep, in the order their domain states them. A flat list: no row under another."""
        keep = self.selected_variable_key()
        everywhere = self.all_domains_box.isChecked()
        self.tree.setColumnHidden(DOMAIN, not everywhere)
        self.tree.blockSignals(True)
        try:
            self.tree.clear()
            needle = self.search.text().strip()
            unit = self.unit_box.currentData()
            provenance = self.provenance_box.currentData()
            results_only = self.results_box.isChecked()
            chosen = self.domains.get(self.domain_key) if self.domain_key else None
            scope = list(self.domains.values()) if everywhere else ([chosen] if chosen is not None else [])
            shown = 0
            for domain in scope:
                for var in domain.variables:
                    if not self.matches(var, domain, needle, unit, provenance, results_only):
                        continue
                    result = var.key in domain.results
                    row = QTreeWidgetItem(self.tree, [
                        (RESULT_MARK if result else "") + var.key, var.symbol, model.fmt_value(var.value), var.unit, var.label,
                        self.provenance_text(var, domain), self.domain_caption(domain),
                    ])
                    row.setData(NAME, Qt.ItemDataRole.UserRole, (domain.origin, domain.name, var.key))
                    row.setToolTip(LABEL, var.description or var.label)
                    if domain.origin != EXPORT:
                        row.setToolTip(PROVENANCE, self.document_name(domain.origin))
                    elif var.source:
                        row.setToolTip(PROVENANCE, var.source)
                    if result:
                        row.setFont(NAME, self.app.bold_font)
                    if var.is_number:
                        # a number is read from the right, so its digits line up down the column, which is
                        # what the report's own tables do with a `number` column (§3.3); a word -- a load
                        # model's name, a category of Nutzfläche -- reads from the left like the prose it is
                        row.setTextAlignment(VALUE, int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter))
                    shown += 1
            self.tree.setVisible(shown > 0)
            self.empty.setVisible(shown == 0)
            if shown == 0:
                self.empty.setText(self.empty_text(everywhere, chosen))
            for column in (NAME, SYMBOL, VALUE, UNIT, PROVENANCE, DOMAIN):
                self.tree.resizeColumnToContents(column)
            title = self.t("vr_list")
            if chosen is not None and not everywhere:
                title += f" — {self.domain_caption(chosen)}"
            self.list_title.setText(title)
        finally:
            self.tree.blockSignals(False)
        self.select_variable(keep)
        self.show_selected()

    def empty_text(self, everywhere, chosen):
        """Why the list is empty: nothing at all, a filter that keeps nothing, or no domain chosen yet."""
        if not any(domain.variables for domain in self.domains.values()):
            text = self.t("vr_empty")
            if len(self.export.missing) == len(sources.FILE_SOURCES):
                text = self.t("vr_no_export") + "\n\n" + text
            return text
        if not everywhere and chosen is None:
            return self.t("vr_choose_domain")
        return self.t("vr_filtered")

    # -- the choosing mode: a variable taken into a domain of the «Formule» tab (v0.117, spec 2026-10-08-onglet-formule-domaines REQ-015, UI-007) --

    def build_pick_bar(self):
        """The line that says the tab is choosing a variable for the «Formule» tab -- «Choisir une variable à importer dans …» --, with «Importer» and «Annuler»; hidden but while choosing. Escape gives up."""
        from PySide6.QtGui import QKeySequence, QShortcut
        from PySide6.QtWidgets import QFrame, QHBoxLayout, QPushButton
        self.pick_done = None
        self.pick_accept = None   # while a field is being linked, what it may take (spec 2026-10-11-variables-liees-champs-et-textes, UI-003)
        bar = QFrame()
        bar.setProperty("callout", "info")
        row = QHBoxLayout(bar)
        row.setContentsMargins(8, 4, 8, 4)
        self.pick_label = QLabel("")
        self.pick_label.setWordWrap(True)
        row.addWidget(self.pick_label, 1)
        self.pick_import = QPushButton(self.t("vr_pick_import"))
        self.pick_import.clicked.connect(self.pick_chosen)
        row.addWidget(self.pick_import)
        self.pick_cancel = QPushButton(self.t("vr_pick_cancel"))
        self.pick_cancel.clicked.connect(lambda: self.end_pick(None))
        row.addWidget(self.pick_cancel)
        bar.setVisible(False)
        self.pick_bar = bar
        escape = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        escape.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        escape.activated.connect(lambda: self.end_pick(None) if self.pick_done is not None else None)
        return bar

    def begin_pick(self, on_done, title, accept=None):
        """The choosing mode: `on_done(key)` is called with the (origin, domain, name) chosen, or None where the choice is given up. The window makes every other module unavailable meanwhile (MainWindow.begin_variable_pick). `accept(var, domain)`, where given, is what the field being linked may take (variable_sources.linkable): the domains and the variables it refuses are not listed until the choice ends (UI-003)."""
        self.pick_done = on_done
        self.pick_accept = accept
        self.pick_label.setText(title)
        self.pick_bar.setVisible(True)
        if accept is not None:
            self.fill_domains()

    def pick_chosen(self):
        key = self.selected_key()
        refused = key is not None and key[2] is not None and self.variable(key) is not None and self.pick_accept is not None \
            and not self.pick_accept(self.variable(key), self.domain_of(key))
        if key is None or key[2] is None or self.variable(key) is None or refused:
            self.pick_label.setText(self.t("vr_pick_none"))
            return
        self.end_pick(key)

    def end_pick(self, key):
        done, self.pick_done = self.pick_done, None
        self.pick_bar.setVisible(False)
        if self.pick_accept is not None:
            self.pick_accept = None
            self.fill_domains()   # every domain again
        if done is not None:
            done(key)

    # -- choosing ---------------------------------------------------------------------

    def selected_variable_key(self):
        item = self.tree.currentItem()
        return tuple(item.data(NAME, Qt.ItemDataRole.UserRole)) if item is not None else None

    def selected_key(self):
        """(origin, domain, name) of what is chosen -- the variable in the list, else the domain on the left with name None -- or None."""
        found = self.selected_variable_key()
        if found is not None:
            return found
        if self.domain_key is not None:
            return (*self.domain_key, None)
        return None

    def select_variable(self, key):
        if key is None:
            return
        key = tuple(key)
        for index in range(self.tree.topLevelItemCount()):
            row = self.tree.topLevelItem(index)
            if tuple(row.data(NAME, Qt.ItemDataRole.UserRole)) == key:
                self.tree.blockSignals(True)
                self.tree.setCurrentItem(row)
                self.tree.blockSignals(False)
                return

    def select_key(self, key):
        """Chooses (origin, domain, name) again: the domain on the left, then the variable where one is named."""
        if not key:
            return
        origin, name, var_key = tuple(key)
        for index in range(self.domain_list.topLevelItemCount()):
            row = self.domain_list.topLevelItem(index)
            if tuple(row.data(0, Qt.ItemDataRole.UserRole)) == (origin, name):
                self.domain_list.setCurrentItem(row)   # fills the list (on_domain_chosen)
                break
        if var_key is not None:
            self.select_variable((origin, name, var_key))
        else:
            self.tree.blockSignals(True)
            self.tree.setCurrentItem(None)
            self.tree.blockSignals(False)
        self.show_selected()

    def on_selected(self, *_):
        self.show_selected()

    def domain_of(self, key):
        return self.domains.get((key[0], key[1])) if key else None

    def variable(self, key):
        """The `variables.Variable` a key names, None for a domain's own key or one no longer listed."""
        domain = self.domain_of(key)
        if domain is None or key[2] is None:
            return None
        return domain.variable(key[2])

    def address(self, key):
        """(calculation, instance) an export's domain is called by -- `#val("s_k", domain: ("snow-load", "SL"))` --, None for a document's."""
        domain = self.domain_of(key)
        return domain.address if domain is not None and domain.origin == EXPORT else None

    def show_selected(self):
        """The right pane: what the chosen variable carries, row by row, a row with nothing in it hidden rather than shown empty -- or, a domain chosen alone, what the domain is."""
        key = self.selected_key()
        domain = self.domain_of(key)
        var = self.variable(key)
        self.identity.setVisible(domain is not None)
        self.untraced.setVisible(var is not None and domain.origin != EXPORT)   # the export's values are traced: each carries its cell
        self.hint.setVisible(domain is None)
        here = project.current()
        self.workbook_path = None
        shown = {}
        if var is not None:
            kind, workbook, sheet, cell = model.parse_source(var.source)
            if kind != "excel":
                # a value computed from a sheet's own table -- wind-load's local forces -- names the instance's workbook, as the loads tab did; one of Woodcore or a norm names none
                workbook, sheet, cell = (domain.workbook, domain.sheet, "") if kind == "python" and domain.workbook else ("", "", "")
            choices = "\n".join(f"{'▶' if choice.get('value') == var.value else '•'} {choice.get('value')} — {choice.get('desc', '')}"
                                for choice in var.choices if isinstance(choice, dict))
            shown = {
                "vr_provenance": self.provenance_text(var, domain),
                "vr_domain": self.domain_caption(domain),
                "vr_key": var.key,
                "vr_symbol": var.symbol,
                "vr_value": model.fmt_value(var.value),
                "vr_unit": var.unit,
                "vr_label": var.label,
                "vr_description": var.description,
                "vr_citation": var.citation,
                "vr_level": "" if var.level is None else str(var.level),
                "vr_formula": domain.formulas.get(var.key, ""),
                "vr_choices": choices,
                "vr_workbook": workbook,
                "vr_sheet": sheet,
                "vr_cell": cell,
                "vr_source": var.source,
            }
            if workbook:
                self.workbook_path = here.root / workbook
        elif domain is not None:
            shown = {
                "vr_provenance": self.domain_provenance_text(domain),
                "vr_domain": self.domain_caption(domain),
                "vr_value": str(len(domain.variables)),
                "vr_label": domain.label or self.kind_text(domain),
                "vr_workbook": domain.workbook,
                "vr_sheet": domain.sheet,
            }
            if domain.workbook:
                self.workbook_path = here.root / domain.workbook
        for row_key, (caption, cell) in self.rows.items():
            text = shown.get(row_key, "")
            # a symbol is set as the page sets it, the value as text: the two rows say different things
            if row_key == "vr_symbol" and text:
                cell.setTextFormat(Qt.TextFormat.RichText)
                cell.setText(richtext.math_html(text))
            else:
                cell.setTextFormat(Qt.TextFormat.PlainText)
                cell.setText(text)
            caption.setVisible(bool(text))
            cell.setVisible(bool(text))
        self.open_button.setVisible(domain is not None and domain.origin == EXPORT)
        self.open_button.setEnabled(bool(self.workbook_path and self.workbook_path.exists()))
        self.fill_commands(var, key)

    def open_workbook(self):
        if self.workbook_path and self.workbook_path.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.workbook_path)))

    def fill_commands(self, var, key):
        """The «Affichage» view told what is chosen (display_view.DisplayTab): the calls to copy left the right pane in v0.117."""
        self.chosen = (var, key)
        self.update_display()

    def display_entries(self):
        """What prints what is chosen, one command or the other with its own options (the engineer: «une commande val, une commande var … afficher l'une ou l'autre des commandes et ainsi voir les options»).

        A value of the export: `val` and `var` -- named by its calculation and its instance, the pair they read --,
        its input line `show-input`, and `var-of` and `value-of`, which print nothing: what the loads tab offered for
        a variable (D-006). A domain of the export: `show-calc`, `show-live-load` for a category of Tabelle 8, one
        `show-check` per check, the loop over every case of its calculation (D-013) and, for a load, the two summary
        tables. A value of a document: `val` and `#var(key, domain: …)` for a **named** domain only -- `#var("R_d")`
        alone can never work, `build_reference.call_var_registry` refusing it by name --, and `find`; a snippet holds
        no document's registry, so those say the PDF shows them (display_options.NOTES). A domain of a document:
        `find`. `eq` is put off (the engineer's answer of 07.10.2026).
        """
        var, key = self.chosen
        domain = self.domain_of(key)
        if domain is None:
            return []
        entries = []
        if domain.origin == EXPORT:
            calc, instance = domain.address
            if var is not None:
                entries += [
                    display_view.Entry("val", "val", "val", call_fn=lambda o, k=var.key, d=calc, s=instance: ref.call_val(k, d, s, type_=o.pop("type", None), **o)),
                    display_view.Entry("var", "var", "var", call_fn=lambda o, k=var.key, d=calc, s=instance, sym=var.symbol: ref.call_var(d, s, k, sym, **o)),
                    display_view.Entry("input", "show-input", "show-input", positional=(calc, instance, var.key)),
                    display_view.Entry("var-of", "var-of", call=ref.call_var_of(calc, instance, var.key), note="ds_note_prints_nothing"),
                ]
                if var.is_number:
                    entries.append(display_view.Entry("value-of", "value-of", call=ref.call_value_of(calc, instance, var.key), note="ds_note_prints_nothing"))
            else:
                if calc == ref.LIVE_LOAD_DOMAIN and domain.variable("q_k") is not None:
                    entries.append(display_view.Entry("live", "show-live-load", "show-live-load", positional=(instance,)))
                entries.append(display_view.Entry("calc", "show-calc", "show-calc", positional=(calc, instance),
                                                  context={"shown": shown_variables.export_choices(project.current().data_dir, calc, instance)}))   # -1 offered wherever show-calc is, loads included (spec D-16)
                entries += [display_view.Entry(f"check:{name}", f"show-check — {name}", "show-check", positional=(calc, instance, name))
                            for name in domain.checks]
                entries.append(self.loop_entry("show-calc", ref.call_instance_loop(calc)))
                if domain.file == sources.CALCULATIONS_FILE:
                    entries += [
                        display_view.Entry("summary", "show-load-summary", "show-load-summary", note=display_options.NOTES["show-load-summary"]),
                        display_view.Entry("line-summary", "show-line-load-summary", "show-line-load-summary", note=display_options.NOTES["show-line-load-summary"]),
                    ]
            return entries
        where = domain.name or None
        if var is not None:
            entries.append(display_view.Entry("val", "val", "val", note="ds_note_document_variable",
                                              call_fn=lambda o, k=var.key, d=where: ref.call_val(k, d, type_=o.pop("type", None), **o)))
            if where:
                entries.append(display_view.Entry("var", "var", "var", note="ds_note_document_variable",
                                                  call_fn=lambda o, k=var.key, d=where: ref.call_var_registry(k, d, **o)))
        entries.append(display_view.Entry("find", "find", "find", note="ds_note_document_variable",
                                          call_fn=lambda o, d=where: ref.call_find(d, o.get("type"))))
        return entries

    def on_mode(self, _mode):
        """Another document shown in the window: it is listed first -- the tab is the three documents' and reads nothing for it."""
        self.refresh()

    def set_language(self, _lang=None):
        self.rebuild_texts()

    def rebuild_texts(self):
        self.reload_button.setText(self.t("vr_reload"))
        self.domains_title.setText(self.t("vr_domains"))
        self.search.setPlaceholderText(self.t("vr_search"))
        self.all_domains_box.setText(self.t("vr_all_domains"))
        self.all_domains_box.setToolTip(self.t("vr_all_domains_hint"))
        self.results_box.setText(self.t("vr_results_only"))
        self.results_box.setToolTip(self.t("vr_results_only_hint"))
        self.domain_list.setHeaderLabels([self.t(key) for key in DOMAIN_COLUMNS])
        self.tree.setHeaderLabels([self.t(key) for key in COLUMNS])
        self.identity.setTitle(self.t("vr_variable"))
        self.open_button.setText(self.t("vr_open_workbook"))
        self.open_button.setToolTip(self.t("vr_open_workbook_tip"))
        self.untraced.setText(self.t("vr_untraced"))
        self.hint.setText(self.t("vr_no_selection"))
        for key, (caption, _cell) in self.rows.items():
            caption.setText(self.t(key))
        self.refresh()

    def view_state(self):
        origin, domain, name = self.selected_key() or (None, None, None)
        return {
            "splitter": self.splitter.sizes(),
            "search": self.search.text(),
            "unit": self.unit_box.currentData(),
            "provenance": self.provenance_box.currentData(),
            "all_domains": self.all_domains_box.isChecked(),
            "results_only": self.results_box.isChecked(),
            "source": origin,
            "domain": domain,
            "name": name,
            "opened": self.opened,
        }

    def restore(self, state):
        """A view kept through a rebuilt window. ⚠️ The splitter's sizes are applied only where they are as many as its panes: before v0.117 it had three -- the tree, the detail, the hidden display pane -- and three sizes laid on four panes would squeeze the detail to nothing (review ARCH-RISK-001). A state of that shape is otherwise read: its `source` is an origin still, and its `document` filter is gone with the column."""
        if not state:
            return
        sizes = state.get("splitter")
        if sizes and len(sizes) == self.splitter.count():
            self.splitter.setSizes(sizes)
        self.opened = bool(state.get("opened"))
        for box, value in ((self.all_domains_box, state.get("all_domains")), (self.results_box, state.get("results_only"))):
            box.blockSignals(True)
            box.setChecked(bool(value))
            box.blockSignals(False)
        self.search.blockSignals(True)
        self.search.setText(state.get("search") or "")
        self.search.blockSignals(False)
        for box, value in ((self.unit_box, state.get("unit")), (self.provenance_box, state.get("provenance"))):
            index = box.findData(value)
            if index >= 0:
                box.blockSignals(True)
                box.setCurrentIndex(index)
                box.blockSignals(False)
        self.fill_list()
        if state.get("source") is not None and state.get("domain") is not None:
            self.select_key((state["source"], state["domain"], state.get("name")))
