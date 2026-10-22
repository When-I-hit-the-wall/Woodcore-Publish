"""Woodcore's «Formules» tab (v0.117, reworked by issue #15): calculations written as blocks of commands, each a line of Typst, and the engineer's own Typst between them, gathered in calculation domains (specs docs/requirements/completed/2026-10-08-onglet-formule-domaines.md and docs/requirements/completed/2026-10-08-onglet-formules-editeur-dossiers-include.md).

The engineer, 08.10.2026: «Il faut un nouveau onglet en référence qui s'appelle formule … Son, sa fonction est de pouvoir écrire des calculs de manière simplifiée et que ça en fasse des commandes TYPST.» It takes the place of v0.100's «Formules» (keyword lines, retired then: archive/formules-dsl/), with another behaviour altogether.

**Three panes:**

* **on the left, the domains** of the project -- one file each, `<Typst root>/Formules/<id>.typ`, read again every time the tab is shown, so what VS Code wrote is what the tab shows. The list is every tab's own (grouped_list.GroupedList, issue #15 ARCH-001): folders, «Archives» at the bottom, the order dropped -- the folders and the order kept in `Woodcore-Datei/lists.json` (calc/list_order.py), the files flat in Formules/. A domain unfolds into what it computes; a click opens it.
* **in the middle, the domain open, as one text being written** (issue #15, REQ-006; issue #40): its name on the first line; then the engineer's own Typst (a title, a sentence, a formula), coloured as Typst is, and each command validated a **pill** in it -- `q_d = 4.5 kN/m`, an equation's answer, a relation and its ✔ or ✘ --, inline in its sentence where Typst prints the command inline and on a line of its own where `note: "line"` prints it apart (calc/domains/formula_layout.py), moved by a drag. A double-click opens a pill as its row of labelled fields on a line of its own, the text parted around it (D-04) -- Tab goes to the next field, Shift+Tab to the one before, Enter validates, Escape gives up, and a click elsewhere in the middle validates too (REQ-007 of issue #15). Validating writes the file, the text is written once the typing pauses: there is nothing else to save.
* **on the right, one column that scrolls** (D-12): the domain's variables always -- a click writes the one clicked into the formula being typed, and «Importer…» takes one from elsewhere through the «Variables» tab --; the options of the block chosen, a single click away whether it is being written or validated (REQ-003) -- every other argument of the command, read off its signature (display_options.SPECS), and an equation's output unit --; the domain's own card while its line is chosen, with its **ID**, the name of its file (REQ-004); and the commands to add, always.

**A domain is printed by `#include "/Formules/<id>.typ"`** (issue #15, D-01): «Affichage» shows the page that line prints and copies it. No Typst is shown in the window (principle 15) but what the engineer types between the blocks.

Everything the blocks compute is calc/domains/formula_domain.py's, at once and in Python (D-10 of v0.117); the tab shows and edits, and computes nothing itself.
"""

import source_editor  # Ctrl+S bound the one way (source_editor.save_shortcut)
import html
from dataclasses import replace

from PySide6.QtCore import QEvent, QObject, Qt, QTimer, Signal
from PySide6.QtWidgets import (QApplication, QComboBox, QFrame, QGridLayout, QHeaderView, QLabel, QLineEdit, QPlainTextEdit, QPushButton,
                               QScrollArea, QSplitter, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)

import project
import typst_objects
import units
import build_reference as ref
from domains import formula_domain as fd

import autosave
import cards
import display_options as opts
import display_view
import grouped_list
import notifications
import notices_ui
import richtext
import source_archive
import theme
import views
from formula_tab_widgets import Block, FIELDS, FORMULA_FIELDS, FormulaText, _ClickOutside, _Keys, math  # split out of this module (issue #30): every name it had is still importable from it
from formula_tab_domains import FormulaDomainsMixin  # split out of this module (issue #30): every name it had is still importable from it
from formula_tab_unfold import FormulaUnfoldMixin  # an unfolded check's card, the states of its lines (spec 2026-10-15, UI-002)
from formula_tab_blocks import FormulaBlocksMixin, merged_options  # split out of this module (issue #30): every name it had is still importable from it

STRINGS = {
    "fr": {
        "tab_formula": "Domaines",
        # the groups of the list a specialised tab's domain written out whole is shown in (issue #64, REQ-016): its kind of domain; a member check's and a steel check's by the word of its kind, the checks' tabs' own
        "fm_group_snow-load": "Neige", "fm_group_live-load": "Charges utiles", "fm_group_wind-load": "Vent", "fm_group_dead-load": "Charges permanentes", "fm_group_connector": "Connecteurs",
        "fm_group_connection": "Moment polaire", "fm_group_script": "Scripts", "fm_group_steel": "Acier – {kind}",
        "fm_domains": "Domaines de calcul",
        "fm_empty": "Aucun domaine de calcul. Choisissez « Domaine » à droite pour en créer un.",
        "fm_no_domain": "Ouvrez un domaine à gauche, ou créez-en un avec « Domaine » à droite.",
        "fm_name_placeholder": "Nom du domaine",
        "fm_name_tip": "Le nom du domaine : le titre que le rapport imprime. Entrée ou ↓ pour passer aux commandes.",
        "fm_commands": "Commandes",
        "fm_commands_hint": "Choisissez la commande à ajouter au domaine.",
        "fm_cmd_domain": "Domaine",
        "fm_cmd_domain_tip": "Un nouveau domaine de calcul : un fichier Domains/<id>.typ du projet",
        "fm_cmd_var": "var — une variable",
        "fm_cmd_eq": "eq — équation",
        "fm_cmd_verify": "verify — vérification",
        "fm_cmd_val": "val — valeur",
        "fm_cmd_var-unit": "var-unit — autre unité",
        "fm_variables": "Variables du domaine",
        "fm_variables_tip": "Un clic écrit la variable dans le calcul en cours, sous le nom affiché.",
        "fm_variables_none": "Aucune variable encore.",
        "fm_import": "Importer…",
        "fm_unfold": "Vérification dépliée",
        "fm_unfold_head": "Écrite depuis la vérification {id}",
        "fm_unfold_gone": "la vérification n’est plus dans l’export",
        "fm_unfold_no_match": "sa forme ne correspond plus aux données : régénérer",
        "fm_unfold_in_step": "Toutes les lignes sont à jour.",
        "fm_unfold_state_own": "valeur de l’ingénieur",
        "fm_unfold_state_data": "donnée changée",
        "fm_unfold_state_local": "modifiée hors de Woodcore",
        "fm_unfold_state_conflict": "conflit",
        "fm_unfold_state_missing": "ligne supprimée",
        "fm_unfold_state_in_sync": "à jour",
        "fm_unfold_import": "Importer",
        "fm_unfold_import_tip": "Reprend dans Woodcore la ligne modifiée dans le fichier : une valeur de la vérification y est écrite, une autre devient la valeur de l’ingénieur",
        "fm_unfold_import_all": "Tout importer",
        "fm_unfold_import_all_tip": "Importe toutes les lignes modifiées dans le fichier",
        "fm_unfold_take_back": "Reprendre",
        "fm_unfold_take_back_tip": "Remet la valeur de l’export à la place de la valeur de l’ingénieur",
        "fm_unfold_reinsert": "Réinsérer",
        "fm_unfold_reinsert_tip": "Remet la ligne supprimée à sa place",
        "fm_unfold_mine": "Garder la mienne",
        "fm_unfold_mine_tip": "Garde la ligne du fichier dans ce conflit",
        "fm_unfold_theirs": "Prendre celle de l’export",
        "fm_unfold_theirs_tip": "Écrit la ligne de l’export dans ce conflit",
        "fm_unfold_regenerate": "Régénérer",
        "fm_unfold_regenerate_tip": "Réécrit le calcul selon la forme de la vérification maintenant, en gardant les lignes de l’ingénieur",
        "fm_unfold_conflicts": "Conflit sur {lines} : choisissez quelle version garder.",
        "fm_unfold_done_import": "{id} : {line} importée",
        "fm_unfold_done_import_all": "{id} : lignes importées",
        "fm_unfold_done_take_back": "{id} : {line} reprend la valeur de l’export",
        "fm_unfold_done_reinsert": "{id} : {line} réinsérée",
        "fm_unfold_done_regenerate": "{id} : régénéré",
        "fm_import_tip": "Reprendre une variable de l'export, d'un autre domaine ou d'un document, choisie dans l'onglet « Variables »",
        "fm_import_unavailable": "L'import de variables arrive avec la nouvelle version de l'onglet « Variables ».",
        "fm_import_refused": "« {name} » est une variable du domaine propre au document, qui ne se reprend pas : elle n'a pas de domaine nommé.",
        "fm_pick_title": "Choisir une variable à importer dans « {domain} »",
        "fm_f_key": "Variable de calcul",
        "fm_f_key_tip": "La clé du registre : lettres, chiffres et _. Laissée vide, elle est tirée de la variable affichée.",
        "fm_f_symbol": "Variable affichée",
        "fm_f_symbol_tip": "Le symbole imprimé, en mathématiques de Typst : M_(y,d), sigma_(m,d), F_Ed.",
        "fm_f_value": "Valeur",
        "fm_f_unit": "Unité",
        "fm_f_formula": "Calcul",
        "fm_f_formula_tip": "Les variables par leur nom affiché, des nombres, une unité après un nombre (12 N / 3000 mm) ; + − * / ^, parenthèses, sqrt, min, max…",
        "fm_f_relation": "Relation",
        "fm_f_relation_tip": "Deux côtés et un signe : M_d <= M_(R,d) ; ≤ ≥ < > = ≠",
        "fm_keys": "Tab : champ suivant · Entrée : valider · Échap : abandonner",
        "fm_out_unit": "Unité de sortie",
        "fm_out_auto": "automatique ({unit})",
        "fm_options": "Options de {command}",
        "fm_domain_options": "Le domaine",
        "fm_domain_file": "Fichier",
        "fm_domain_note": "Une section imprime le domaine par #include \"/Domains/<id>.typ\" et lit une valeur par #var(clé, domain: \"<id>\") : changer l'ID oblige à corriger ces appels, que Woodcore liste.",
        "fm_delete_domain": "Supprimer le domaine…",
        "fm_delete_block": "Supprimer ce bloc",
        "fm_state_misnamed": "Son #var-domain nomme un autre id que celui de son fichier : l'id du fichier y sera réécrit à la prochaine validation.",
        "fm_state_unreadable": "Ce fichier ne peut pas être lu : {reason}. Corrigez-le dans VS Code.",
        "fm_changed_on_disk": "{file} a été modifié sur le disque depuis que Woodcore l'a lu : rien n'a été écrit par-dessus. Le domaine est relu tel qu'il est maintenant ; refaites la modification.",
        "fm_double_click": "Double-cliquer pour modifier",
        "fm_imported": "repris de {source}",
        "fm_as_unit": "unité attribuée sans conversion : {natural} → {wanted}",
        "fm_new_name": "Nouveau domaine",
        "fm_display_call": "#include",
        "fm_saved": "Domaine « {name} » enregistré.",
        "fm_missing": "{field} : à remplir.",
        "fm_key_taken": "« {name} » est déjà défini dans ce domaine : choisissez un autre nom.",
        "fm_not_number": "« {text} » n'est pas un nombre.",
        "fm_id": "ID",
        "fm_id_tip": "Le nom du fichier Domains/<id>.typ, et ce que #var(domain:) reçoit : tiré du nom tant que le domaine n'est pas enregistré ; le changer renomme le fichier.",
        "fm_id_invalid": "« {id} » n'est pas un ID : des minuscules, des chiffres et des traits d'union, en commençant par une lettre.",
        "fm_id_taken": "L'ID « {id} » est déjà celui d'un autre domaine.",
        "fm_rename_failed": "{file} ne peut pas être renommé : est-il ouvert dans un autre programme ?",
        "fm_renamed": "Domaine renommé en « {id} ».",
        "fm_cited": "L'ancien ID « {old} » est encore cité ; à corriger :\n{lines}",
        "fm_duplicate": "Dupliquer le domaine",
        "fm_copy": "{name} (copie)",
        "fm_text_tip": "Du Typst à vous : un titre (= Titre), une phrase, une formule ($ … $). Imprimé tel quel, jamais calculé.",
        "fm_text_placeholder": "Titre, texte ou formule en Typst…",
        "fm_text_command": "Un texte ne peut pas contenir #{command} : écrivez-le comme un bloc, que Woodcore calcule.",
        "fm_index_refused": "Le domaine est enregistré, mais l'index des domaines (data/formulas.json) n'a pas pu être mis à jour : {reason}",
        "fm_text_tag": "Un texte ne peut pas contenir une ligne de balises de Woodcore (// woodcore:).",
        "fm_text_unbalanced": "Ce texte ne se relirait pas tel quel une fois écrit : ses crochets sont-ils équilibrés ?",
        "fm_name_empty": "Un domaine a besoin d'un nom.",
        "fm_name_line": "Le nom d'un domaine tient sur une ligne.",
        "fm_drop_inside": "Une commande ne se place pas dans une équation, un bloc brut, une chaîne ou un appel : le domaine ne se relirait pas.",
        "fm_drop_apart": "Une commande ne se place pas dans un titre, un élément de liste ou un commentaire : elle en sortirait à l'impression.",
        "fm_drop_order": "Déplacement refusé : {reason}",
    },
    "de": {
        "tab_formula": "Domänen",
        "fm_group_snow-load": "Schnee", "fm_group_live-load": "Nutzlasten", "fm_group_wind-load": "Wind", "fm_group_dead-load": "Ständige Lasten", "fm_group_connector": "Verbindungsmittel",
        "fm_group_connection": "Polares Trägheitsmoment", "fm_group_script": "Skripte", "fm_group_steel": "Stahl – {kind}",
        "fm_domains": "Berechnungsbereiche",
        "fm_empty": "Noch kein Berechnungsbereich. Wählen Sie rechts «Bereich», um einen anzulegen.",
        "fm_no_domain": "Öffnen Sie links einen Bereich oder legen Sie rechts mit «Bereich» einen an.",
        "fm_name_placeholder": "Name des Bereichs",
        "fm_name_tip": "Der Name des Bereichs: der Titel, den der Bericht druckt. Enter oder ↓ für die Befehle.",
        "fm_commands": "Befehle",
        "fm_commands_hint": "Wählen Sie den Befehl, der dem Bereich hinzugefügt wird.",
        "fm_cmd_domain": "Bereich",
        "fm_cmd_domain_tip": "Ein neuer Berechnungsbereich: eine Datei Domains/<id>.typ des Projekts",
        "fm_cmd_var": "var — Variable",
        "fm_cmd_eq": "eq — Gleichung",
        "fm_cmd_verify": "verify — Nachweis",
        "fm_cmd_val": "val — Wert",
        "fm_cmd_var-unit": "var-unit — andere Einheit",
        "fm_variables": "Variablen des Bereichs",
        "fm_variables_tip": "Ein Klick schreibt die Variable unter ihrem angezeigten Namen in die laufende Berechnung.",
        "fm_variables_none": "Noch keine Variable.",
        "fm_import": "Importieren…",
        "fm_unfold": "Entfalteter Nachweis",
        "fm_unfold_head": "Geschrieben aus dem Nachweis {id}",
        "fm_unfold_gone": "der Nachweis ist nicht mehr im Export",
        "fm_unfold_no_match": "seine Form entspricht nicht mehr den Daten: neu erzeugen",
        "fm_unfold_in_step": "Alle Zeilen sind aktuell.",
        "fm_unfold_state_own": "Wert des Ingenieurs",
        "fm_unfold_state_data": "Daten geändert",
        "fm_unfold_state_local": "ausserhalb von Woodcore geändert",
        "fm_unfold_state_conflict": "Konflikt",
        "fm_unfold_state_missing": "Zeile gelöscht",
        "fm_unfold_state_in_sync": "aktuell",
        "fm_unfold_import": "Übernehmen",
        "fm_unfold_import_tip": "Übernimmt die in der Datei geänderte Zeile in Woodcore: ein Wert des Nachweises wird dort geschrieben, ein anderer wird zum Wert des Ingenieurs",
        "fm_unfold_import_all": "Alle übernehmen",
        "fm_unfold_import_all_tip": "Übernimmt alle in der Datei geänderten Zeilen",
        "fm_unfold_take_back": "Zurücksetzen",
        "fm_unfold_take_back_tip": "Setzt den Wert des Exports anstelle des Wertes des Ingenieurs",
        "fm_unfold_reinsert": "Wieder einfügen",
        "fm_unfold_reinsert_tip": "Setzt die gelöschte Zeile an ihren Platz zurück",
        "fm_unfold_mine": "Meine behalten",
        "fm_unfold_mine_tip": "Behält in diesem Konflikt die Zeile der Datei",
        "fm_unfold_theirs": "Die des Exports nehmen",
        "fm_unfold_theirs_tip": "Schreibt in diesem Konflikt die Zeile des Exports",
        "fm_unfold_regenerate": "Neu erzeugen",
        "fm_unfold_regenerate_tip": "Schreibt die Berechnung nach der jetzigen Form des Nachweises neu und behält die Zeilen des Ingenieurs",
        "fm_unfold_conflicts": "Konflikt bei {lines}: Wählen Sie, welche Fassung bleibt.",
        "fm_unfold_done_import": "{id}: {line} übernommen",
        "fm_unfold_done_import_all": "{id}: Zeilen übernommen",
        "fm_unfold_done_take_back": "{id}: {line} übernimmt wieder den Wert des Exports",
        "fm_unfold_done_reinsert": "{id}: {line} wieder eingefügt",
        "fm_unfold_done_regenerate": "{id}: neu erzeugt",
        "fm_import_tip": "Eine Variable aus dem Export, einem anderen Bereich oder einem Dokument übernehmen, im Register «Variablen» gewählt",
        "fm_import_unavailable": "Der Import von Variablen kommt mit der neuen Fassung des Registers «Variablen».",
        "fm_import_refused": "«{name}» ist eine Variable des eigenen Bereichs des Dokuments, die sich nicht übernehmen lässt: Sie hat keinen benannten Bereich.",
        "fm_pick_title": "Eine Variable wählen, die in «{domain}» importiert wird",
        "fm_f_key": "Rechenvariable",
        "fm_f_key_tip": "Der Schlüssel des Registers: Buchstaben, Ziffern und _. Leer gelassen, wird er aus der angezeigten Variable gebildet.",
        "fm_f_symbol": "Angezeigte Variable",
        "fm_f_symbol_tip": "Das gedruckte Symbol, in Typst-Mathematik: M_(y,d), sigma_(m,d), F_Ed.",
        "fm_f_value": "Wert",
        "fm_f_unit": "Einheit",
        "fm_f_formula": "Berechnung",
        "fm_f_formula_tip": "Die Variablen mit ihrem angezeigten Namen, Zahlen, eine Einheit nach einer Zahl (12 N / 3000 mm); + − * / ^, Klammern, sqrt, min, max…",
        "fm_f_relation": "Beziehung",
        "fm_f_relation_tip": "Zwei Seiten und ein Zeichen: M_d <= M_(R,d); ≤ ≥ < > = ≠",
        "fm_keys": "Tab: nächstes Feld · Enter: bestätigen · Esc: verwerfen",
        "fm_out_unit": "Ausgabeeinheit",
        "fm_out_auto": "automatisch ({unit})",
        "fm_options": "Optionen von {command}",
        "fm_domain_options": "Der Bereich",
        "fm_domain_file": "Datei",
        "fm_domain_note": "Ein Abschnitt druckt den Bereich mit #include \"/Domains/<id>.typ\" und liest einen Wert mit #var(Schlüssel, domain: \"<id>\"): Wer die ID ändert, muss diese Aufrufe korrigieren, die Woodcore auflistet.",
        "fm_delete_domain": "Bereich löschen…",
        "fm_delete_block": "Diesen Block löschen",
        "fm_state_misnamed": "Sein #var-domain nennt eine andere id als den Namen seiner Datei: Die id der Datei wird bei der nächsten Bestätigung hineingeschrieben.",
        "fm_state_unreadable": "Diese Datei lässt sich nicht lesen: {reason}. Korrigieren Sie sie in VS Code.",
        "fm_changed_on_disk": "{file} wurde auf der Festplatte geändert, seit Woodcore sie gelesen hat: Nichts wurde überschrieben. Der Bereich wird so neu gelesen, wie er jetzt ist; nehmen Sie die Änderung erneut vor.",
        "fm_double_click": "Doppelklick zum Bearbeiten",
        "fm_imported": "übernommen aus {source}",
        "fm_as_unit": "Einheit ohne Umrechnung zugewiesen: {natural} → {wanted}",
        "fm_new_name": "Neuer Bereich",
        "fm_display_call": "#include",
        "fm_saved": "Bereich «{name}» gespeichert.",
        "fm_missing": "{field}: auszufüllen.",
        "fm_key_taken": "«{name}» ist in diesem Bereich bereits definiert: Wählen Sie einen anderen Namen.",
        "fm_not_number": "«{text}» ist keine Zahl.",
        "fm_id": "ID",
        "fm_id_tip": "Der Name der Datei Domains/<id>.typ und das, was #var(domain:) erhält: aus dem Namen gebildet, solange der Bereich nicht gespeichert ist; eine Änderung benennt die Datei um.",
        "fm_id_invalid": "«{id}» ist keine ID: Kleinbuchstaben, Ziffern und Bindestriche, mit einem Buchstaben am Anfang.",
        "fm_id_taken": "Die ID «{id}» gehört schon einem anderen Bereich.",
        "fm_rename_failed": "{file} lässt sich nicht umbenennen: Ist die Datei in einem anderen Programm geöffnet?",
        "fm_renamed": "Bereich umbenannt in «{id}».",
        "fm_cited": "Die alte ID «{old}» wird noch zitiert; zu korrigieren:\n{lines}",
        "fm_duplicate": "Bereich duplizieren",
        "fm_copy": "{name} (Kopie)",
        "fm_text_tip": "Eigenes Typst: ein Titel (= Titel), ein Satz, eine Formel ($ … $). So gedruckt, wie es steht, nie berechnet.",
        "fm_text_placeholder": "Titel, Text oder Formel in Typst…",
        "fm_text_command": "Ein Text darf kein #{command} enthalten: Schreiben Sie es als Block, den Woodcore berechnet.",
        "fm_index_refused": "Der Bereich ist gespeichert, aber das Verzeichnis der Bereiche (data/formulas.json) konnte nicht aktualisiert werden: {reason}",
        "fm_text_tag": "Ein Text darf keine Zeile der Markierungen von Woodcore enthalten (// woodcore:).",
        "fm_text_unbalanced": "Dieser Text liesse sich nach dem Schreiben nicht unverändert zurücklesen: Sind seine Klammern ausgeglichen?",
        "fm_name_empty": "Ein Bereich braucht einen Namen.",
        "fm_name_line": "Der Name eines Bereichs steht auf einer Zeile.",
        "fm_drop_inside": "Ein Befehl steht nicht in einer Gleichung, einem Rohblock, einer Zeichenkette oder einem Aufruf: Der Bereich liesse sich nicht zurücklesen.",
        "fm_drop_apart": "Ein Befehl steht nicht in einem Titel, einem Listenpunkt oder einem Kommentar: Beim Drucken stünde er ausserhalb.",
        "fm_drop_order": "Verschieben abgelehnt: {reason}",
    },
    "en": {
        "tab_formula": "Domains",
        "fm_group_snow-load": "Snow", "fm_group_live-load": "Live loads", "fm_group_wind-load": "Wind", "fm_group_dead-load": "Permanent loads", "fm_group_connector": "Connectors",
        "fm_group_connection": "Polar moment", "fm_group_script": "Scripts", "fm_group_steel": "Steel – {kind}",
        "fm_domains": "Calculation domains",
        "fm_empty": "No calculation domain yet. Choose «Domain» on the right to make one.",
        "fm_no_domain": "Open a domain on the left, or make one with «Domain» on the right.",
        "fm_name_placeholder": "The domain's name",
        "fm_name_tip": "The domain's name: the title the report prints. Enter or ↓ to go to the commands.",
        "fm_commands": "Commands",
        "fm_commands_hint": "Choose the command to add to the domain.",
        "fm_cmd_domain": "Domain",
        "fm_cmd_domain_tip": "A new calculation domain: a file Domains/<id>.typ of the project",
        "fm_cmd_var": "var — variable",
        "fm_cmd_eq": "eq — equation",
        "fm_cmd_verify": "verify — check",
        "fm_cmd_val": "val — value",
        "fm_cmd_var-unit": "var-unit — another unit",
        "fm_variables": "The domain's variables",
        "fm_variables_tip": "A click writes the variable into the calculation being typed, by its shown name.",
        "fm_variables_none": "No variable yet.",
        "fm_import": "Import…",
        "fm_unfold": "Unfolded check",
        "fm_unfold_head": "Written from the check {id}",
        "fm_unfold_gone": "the check is no longer in the export",
        "fm_unfold_no_match": "its form no longer matches the data: regenerate",
        "fm_unfold_in_step": "Every line is up to date.",
        "fm_unfold_state_own": "the engineer's value",
        "fm_unfold_state_data": "data changed",
        "fm_unfold_state_local": "changed outside Woodcore",
        "fm_unfold_state_conflict": "conflict",
        "fm_unfold_state_missing": "line taken out",
        "fm_unfold_state_in_sync": "up to date",
        "fm_unfold_import": "Import",
        "fm_unfold_import_tip": "Takes the line changed in the file into Woodcore: a value of the check is written there, any other becomes the engineer's own",
        "fm_unfold_import_all": "Import all",
        "fm_unfold_import_all_tip": "Imports every line changed in the file",
        "fm_unfold_take_back": "Take back",
        "fm_unfold_take_back_tip": "Puts the export's value back in place of the engineer's",
        "fm_unfold_reinsert": "Reinsert",
        "fm_unfold_reinsert_tip": "Puts the line taken out back where it was",
        "fm_unfold_mine": "Keep mine",
        "fm_unfold_mine_tip": "Keeps the file's line in this conflict",
        "fm_unfold_theirs": "Take the export's",
        "fm_unfold_theirs_tip": "Writes the export's line in this conflict",
        "fm_unfold_regenerate": "Regenerate",
        "fm_unfold_regenerate_tip": "Writes the calculation again in the check's form now, keeping the engineer's lines",
        "fm_unfold_conflicts": "Conflict on {lines}: choose which version to keep.",
        "fm_unfold_done_import": "{id}: {line} imported",
        "fm_unfold_done_import_all": "{id}: lines imported",
        "fm_unfold_done_take_back": "{id}: {line} takes the export's value again",
        "fm_unfold_done_reinsert": "{id}: {line} put back",
        "fm_unfold_done_regenerate": "{id}: regenerated",
        "fm_import_tip": "Take a variable from the export, another domain or a document, chosen in the «Variables» tab",
        "fm_import_unavailable": "Importing variables comes with the new version of the «Variables» tab.",
        "fm_import_refused": "«{name}» is a variable of the document's own domain, which cannot be taken: it has no named domain.",
        "fm_pick_title": "Choose a variable to import into «{domain}»",
        "fm_f_key": "Computation variable",
        "fm_f_key_tip": "The registry's key: letters, digits and _. Left empty, it is made from the shown variable.",
        "fm_f_symbol": "Shown variable",
        "fm_f_symbol_tip": "The printed symbol, in Typst's math: M_(y,d), sigma_(m,d), F_Ed.",
        "fm_f_value": "Value",
        "fm_f_unit": "Unit",
        "fm_f_formula": "Calculation",
        "fm_f_formula_tip": "The variables by their shown name, numbers, a unit after a number (12 N / 3000 mm); + − * / ^, parentheses, sqrt, min, max…",
        "fm_f_relation": "Relation",
        "fm_f_relation_tip": "Two sides and a sign: M_d <= M_(R,d); ≤ ≥ < > = ≠",
        "fm_keys": "Tab: next field · Enter: validate · Esc: give up",
        "fm_out_unit": "Output unit",
        "fm_out_auto": "automatic ({unit})",
        "fm_options": "Options of {command}",
        "fm_domain_options": "The domain",
        "fm_domain_file": "File",
        "fm_domain_note": "A section prints the domain with #include \"/Domains/<id>.typ\" and reads a value with #var(key, domain: \"<id>\"): changing the ID means correcting those calls, which Woodcore lists.",
        "fm_delete_domain": "Delete the domain…",
        "fm_delete_block": "Delete this block",
        "fm_state_misnamed": "Its #var-domain names another id than its file's name: the file's id is written into it at the next validation.",
        "fm_state_unreadable": "This file cannot be read: {reason}. Correct it in VS Code.",
        "fm_changed_on_disk": "{file} changed on the disk since Woodcore read it: nothing was written over it. The domain is read again as it is now; make the change again.",
        "fm_double_click": "Double-click to edit",
        "fm_imported": "taken from {source}",
        "fm_as_unit": "unit given without conversion: {natural} → {wanted}",
        "fm_new_name": "New domain",
        "fm_display_call": "#include",
        "fm_saved": "Domain «{name}» saved.",
        "fm_missing": "{field}: to be filled in.",
        "fm_key_taken": "«{name}» is defined already in this domain: choose another name.",
        "fm_not_number": "«{text}» is not a number.",
        "fm_id": "ID",
        "fm_id_tip": "The name of the file Domains/<id>.typ, and what #var(domain:) is given: made from the name until the domain is saved; changing it renames the file.",
        "fm_id_invalid": "«{id}» is no ID: lower-case letters, digits and hyphens, starting with a letter.",
        "fm_id_taken": "The ID «{id}» is another domain's already.",
        "fm_rename_failed": "{file} cannot be renamed: is it open in another program?",
        "fm_renamed": "Domain renamed «{id}».",
        "fm_cited": "The old ID «{old}» is still cited; to be corrected:\n{lines}",
        "fm_duplicate": "Duplicate the domain",
        "fm_copy": "{name} (copy)",
        "fm_text_tip": "Typst of your own: a title (= Title), a sentence, a formula ($ … $). Printed as it stands, never computed.",
        "fm_text_placeholder": "Title, text or formula in Typst…",
        "fm_text_command": "A text cannot hold #{command}: write it as a block, which Woodcore computes.",
        "fm_index_refused": "The domain is saved, but the index of the domains (data/formulas.json) could not be updated: {reason}",
        "fm_text_tag": "A text cannot hold a line of Woodcore's tags (// woodcore:).",
        "fm_text_unbalanced": "This text would not read back as it is once written: do its brackets balance?",
        "fm_name_empty": "A domain needs a name.",
        "fm_name_line": "A domain's name is one line.",
        "fm_drop_inside": "A command cannot stand inside an equation, a raw block, a string or a call: the domain would not read back.",
        "fm_drop_apart": "A command cannot stand inside a heading, a list's item or a comment: it would leave it once printed.",
        "fm_drop_order": "Move refused: {reason}",
    },
}

# the commands the right pane offers, in order (D-04)
PALETTE = ("var", "eq", "verify")
# the commands whose printing «Affichage» sets line by line (issue #19) -- every one the palette writes: a `verify`'s level is how it is printed, and «Calcul» offers it no more
PRINTED = ("var", "eq", "verify")


def display_preset(command):
    """The state the «Affichage» panel of a line starts in: each argument of how it is printed as the call writes it, or as the signature does where the call leaves it (display_options.initial) -- the panel then writes only what differs (review B03)."""
    defaults = ref.signature_defaults(command.kind)
    preset = {}
    for option in opts.spec(command.kind).for_view("display").options:
        value = command.options.get(option.name)
        if value is None:
            preset[option.name] = opts.initial(option, defaults.get(option.name))
        elif option.kind == "level":
            preset[option.name] = str(value)
        elif option.kind == "choice":
            preset[option.name] = value if value in option.choices else opts.initial(option, defaults.get(option.name))
        else:
            preset[option.name] = value
    return preset


class FormulaTab(FormulaUnfoldMixin, FormulaBlocksMixin, FormulaDomainsMixin, source_editor.SourceEditorTab, display_view.DisplayTab, QWidget):
    """See the module's docstring."""

    VIEWS = views.CALC_VIEWS
    KEY = "tab_formula"
    # The domain's own refusals (formula_domain.DomainError), by code, as the window says them: English stays the export's
    REFUSALS = {"id_invalid": "fm_id_invalid", "id_taken": "fm_id_taken", "rename_failed": "fm_rename_failed", "changed_on_disk": "fm_changed_on_disk", "text_command": "fm_text_command",
                "text_tag": "fm_text_tag", "text_unbalanced": "fm_text_unbalanced", "name_empty": "fm_name_empty", "name_line": "fm_name_line"}

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.t = app.t
        self.domains = []
        self.domain = None
        self.current_id = None
        self.results = []
        self.blocks = []            # one per command of the domain open, in its order: the open one its fields, every other a pill of the text (issue #40)
        self.zones = []             # the text -- or, a block open, the text before it and the text after it (D-04)
        self.pills = {}             # uid -> block, what a pill of the text names
        self.open_block = None
        self.split_join = (False, False)
        self.target = None          # the formula field a click on a variable writes into
        self.chosen_block = None
        self.shown_ref = None       # the line chosen on the left, which «Affichage» offers (ref_of): (kind, key, the how-manyth)
        self.domain_line = False    # the domain's line chosen: its card, with the ID, shown on the right
        self.id_typed = False       # an ID the engineer wrote himself: no longer made from the name
        self.dirty = False
        self.view = "calc"
        self.panel = None
        self.unit_box = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.addWidget(self.build_left())
        self.splitter.addWidget(self.build_centre())
        self.splitter.addWidget(self.build_right())
        self.install_display(self.KEY, centre=1, right=2)
        for index, stretch in enumerate((2, 6, 3)):
            self.splitter.setStretchFactor(index, stretch)
        layout.addWidget(self.splitter, 1)
        source_editor.save_shortcut(self)   # Ctrl+S
        # the text written, and an option of a closed block, saved once the typing pauses -- not at every key (ARCH-RISK-103)
        self.text_timer = QTimer(self)
        self.text_timer.setSingleShot(True)
        self.text_timer.setInterval(700)
        self.text_timer.timeout.connect(self.write_text)
        self.option_timer = QTimer(self)
        self.option_timer.setSingleShot(True)
        self.option_timer.setInterval(400)
        self.option_timer.timeout.connect(self.write_options)
        self.clicks = _ClickOutside(self)
        QApplication.instance().installEventFilter(self.clicks)
        self.reload()
        self.restore(app.views.get(self.KEY))

    # --- building ---------------------------------------------------------------------------------

    def build_left(self):
        """The domains, by the one list every tab's left pane is (grouped_list.GroupedList, ARCH-001): folders, «Archives», the order dropped -- the folders and the order kept in Woodcore-Datei/lists.json (calc/list_order.py, D-07), the files flat in Formules/."""
        box = QWidget()
        v = QVBoxLayout(box)
        v.setContentsMargins(0, 0, 0, 0)
        title = QLabel(f"<b>{html.escape(self.t('fm_domains'))}</b>")
        self.list = grouped_list.GroupedList(STRINGS.get(self.app.lang, STRINGS["fr"]), lang=self.app.lang)
        self.list.attach_order(self.KEY, self.app.list_store, groups=True)
        self.list.setIconSize(self.app.mark_size)
        v.addWidget(grouped_list.title_row(title, self.list))
        self.list.itemClicked.connect(self.on_tree_clicked)
        self.list.foldersChanged.connect(self.on_folders_changed)
        self.list.reordered.connect(self.fill_tree)
        self.backend = fd.ArchiveBackend(project.current, self.app.list_store, self.KEY)
        self.archive = source_archive.Actions(self, lambda: project.current().formulas_dir, self.app.set_status,
                                              lambda select: self.reload(keep=select or ""), self.forget_current, backend=self.backend)
        self.archive.connect()
        v.addWidget(self.list, 1)
        self.empty = cards.note(self.t("fm_empty"))
        v.addWidget(self.empty)
        return box

    def build_centre(self):
        box = QWidget()
        v = QVBoxLayout(box)
        v.setContentsMargins(0, 0, 0, 0)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText(self.t("fm_name_placeholder"))
        self.name_edit.setToolTip(self.t("fm_name_tip"))
        font = self.name_edit.font()
        font.setPointSizeF(font.pointSizeF() * 1.25)
        font.setBold(True)
        self.name_edit.setFont(font)
        self.name_edit.installEventFilter(self)
        self.name_edit.returnPressed.connect(self.name_done)
        self.name_edit.textEdited.connect(self.name_typed)
        v.addWidget(self.name_edit)
        self.state_note = cards.note("")
        self.state_note.setVisible(False)
        v.addWidget(self.state_note)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        inner = QWidget()
        self.blocks_layout = QVBoxLayout(inner)
        self.blocks_layout.setContentsMargins(0, 4, 0, 4)
        self.blocks_layout.setSpacing(2)
        self.blocks_layout.addStretch(1)
        self.scroll.setWidget(inner)
        v.addWidget(self.scroll, 1)
        self.centre_note = cards.note(self.t("fm_no_domain"))
        v.addWidget(self.centre_note)
        return box

    def build_right(self):
        """The right pane, one column that scrolls (D-12, the engineer: «les deux. le volet pour se défiler»): the domain's variables always; the options of the block chosen; the domain's own card while its line is chosen; the commands to add, always."""
        box = QWidget()
        outer = QVBoxLayout(box)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        column = QWidget()
        v = QVBoxLayout(column)
        v.setContentsMargins(0, 0, 0, 0)
        var_card = cards.card(self.t("fm_variables"))
        cv = QVBoxLayout(var_card)
        self.var_list = QTreeWidget()
        self.var_list.setColumnCount(2)
        self.var_list.setHeaderHidden(True)
        self.var_list.setRootIsDecorated(False)
        self.var_list.setToolTip(self.t("fm_variables_tip"))
        self.var_list.setItemDelegate(richtext.MathDelegate(self.var_list, (0,)))
        self.var_list.header().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.var_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)   # a click must leave the formula field its focus
        self.var_list.itemClicked.connect(self.on_variable_clicked)
        self.var_list.setMaximumHeight(220)
        cv.addWidget(self.var_list)
        self.var_none = cards.note(self.t("fm_variables_none"))
        cv.addWidget(self.var_none)
        self.import_button = QPushButton(self.t("fm_import"))
        self.import_button.setToolTip(self.t("fm_import_tip"))
        self.import_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.import_button.clicked.connect(self.import_variable)
        cv.addWidget(self.import_button, 0, Qt.AlignmentFlag.AlignLeft)
        self.var_card = var_card
        v.addWidget(var_card)
        # an unfolded check: where each of its lines stands, and what to do with it (spec 2026-10-15, UI-002)
        v.addWidget(self.build_unfold_card())
        # the options of the block chosen -- a block being written, or one validated, a single click away (REQ-003)
        self.options_box = QWidget()
        self.options_layout = QVBoxLayout(self.options_box)
        self.options_layout.setContentsMargins(0, 0, 0, 0)
        self.options_box.setVisible(False)
        v.addWidget(self.options_box)
        # the domain's own: its file, its ID, duplicate, delete
        self.domain_card = cards.card(self.t("fm_domain_options"))
        dform = cards.form(self.domain_card)
        self.id_edit = QLineEdit()
        self.id_edit.setToolTip(self.t("fm_id_tip"))
        self.id_edit.textEdited.connect(self.id_typed_now)
        self.id_edit.editingFinished.connect(self.id_done)
        dform.addRow(self.t("fm_id"), self.id_edit)
        self.domain_file = QLabel("")
        dform.addRow(self.t("fm_domain_file"), self.domain_file)
        dform.addRow(cards.note(self.t("fm_domain_note")))
        self.duplicate_button = QPushButton(self.t("fm_duplicate"))
        self.duplicate_button.clicked.connect(self.duplicate_domain)
        dform.addRow(self.duplicate_button)
        self.delete_domain_button = QPushButton(self.t("fm_delete_domain"))
        self.delete_domain_button.clicked.connect(self.delete)
        dform.addRow(self.delete_domain_button)
        self.domain_card.setVisible(False)
        v.addWidget(self.domain_card)
        # the commands to add
        self.palette = cards.card(self.t("fm_commands"))
        pv = QVBoxLayout(self.palette)
        pv.addWidget(cards.note(self.t("fm_commands_hint")))
        self.domain_button = QPushButton(self.t("fm_cmd_domain"))
        self.domain_button.setToolTip(self.t("fm_cmd_domain_tip"))
        self.domain_button.clicked.connect(self.new_domain)
        pv.addWidget(self.domain_button)
        self.command_buttons = {}
        for kind in PALETTE:
            button = QPushButton(self.t(f"fm_cmd_{kind}"))
            button.setFocusPolicy(Qt.FocusPolicy.NoFocus)   # the cursor of a text zone stays where it is: a command goes there (REQ-006)
            button.clicked.connect(lambda _checked=False, kind=kind: self.add_block(kind))
            pv.addWidget(button)
            self.command_buttons[kind] = button
        v.addWidget(self.palette)
        v.addStretch(1)
        scroll.setWidget(column)
        outer.addWidget(scroll, 1)
        return box

    def right_cards(self):
        """What the right pane shows now, in its order -- what the tests read."""
        cards_ = [("variables", self.var_card), ("unfold", self.unfold_card), ("options", self.options_box), ("domain", self.domain_card), ("commands", self.palette)]
        return [name for name, widget in cards_ if not widget.isHidden()]

    def show_right(self):
        """The options while a block is chosen, the domain's card while its line is (D-12); the variables and the commands always."""
        chosen = self.chosen_block is not None and self.chosen_block in self.blocks
        self.options_box.setVisible(chosen and not self.domain_line)
        self.domain_card.setVisible(self.domain is not None and self.domain_line)

    # --- the domains -------------------------------------------------------------------------------


    # --- the name line and the ID ------------------------------------------------------------------


    # --- the blocks and the texts -------------------------------------------------------------------


    # --- variables taken from elsewhere (REQ-015 of v0.117) -------------------------------------------


    # --- writing ----------------------------------------------------------------------------------

    def fail(self, message):
        return autosave.refuse(self, self.t(self.KEY), message)

    def refusal(self, exc):
        """A refusal of the domain module in the window's language, by its code; its own sentence otherwise."""
        key = self.REFUSALS.get(getattr(exc, "code", ""))
        return self.t(key, **getattr(exc, "values", {})) if key else str(exc)

    def save(self, close_open=True):
        """Writes the domain open into its file and the index (formula_domain.save): what every validated block, a name changed, a block removed, a text and an option do. `close_open`: a block being written is taken as its fields say -- not where a text or an option is written while it is open."""
        if self.domain is None or self.domain.state == "unreadable":
            self.dirty = False
            return True
        open_editor = next((b for b in self.blocks if b.editing and not b.fresh), None)
        if open_editor is not None and close_open:
            try:
                open_editor.command = self.command_from(open_editor)
            except fd.DomainError as exc:
                return self.fail(str(exc))
            self.domain.commands = self.items()
        try:
            saved = fd.save(project.current(), self.domain)
        except (fd.DomainError, ValueError, OSError) as exc:
            if getattr(exc, "code", "") == "changed_on_disk":
                return self.changed_on_disk(exc)
            return self.fail(self.refusal(exc))
        self.index_refused(saved)
        self.domain.text = saved.text
        self.domain.path = saved.path
        self.domain.state = saved.state
        self.domain.declared = saved.declared
        self.current_id = saved.id
        self.id_typed = True
        self.dirty = False
        self.domains = fd.list_domains(project.current())
        self.fill_tree()
        self.state_note.setVisible(False)
        self.domain_file.setText(project.current().rel(saved.path))   # Domains/<id>.typ, or the specialised tab's folder of a domain written there (issue #64)
        self.update_list_marker()
        self.app.set_status(self.t("fm_saved", name=self.domain.name))
        return True

    def index_refused(self, saved):
        """A domain written whose index could not be (formula_domain.save's `index_problem`: another file of Formules/ unreadable, or two files of one id): said as a warning -- the save itself went through."""
        if saved is not None and saved.index_problem:
            notices_ui.tell(self.t("fm_index_refused", reason=saved.index_problem), notifications.WARNING, key="fm_index_refused", source="formula_tab")

    def changed_on_disk(self, exc):
        """The file changed on the disk since the tab read it (formula_domain.check_unchanged): nothing written over it, the change refused and said, and the domain read again as the file now is -- the lines written elsewhere are never dropped."""
        self.text_timer.stop()
        self.option_timer.stop()
        self.dirty = False
        # a notice even while saving without a question: the change typed was given up, which the status line alone would hide
        notices_ui.tell(self.refusal(exc), notifications.WARNING, key="fm_changed_on_disk", source="formula_tab")
        self.reload()
        return False

    def delete(self):
        """«Supprimer le domaine…»: a domain not yet written given up; one written into «Archives», as every tab's «Supprimer» does (source_archive.Actions, its file into Formules/archives/, never deleted)."""
        if self.domain is not None and self.current_id is None:
            self.domain = None
            self.dirty = False
            self.show_domain()
            return True
        return self.archive.delete()

    def forget_current(self):
        """The domain shown was archived: the tab opens the first left, or none."""
        self.domain = None
        self.current_id = None
        self.dirty = False
        self.reload()

    def confirm_leave(self):
        """Another domain, or another tab: the block being written and the text typed saved where they can be, as the window saves without a question (autosave.py)."""
        if self.text_timer.isActive():
            self.write_text()
        if self.option_timer.isActive():
            self.write_options()
        if self.dirty and not autosave.leave(self.app, self, "leave"):
            return not self.dirty
        return True

    def update_list_marker(self):
        """The mark of unsaved work before the domain open -- the dot, or the blank of its size on every other row, what it computes included --, and the tab's own, as the editor tabs mark the object they edit."""
        for item, entry_id in self.list.rows():
            item.setIcon(0, self.app.dirty_mark(self.dirty and entry_id == self.current_id))
        update = getattr(self.app, "update_tab_marks", None)
        if update is not None:
            update()

    # --- the window's hooks -------------------------------------------------------------------------

    def on_shown(self):
        """The tab brought to the front: the domains read again -- a domain VS Code changed is shown as it is now. The domain open is read again only where its file changed: one that did not keeps its blocks, the one chosen and the pills laid out (a reading of it renews them all)."""
        if any(b.editing for b in self.blocks) or self.text_timer.isActive():
            return
        if self.domain is not None and self.domain.path is not None and self.domain.path.is_file():
            try:
                fd.check_unchanged(self.domain)
            except fd.DomainError:
                self.reload()
                return
            self.domains = fd.list_domains(project.current())
            self.fill_tree()
            return
        self.reload()

    def on_mode(self, _mode):
        self.update_display()

    def display_entries(self):
        """«Affichage»: the domain as a section prints it, `#include "/Formules/<id>.typ"` (issue #15, D-01) -- its page, and the line «Copier» copies. A line of it chosen on the left -- a `var`, an `eq`, a `verify`, a `val`, a `var-unit` -- comes first (issue #19, D-17): every argument of how it is printed, written into its call in the file as it is changed (D-06), the page the `#include` again."""
        if self.domain is None or self.current_id is None:
            return []
        include = fd.include_call(self.domain)
        command = self.shown_command()
        line = command is not None and command.kind in PRINTED
        # the include's key differs where a line is chosen: the view keeps the entry of the same key, and a line chosen comes first (D-17) -- going from one line to another, the engineer looking at the include keeps it
        entries = [display_view.Entry("include:line" if line else "include", self.t("fm_display_call"), call=include)]
        if line:
            ref_ = self.shown_ref
            entries.insert(0, display_view.Entry(
                f"line:{ref_}", f"#{command.kind} {command.shown_symbol}", command.kind, view="display",
                panel_key=f"formula:{self.current_id}:{ref_}", preset=display_preset(command),
                call_fn=lambda _values, call=include: call, apply_fn=lambda values, r=ref_: self.write_display(r, values)))
        return entries

    def ref_of(self, command):
        """A line of the domain named by what it is rather than by its place, which a block added or removed moves (ARCH-RISK-W04): its kind, its key and how many lines of the same before it."""
        same = [c for c in self.domain.commands if not c.is_text and (c.kind, c.key) == (command.kind, command.key)]
        return (command.kind, command.key, next((i for i, c in enumerate(same) if c is command), 0))

    def shown_command(self):
        """The line `shown_ref` names in the domain open, or None."""
        if self.domain is None or self.shown_ref is None:
            return None
        kind, key, nth = self.shown_ref
        same = [c for c in self.domain.commands if not c.is_text and (c.kind, c.key) == (kind, key)]
        return same[nth] if nth < len(same) else None

    def shown_index(self):
        """The place among the lines of the list of the line chosen, or None."""
        command = self.shown_command()
        lines = [c for c in self.domain.commands if not c.is_text] if self.domain is not None else []
        return next((i for i, c in enumerate(lines) if c is command), None) if command is not None else None

    def write_display(self, ref_, values):
        """An argument of how a line is printed changed in «Affichage» (issue #19, D-06): written into its call in `Formules/<id>.typ` at once -- before the page is compiled again (ARCH-006) --, the options «Calcul» wrote kept (ARCH-005). Refused, with nothing written, in a project open read-only (WRITERS)."""
        if self.domain is None or self.domain.state == "unreadable":
            return False
        kind, key, nth = ref_
        same = [b for b in self.blocks if (b.command.kind, b.command.key) == (kind, key)]
        if nth >= len(same) or same[nth].editing:
            return False
        block = same[nth]
        names = {option.name for option in opts.spec(kind).for_view("display").options}
        command = replace(block.command, options=merged_options(block.command.options, names, values))
        if self.same([command], [block.command]):
            return True
        self.replace_command(block, command)
        self.dirty = True
        if not self.save(close_open=False):
            return False
        if self.open_block is None:
            self.render()            # `note:` changed moves the pill into its sentence or onto a line of its own (REQ-002)
        self.refresh_results()
        return True

    def set_language(self, _lang=None):
        pass

    def view_state(self):
        return {"domain": self.current_id}

    def restore(self, state):
        if isinstance(state, dict) and state.get("domain"):
            found = next((d for d in self.domains if d.id == state["domain"]), None)
            if found is not None:
                self.open_domain(found)
