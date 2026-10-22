"""Woodcore's «Positions» tab (docs/domain/positions.md §7, docs/ui/window.md §10quater): the project's positions listed and edited -- a position added, modified, renamed or deleted -- and, since v0.114, kept by Woodcore itself in `Woodcore-Datei/positions.json` (calc/positions_store.py). From v0.94 to v0.113 the tab wrote the engineer's Positionen.xlsx through calc/positions_workbook.py; the engineer asked for Woodcore to be the one source of positions (06.10.2026), so the workbook is no longer read: a project made before has it imported once and moved into its archives (positions_store.migrate, at the first opening), and «Importer depuis Excel…» here reads one found later -- adding the positions the project lacks, or writing over the ones it has, after a question.

**Only the id and the type are required.** Every other field may be left blank, and nothing the form says about a section stops it being saved: a dimension that does not read as its section type is said under the field, and the export writes the position with no section and a warning (export_all._positions). What is refused before anything is written -- in the window's language and under the field it concerns -- is what makes a row no position: no id, an id that cannot name a file or that another position holds (ignoring case, as Windows does), no type.

A write is followed by the export «Import données» runs (the window's own `reexport`, `woodcore-cli export --data-only`), so data/ and every other tab follow; where that export fails, the position stays written and the exporter's own message is shown.

The other tabs reach this one through the window (`MainWindow.new_position`), never by importing it: the schemas tab's element panel opens a new position here; the plan tab, since v0.114, writes a blank position itself (positions_store.create_blank) where a tool has none of its letter.

The tab lives in its own module, which woodcore_gui.py lists in its TABS and whose STRINGS it merges into its own: the keys carry a `po_` prefix of their own, and `warn_positions_*` the sentences of positions_store's notes (`note_text`).
"""

import source_editor  # Ctrl+S bound the one way (source_editor.save_shortcut)
import json
import re

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView, QApplication, QComboBox, QFileDialog, QFormLayout, QHBoxLayout, QHeaderView, QLabel,
    QLineEdit, QMessageBox, QPlainTextEdit, QPushButton, QSplitter, QTreeWidget, QTreeWidgetItem,
    QVBoxLayout, QWidget,
)

import cards  # the form in a card, after the website (cards.py, v0.93)
import display_view  # the «Affichage» view: the command, its options, the call and the page (display_view.py, v0.117)
import views  # the views the top bar's switch chooses between (views.py, v0.117)
import autosave  # saving without a question, and what is never saved without the engineer (autosave.py, v0.117)
import positions_store as store   # the project's positions, Woodcore's own file (calc/positions_store.py, v0.114)
import renumbering  # a position renamed everywhere it is cited, by the table a renumbering writes (issue #9)
import renumber_dialog  # deleting a position, the ones after it numbered again (issue #9)
import section_fields  # the dimension typed in fields of its type, the one widget this tab and the plan's pane share (issue #9)
import project  # where the project this tab works on is (calc/project.py)
import theme  # the colours this tab states itself (theme.py)
import validation
from domains import section
from domains import quantities   # the lengths of what the plans draw, added up from the export's rows (issue #14; the «Métré» tab shows the rest)
from domains import list_files   # the list of the positions written once in raw Typst (spec 2026-10-21-commandes-typst-refonte, Q-008)
import notifications  # every error, warning and information, gathered in one place (calc/notifications.py, v0.117)
import notices_ui  # what was a message box is a notice since v0.117 (notices_ui.tell)
import list_file_card  # the list of the positions written once in raw Typst (spec 2026-10-21-commandes-typst-refonte, Q-008)

# A position's fields, as positions_store keeps them (calc/positions_store.py's KEYS).
STRENGTH = "strength_class"
SECTION = "section_type"
MOISTURE = "moisture_class"
FIELDS = store.KEYS

# The list's columns, in the file's order, each with its header's key; the description is searched and edited, not listed.
COLUMNS = (
    ("position", "po_col_id"), ("type", "po_col_type"), ("material", "po_col_material"), (STRENGTH, "po_col_strength"),
    (SECTION, "po_col_section"), ("dimension", "po_col_dimension"), ("units", "po_col_units"), (MOISTURE, "po_col_moisture"),
)

# The column after them: the length the plans draw a position with, all its elements added up (issue #14, quantities.length_by_position). Shown, never edited, never written -- it is not a field of positions.json, and stays out of COLUMNS, which the form compares and saves.
LENGTH_COLUMN = len(COLUMNS)


# The row that stands for the position nobody has written yet. Not an id: positions_store.ID_PATTERN allows no angle bracket.
from source_editor import NEW_ROW  # the list's row of the draft, the one constant (spec 2026-10-20-indices-et-niveaux, ARCH-005)

# A refusal of positions_store, by its code, and the window's sentence for it; any other code is said with po_refused_other and the module's own English sentence.
REFUSALS = {
    "duplicate-id": "po_refused_duplicate",
    "bad-id": "po_refused_bad_id",
    "no-id": "po_refused_no_id",
    "no-type": "po_type_missing",
    "unknown-position": "po_refused_unknown",
    "moisture": "po_refused_moisture",
    "unreadable": "po_refused_unreadable",
}

# How a timber section's dimension is written, by its code (domains/section.py's TIMBER_TYPES).
TIMBER_FORMS = {"rec": "po_form_rec", "cir": "po_form_cir", "pla": "po_form_pla", "clt": "po_form_clt"}

STRINGS = {
    "fr": {
        "tab_positions": "Positions",
        "po_list": "Positions du projet",
        "po_search": "Rechercher…",
        "po_col_id": "ID", "po_col_type": "Type", "po_col_material": "Matériau", "po_col_strength": "Classe de résistance",
        "po_col_section": "Type de section", "po_col_dimension": "Dimension", "po_col_units": "Unités", "po_col_moisture": "Classe d’humidité",
        "po_col_length": "Longueur [m]", "po_col_length_tip": "La longueur dessinée sur les plans de positions, tous ses éléments additionnés",
        "po_new": "Nouvelle position", "po_duplicate": "Dupliquer", "po_delete": "Supprimer",
        "po_import": "Importer depuis Excel…",
        "po_import_tip": "Lire les positions d’un classeur Positionen.xlsx (feuille « Positions Element ») et les ajouter au projet.",
        "po_new_item": "(nouvelle, non enregistrée)",
        "po_form": "Position",
        "po_id": "ID", "po_floor": "Étage",
        "po_floor_tip": "Le deuxième caractère du numéro : U, 0, 1… Vide, celui de la dernière position de ce type.",
        "po_type": "Type", "po_material": "Matériau", "po_strength": "Classe de résistance", "po_section": "Type de section",
        "po_section_none": "(aucun : texte descriptif)", "po_dimension": "Dimension", "po_units": "Unités",
        "po_dim_card": "Dimension",
        "po_moisture": "Classe d’humidité", "po_description": "Description",
        "po_id_taken": "Il y a déjà une position « {existing} ».",
        "po_id_invalid": "Des lettres, des chiffres et _ . + -, en commençant par une lettre ou un chiffre.",
        "po_type_missing": "Une position a besoin d’un type.",
        "po_section_ok": "Lue : {text}",
        "po_section_text": "Sans type de section, la dimension reste un texte descriptif.",
        "po_section_deduced": "Lue comme rec, {text} : l’écrire dans « Type de section ».",
        "po_section_unknown": "« {code} » n’est pas un type de section de la liste.",
        "po_dim_missing": "Une section {code} a besoin d’une dimension.",
        "po_dim_bad": "« {dimension} » ne se lit pas comme une section {code} ({name}) : l’écrire {form}.",
        "po_units_bad": "Une section {code} s’écrit en {units} (vide : mm).",
        "po_section_export": "La position s’enregistre quand même : l’export la sortira sans section, avec un avertissement.",
        "po_form_rec": "b/h, p. ex. « 100/200 »",
        "po_form_cir": "d, p. ex. « 200 »",
        "po_form_pla": "t, p. ex. « 22 »",
        "po_form_clt": "par ses couches, p. ex. « 20/30/20/30/20 »",
        "po_form_steel": "par la taille de sa désignation SZS C5, {form}",
        "po_revert": "Annuler les modifications", "po_save": "Enregistrer",
        "po_unsaved_title": "Modifications non enregistrées",
        "po_unsaved": "La position « {id} » a des modifications non enregistrées.",
        "po_rename": "Renommer « {old} » en « {new} » ? Les plans, les vérifications, les schémas et les fichiers Typst qui nomment {old} sont réécrits ; une copie est gardée dans les archives du projet.{named}",
        "po_named": "\n\nNommée par : {names}.",
        "po_ref_plan": "plan {id}", "po_ref_schema": "schéma {id}",
        "po_saved": "{id} enregistrée.",
        "po_renamed": "{old} renommée {new}.",
        "po_deleted": "{id} supprimée.",
        "po_unchanged": "Rien à enregistrer : la position est telle que le projet la tient.",
        "po_import_later": "{done} Un export est en cours : « Import données » ensuite.",
        "po_import_title": "Importer des positions",
        "po_import_filter": "Classeurs Excel (*.xlsx *.xlsm)",
        "po_import_ask": "{file} contient {count} position(s), dont {existing} que le projet a déjà ({ids}). Remplacer celles-ci par celles du classeur, ou ajouter seulement les positions qui manquent ?",
        "po_import_replace": "Remplacer", "po_import_add": "Ajouter les manquantes",
        "po_import_done": "{file} : {added} position(s) ajoutée(s), {replaced} remplacée(s).",
        "po_import_nothing": "{file} ne contient aucune position à importer.",
        "po_import_failed": "{file} n’a pas pu être lu : {error}",
        "po_refused_title": "Les positions n’ont pas été modifiées",
        "po_refused_duplicate": "Il y a déjà une position « {existing} » : un ID est le nom d’un fichier, et Windows ne distingue pas les majuscules des minuscules.",
        "po_refused_bad_id": "« {position} » ne peut pas être un ID de position : des lettres, des chiffres et _ . + -, en commençant par une lettre ou un chiffre.",
        "po_refused_no_id": "Une position a besoin d’un ID.",
        "po_refused_unknown": "Le projet n’a plus de position « {position} » : elle a été renommée ou supprimée entre-temps.",
        "po_refused_moisture": "La classe d’humidité de {position} est « {value} » : 1, 2, 3 ou rien.",
        "po_refused_unreadable": "{file} ne peut pas être lu, et n’est pas écrasé : le corriger, ou le retirer pour repartir d’une liste vide.\n\n{error}",
        "po_refused_other": "Woodcore ne peut pas faire ce changement :\n\n{error}",
        "po_banner_unreadable": "Les positions du projet ne peuvent pas être lues : {error}",
        "po_new_position_tip": "Ajouter une position au projet, dans l’onglet « Positions ».",
        "warn_positions_migrated": "{count} position(s) de {workbook} reprise(s) dans {file} : le classeur n’est plus lu, il a été déplacé dans {archive}.",
        "warn_positions_migrated_kept": "{count} position(s) de {workbook} reprise(s) dans {file} ; le classeur n’a pas pu être déplacé dans {archive} : le fermer dans Excel et l’y déplacer, il n’est plus lu.",
        "warn_positions_import_no_id": "Ligne {row} : pas d’ID de position utilisable ({position}), laissée de côté.",
        "warn_positions_import_twice": "{position} figure deux fois : la première ligne est reprise.",
        "warn_positions_import_no_type": "{position} n’a pas de type, et sa lettre n’en nomme aucun : laissée de côté.",
        "warn_positions_import_type": "{position} n’a pas de type : reçoit « {type} », celui de sa lettre.",
        "warn_positions_import_moisture": "La classe d’humidité de {position}, « {value} », n’est pas 1, 2 ou 3 : laissée vide.",
    },
    "de": {
        "tab_positions": "Positionen",
        "po_list": "Positionen des Projekts",
        "po_search": "Suchen…",
        "po_col_id": "ID", "po_col_type": "Typ", "po_col_material": "Material", "po_col_strength": "Festigkeitsklasse",
        "po_col_section": "Querschnittstyp", "po_col_dimension": "Abmessung", "po_col_units": "Einheit", "po_col_moisture": "Feuchteklasse",
        "po_col_length": "Länge [m]", "po_col_length_tip": "Die auf den Positionsplänen gezeichnete Länge, alle Elemente zusammengezählt",
        "po_new": "Neue Position", "po_duplicate": "Duplizieren", "po_delete": "Löschen",
        "po_import": "Aus Excel importieren …",
        "po_import_tip": "Die Positionen einer Arbeitsmappe Positionen.xlsx (Blatt «Positions Element») lesen und dem Projekt hinzufügen.",
        "po_new_item": "(neu, nicht gespeichert)",
        "po_form": "Position",
        "po_id": "ID", "po_floor": "Geschoss",
        "po_floor_tip": "Das zweite Zeichen der Nummer: U, 0, 1 … Leer: jenes der letzten Position dieses Typs.",
        "po_type": "Typ", "po_material": "Material", "po_strength": "Festigkeitsklasse", "po_section": "Querschnittstyp",
        "po_section_none": "(keiner: beschreibender Text)", "po_dimension": "Abmessung", "po_units": "Einheit",
        "po_dim_card": "Abmessung",
        "po_moisture": "Feuchteklasse", "po_description": "Beschreibung",
        "po_id_taken": "Es gibt schon eine Position «{existing}».",
        "po_id_invalid": "Buchstaben, Ziffern und _ . + -, am Anfang ein Buchstabe oder eine Ziffer.",
        "po_type_missing": "Eine Position braucht einen Typ.",
        "po_section_ok": "Gelesen: {text}",
        "po_section_text": "Ohne Querschnittstyp bleibt die Abmessung beschreibender Text.",
        "po_section_deduced": "Als rec gelesen, {text}: im «Querschnittstyp» angeben.",
        "po_section_unknown": "«{code}» ist kein Querschnittstyp der Liste.",
        "po_dim_missing": "Ein Querschnitt {code} braucht eine Abmessung.",
        "po_dim_bad": "«{dimension}» lässt sich nicht als Querschnitt {code} ({name}) lesen: {form} schreiben.",
        "po_units_bad": "Ein Querschnitt {code} wird in {units} geschrieben (leer: mm).",
        "po_section_export": "Die Position wird trotzdem gespeichert: der Export gibt sie ohne Querschnitt aus, mit einer Warnung.",
        "po_form_rec": "b/h, z. B. «100/200»",
        "po_form_cir": "d, z. B. «200»",
        "po_form_pla": "t, z. B. «22»",
        "po_form_clt": "als seine Lagen, z. B. «20/30/20/30/20»",
        "po_form_steel": "als Grösse seiner Bezeichnung nach SZS C5, {form}",
        "po_revert": "Änderungen verwerfen", "po_save": "Speichern",
        "po_unsaved_title": "Nicht gespeicherte Änderungen",
        "po_unsaved": "Die Position «{id}» hat nicht gespeicherte Änderungen.",
        "po_rename": "«{old}» in «{new}» umbenennen? Pläne, Nachweise, Schemas und Typst-Dateien, die {old} nennen, werden umgeschrieben; eine Kopie bleibt im Archiv des Projekts.{named}",
        "po_named": "\n\nGenannt von: {names}.",
        "po_ref_plan": "Plan {id}", "po_ref_schema": "Schema {id}",
        "po_saved": "{id} gespeichert.",
        "po_renamed": "{old} in {new} umbenannt.",
        "po_deleted": "{id} gelöscht.",
        "po_unchanged": "Nichts zu speichern: die Position steht so im Projekt.",
        "po_import_later": "{done} Ein Export läuft: danach «Daten importieren».",
        "po_import_title": "Positionen importieren",
        "po_import_filter": "Excel-Arbeitsmappen (*.xlsx *.xlsm)",
        "po_import_ask": "{file} enthält {count} Position(en), davon {existing}, die das Projekt schon hat ({ids}). Diese durch jene der Arbeitsmappe ersetzen, oder nur die fehlenden Positionen hinzufügen?",
        "po_import_replace": "Ersetzen", "po_import_add": "Fehlende hinzufügen",
        "po_import_done": "{file}: {added} Position(en) hinzugefügt, {replaced} ersetzt.",
        "po_import_nothing": "{file} enthält keine Position zum Importieren.",
        "po_import_failed": "{file} konnte nicht gelesen werden: {error}",
        "po_refused_title": "Die Positionen wurden nicht geändert",
        "po_refused_duplicate": "Es gibt schon eine Position «{existing}»: eine ID ist der Name einer Datei, und Windows unterscheidet Gross- und Kleinschreibung nicht.",
        "po_refused_bad_id": "«{position}» kann keine Positions-ID sein: Buchstaben, Ziffern und _ . + -, am Anfang ein Buchstabe oder eine Ziffer.",
        "po_refused_no_id": "Eine Position braucht eine ID.",
        "po_refused_unknown": "Das Projekt hat keine Position «{position}» mehr: sie wurde inzwischen umbenannt oder gelöscht.",
        "po_refused_moisture": "Die Feuchteklasse von {position} ist «{value}»: 1, 2, 3 oder nichts.",
        "po_refused_unreadable": "{file} lässt sich nicht lesen und wird nicht überschrieben: die Datei berichtigen, oder sie entfernen, um mit einer leeren Liste neu zu beginnen.\n\n{error}",
        "po_refused_other": "Woodcore kann diese Änderung nicht vornehmen:\n\n{error}",
        "po_banner_unreadable": "Die Positionen des Projekts lassen sich nicht lesen: {error}",
        "po_new_position_tip": "Eine Position zum Projekt hinzufügen, im Register «Positionen».",
        "warn_positions_migrated": "{count} Position(en) aus {workbook} in {file} übernommen: die Arbeitsmappe wird nicht mehr gelesen und wurde nach {archive} verschoben.",
        "warn_positions_migrated_kept": "{count} Position(en) aus {workbook} in {file} übernommen; die Arbeitsmappe konnte nicht nach {archive} verschoben werden: in Excel schliessen und dorthin verschieben, sie wird nicht mehr gelesen.",
        "warn_positions_import_no_id": "Zeile {row}: keine brauchbare Positions-ID ({position}), ausgelassen.",
        "warn_positions_import_twice": "{position} steht zweimal da: die erste Zeile wird übernommen.",
        "warn_positions_import_no_type": "{position} hat keinen Typ, und sein Buchstabe nennt keinen: ausgelassen.",
        "warn_positions_import_type": "{position} hat keinen Typ: erhält «{type}», jenen seines Buchstabens.",
        "warn_positions_import_moisture": "Die Feuchteklasse von {position}, «{value}», ist nicht 1, 2 oder 3: leer gelassen.",
    },
    "en": {
        "tab_positions": "Positions",
        "po_list": "The project's positions",
        "po_search": "Search…",
        "po_col_id": "ID", "po_col_type": "Type", "po_col_material": "Material", "po_col_strength": "Strength class",
        "po_col_section": "Section type", "po_col_dimension": "Dimension", "po_col_units": "Units", "po_col_moisture": "Moisture class",
        "po_col_length": "Length [m]", "po_col_length_tip": "The length the position plans draw, all its elements added up",
        "po_new": "New position", "po_duplicate": "Duplicate", "po_delete": "Delete",
        "po_import": "Import from Excel…",
        "po_import_tip": "Read the positions of a Positionen.xlsx workbook (sheet «Positions Element») and add them to the project.",
        "po_new_item": "(new, not saved)",
        "po_form": "Position",
        "po_id": "ID", "po_floor": "Floor",
        "po_floor_tip": "The second character of the number: U, 0, 1… Empty: the one of the last position of this type.",
        "po_type": "Type", "po_material": "Material", "po_strength": "Strength class", "po_section": "Section type",
        "po_section_none": "(none: descriptive text)", "po_dimension": "Dimension", "po_units": "Units",
        "po_dim_card": "Dimension",
        "po_moisture": "Moisture class", "po_description": "Description",
        "po_id_taken": "There is a position «{existing}» already.",
        "po_id_invalid": "Letters, digits and _ . + -, starting with a letter or a digit.",
        "po_type_missing": "A position needs a type.",
        "po_section_ok": "Read: {text}",
        "po_section_text": "Without a section type, the dimension stays descriptive text.",
        "po_section_deduced": "Read as rec, {text}: say so in «Section type».",
        "po_section_unknown": "«{code}» is not a section type of the list.",
        "po_dim_missing": "A {code} section needs a dimension.",
        "po_dim_bad": "«{dimension}» does not read as a {code} section ({name}): write it {form}.",
        "po_units_bad": "A {code} section is written in {units} (empty: mm).",
        "po_section_export": "The position is saved all the same: the export writes it without a section, with a warning.",
        "po_form_rec": "b/h, e.g. «100/200»",
        "po_form_cir": "d, e.g. «200»",
        "po_form_pla": "t, e.g. «22»",
        "po_form_clt": "as its layers, e.g. «20/30/20/30/20»",
        "po_form_steel": "as the size of its SZS C5 designation, {form}",
        "po_revert": "Discard changes", "po_save": "Save",
        "po_unsaved_title": "Unsaved changes",
        "po_unsaved": "The position «{id}» has unsaved changes.",
        "po_rename": "Rename «{old}» to «{new}»? The plans, checks, schemas and Typst files naming {old} are rewritten; a copy is kept in the project's archives.{named}",
        "po_named": "\n\nNamed by: {names}.",
        "po_ref_plan": "plan {id}", "po_ref_schema": "schema {id}",
        "po_saved": "{id} saved.",
        "po_renamed": "{old} renamed {new}.",
        "po_deleted": "{id} deleted.",
        "po_unchanged": "Nothing to save: the position is as the project holds it.",
        "po_import_later": "{done} An export is running: «Import data» afterwards.",
        "po_import_title": "Import positions",
        "po_import_filter": "Excel workbooks (*.xlsx *.xlsm)",
        "po_import_ask": "{file} holds {count} position(s), {existing} of which the project has already ({ids}). Replace those with the workbook's, or add only the positions that are missing?",
        "po_import_replace": "Replace", "po_import_add": "Add the missing ones",
        "po_import_done": "{file}: {added} position(s) added, {replaced} replaced.",
        "po_import_nothing": "{file} holds no position to import.",
        "po_import_failed": "{file} could not be read: {error}",
        "po_refused_title": "The positions were not changed",
        "po_refused_duplicate": "There is a position «{existing}» already: an ID is the name of a file, and Windows does not tell upper from lower case.",
        "po_refused_bad_id": "«{position}» cannot be a position ID: letters, digits and _ . + -, starting with a letter or a digit.",
        "po_refused_no_id": "A position needs an ID.",
        "po_refused_unknown": "The project has no position «{position}» any more: it was renamed or deleted meanwhile.",
        "po_refused_moisture": "The moisture class of {position} is «{value}»: 1, 2, 3 or nothing.",
        "po_refused_unreadable": "{file} cannot be read, and is not written over: correct it, or remove it to start again from an empty list.\n\n{error}",
        "po_refused_other": "Woodcore cannot make this change:\n\n{error}",
        "po_banner_unreadable": "The project's positions cannot be read: {error}",
        "po_new_position_tip": "Add a position to the project, in the «Positions» tab.",
        "warn_positions_migrated": "{count} position(s) of {workbook} taken into {file}: the workbook is no longer read and was moved to {archive}.",
        "warn_positions_migrated_kept": "{count} position(s) of {workbook} taken into {file}; the workbook could not be moved into {archive}: close it in Excel and move it there, it is no longer read.",
        "warn_positions_import_no_id": "Row {row}: no usable position ID ({position}), left out.",
        "warn_positions_import_twice": "{position} is there twice: the first row is taken.",
        "warn_positions_import_no_type": "{position} has no type, and its letter names none: left out.",
        "warn_positions_import_type": "{position} has no type: given «{type}», its letter's.",
        "warn_positions_import_moisture": "The moisture class of {position}, «{value}», is not 1, 2 or 3: left blank.",
    },
}


def plain_label(text, wrap=False):
    """A label showing `text` exactly as it is -- given a text that looks like HTML, QLabel would render it as HTML."""
    label = QLabel(text)
    label.setTextFormat(Qt.TextFormat.PlainText)
    label.setWordWrap(wrap)
    return label


def cell_text(value):
    """A value as the form shows it and compares it: a text stripped, a whole number without its «.0», nothing as ""."""
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def floor_of(pid, symbol):
    """The floor an id carries after its symbol -- T101's «1» -- or None where the id is not numbered that way."""
    match = re.fullmatch(re.escape(symbol) + r"(.)(\d+)", pid or "", re.IGNORECASE) if symbol else None
    return match.group(1) if match else None


def references(pid):
    """What names position `pid` in the project's own drawings, as («plan», id) and («schema», id): a plan's element labelled with it, a schema's element carrying it. A connector reaches its positions through a schema's elements, so the schema is what it names. Read from the sources, which is what the next export reads."""
    here = project.current()
    found = []
    for kind, folder, key in (("plan", here.plans_dir, "label"), ("schema", here.details_dir, "position")):
        if not folder.is_dir():
            continue
        for path in sorted(folder.glob("*.json")):
            try:
                source = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            elements = source.get("elements", []) if isinstance(source, dict) else []
            if any(isinstance(e, dict) and str(e.get(key) or "").strip() == pid for e in elements):
                found.append((kind, path.stem))
    return found


def strength_classes():
    """The strength classes the form offers: SIA 265 Tabellen 8 and 9's timber, then SIA 263 Tabelle 1's steels -- read from calc/norms/, written nowhere here."""
    from norms import sia263, sia265
    return list(sia265.grades()) + list(sia263.grades())


class PositionList(QTreeWidget):
    """The positions, one flat row each, in the file's order -- the draft not written yet as a row of its own. `rows()` is what a test of the window's marks reads (tests/test_window.py)."""

    ID_ROLE = Qt.ItemDataRole.UserRole

    def rows(self):
        return [(self.topLevelItem(i), self.topLevelItem(i).data(0, self.ID_ROLE)) for i in range(self.topLevelItemCount())]

    def ids(self):
        return [pid for _item, pid in self.rows()]

    def item_of(self, pid):
        return next((item for item, key in self.rows() if key == pid), None)


class PositionsTab(source_editor.SourceEditorTab, display_view.DisplayTab, QWidget):
    """Lists the project's positions, edits one at a time, and writes it back through positions_store."""
    WORDS = "po"   # the prefix of its words for the question about unsaved changes (source_editor.SourceEditorTab)


    VIEWS = views.ENTRY_VIEWS   # «Saisie» and «Affichage» (views.py, v0.117)
    GRAPH_KIND = "position"   # a position of the graph of dependencies, opened here by MainWindow.open_object -- the palette's «@T001» (issue #83)

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.t = app.t
        self.loading = False    # set while the form is filled, so filling it is not taken for an edit
        self.dirty = False
        self.current_id = None  # the position the form holds; None for a position not written yet
        self.original = None    # that position's values as the project held them, what a save compares with
        self.draft_symbol = ""  # the symbol a new position was opened for, where its type names none
        self.proposed = ""      # the id last proposed, which the ID field follows while it still holds it
        self.rows = []          # the project's positions, as positions_store reads them
        self.error = None       # why positions.json could not be read, where it could not
        self.type_language = app.lang   # the language a position's type is shown in: the project's, refreshed whenever the positions are read (v0.116)
        self.fitted = False     # the list's columns sized to what they hold, once: a width the engineer dragged is kept after that
        self.quantity_rows = []  # what the position plans draw, one row an element (quantities.rows), read with the positions (issue #14)
        self.lengths = {}        # the length each position is drawn with (quantities.length_by_position)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.addWidget(self.build_list())
        self.splitter.addWidget(self.build_form())
        self.install_display("tab_positions", centre=1, right=None)   # «Affichage»: the list of the positions, its options, the call and the page (v0.117)
        self.splitter.setStretchFactor(0, 3)
        self.splitter.setStretchFactor(1, 2)
        layout.addWidget(self.splitter, 1)
        source_editor.save_shortcut(self)   # Ctrl+S, as in every editor tab
        self.restore(app.views.get("tab_positions"))

    def display_entries(self):
        """What prints the positions (v0.117, «Affichage»): the list of the positions, written once in raw Typst and included where a section prints it (spec 2026-10-21-commandes-typst-refonte, Q-008, UI-002) -- the card «Fichier de la liste» writes it."""
        here = project.current()
        return [display_view.Entry("list", "include", call=f'#include "{here.from_root(list_files.path(here, "position-list"))}"')]

    # -- building ---------------------------------------------------------------------

    def heading(self, text):
        label = plain_label(text)
        label.setFont(self.app.bold_font)
        return label

    def note(self):
        """A line under a field, saying why it cannot be written or what it will be read as: empty and hidden until then."""
        label = plain_label("", wrap=True)
        label.setVisible(False)
        return label

    def build_list(self):
        panel = QWidget()
        box = QVBoxLayout(panel)
        box.setContentsMargins(0, 0, 6, 0)
        box.addWidget(self.heading(self.t("po_list")))
        self.search = QLineEdit()
        self.search.setPlaceholderText(self.t("po_search"))
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self.apply_search)
        box.addWidget(self.search)
        self.list = PositionList()
        self.list.setColumnCount(len(COLUMNS) + 1)
        self.list.setHeaderLabels([self.t(key) for _header, key in COLUMNS] + [self.t("po_col_length")])
        self.list.headerItem().setToolTip(LENGTH_COLUMN, self.t("po_col_length_tip"))
        self.list.headerItem().setTextAlignment(LENGTH_COLUMN, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.list.setRootIsDecorated(False)
        self.list.setUniformRowHeights(True)
        # several positions selected with Ctrl and Shift, for the quantities of «Positions sélectionnées» (issue #14, D-011); the one the form holds is still the current one
        self.list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.list.setIconSize(self.app.mark_size)
        self.list.header().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.list.header().setStretchLastSection(False)
        self.list.currentItemChanged.connect(self.on_list_change)
        box.addWidget(self.list, 1)
        row = QHBoxLayout()
        for key, slot in (("po_new", self.new), ("po_duplicate", self.duplicate), ("po_delete", self.delete)):
            button = QPushButton(self.t(key))
            button.clicked.connect(slot)
            row.addWidget(button)
        row.addStretch(1)
        self.import_button = QPushButton(self.t("po_import"))
        self.import_button.setToolTip(self.t("po_import_tip"))
        self.import_button.clicked.connect(self.import_excel)
        row.addWidget(self.import_button)
        box.addLayout(row)
        return panel

    def combo(self, editable=True):
        box = QComboBox()
        box.setEditable(editable)
        box.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        box.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        box.setMinimumContentsLength(10)
        return box

    def build_form(self):
        outer = QWidget()
        shell = QVBoxLayout(outer)
        shell.setContentsMargins(6, 0, 0, 0)
        # the form in a card, on the soft ground of a column that scrolls up and down and never sideways (cards.py, v0.93)
        area, box = cards.column()
        self.banner = plain_label("", wrap=True)
        self.banner.setVisible(False)
        box.addWidget(self.banner)

        group = cards.card(self.t("po_form"))
        form = QFormLayout(group)
        self.fields, self.captions = {}, {}
        self.id_edit = QLineEdit()
        self.id_edit.textEdited.connect(self.on_id_edited)
        self.id_note = self.note()
        self.add_row(form, "position", "po_id", self.id_edit, self.id_note)
        self.floor_edit = QLineEdit()
        self.floor_edit.setMaxLength(1)
        self.floor_edit.setMaximumWidth(48)
        self.floor_edit.setToolTip(self.t("po_floor_tip"))
        self.floor_edit.textEdited.connect(self.on_floor)
        self.floor_caption = QLabel(self.t("po_floor"))
        form.addRow(self.floor_caption, self.floor_edit)
        self.type_combo = self.combo()
        self.type_combo.currentTextChanged.connect(self.on_type)
        self.type_note = self.note()
        self.add_row(form, "type", "po_type", self.type_combo, self.type_note)
        self.material_combo = self.combo()
        self.material_combo.currentTextChanged.connect(self.changed)
        self.add_row(form, "material", "po_material", self.material_combo)
        self.strength_combo = self.combo()
        self.strength_combo.currentTextChanged.connect(self.changed)
        self.add_row(form, STRENGTH, "po_strength", self.strength_combo)
        self.section_combo = self.combo(editable=False)
        self.section_combo.addItem(self.t("po_section_none"), "")
        kinds = [entry for entry in section.TYPES]
        for i, entry in enumerate(kinds):
            if i == 0 or entry["kind"] != kinds[i - 1]["kind"]:
                self.section_combo.insertSeparator(self.section_combo.count())
            self.section_combo.addItem(f"{entry['code']} — {entry.get(self.app.lang) or entry['de']}", entry["code"])
        self.section_combo.currentIndexChanged.connect(self.on_section)
        self.add_row(form, SECTION, "po_section", self.section_combo)
        # The dimension, in a section of its own under the section type (v0.117, the engineer: «lorsque le type de section est donné, il doit y avoir une section "Dimension" qui apparait avec des textbox différentes à remplir en fonction du type de section»): a box for each number the type has -- `rec` its width and height, `pla` its thickness, a steel family its form's, a CLT panel a box a layer (issue #9; section_fields.DimensionFields, shared with the plan's pane) -- and, for no type or a text its type does not read, the line of text it always was. What is typed is written into that line, which stays the one the form reads (`form_values`).
        self.dimension_edit = QLineEdit()
        self.dimension_edit.textEdited.connect(self.changed)
        self.section_note = self.note()
        dimension_card = cards.card(self.t("po_dim_card"))
        dimension_form = QFormLayout(dimension_card)
        self.dimension_fields = section_fields.DimensionFields(self.app.lang)
        self.dimension_fields.edited.connect(self.on_dimension_field)
        dimension_form.addRow(self.dimension_fields)
        self.dim_fields = {}  # the boxes shown, by their field -- «b», «h», «layer1» … -- kept in place for whoever holds it
        self.dim_by_fields = False
        self.add_row(dimension_form, "dimension", "po_dimension", self.dimension_edit)
        self.units_combo = self.combo()
        self.units_combo.currentTextChanged.connect(self.changed)
        self.add_row(dimension_form, "units", "po_units", self.units_combo)
        dimension_form.addRow(self.section_note)
        form.addRow(dimension_card)
        self.dimension_card = dimension_card
        self.moisture_combo = self.combo(editable=False)
        self.moisture_combo.addItem("—", None)
        for value in validation.moisture_classes():
            self.moisture_combo.addItem(str(value), value)
        self.moisture_combo.currentIndexChanged.connect(self.changed)
        self.add_row(form, MOISTURE, "po_moisture", self.moisture_combo)
        self.description_edit = QPlainTextEdit()
        self.description_edit.setTabChangesFocus(True)
        self.description_edit.setMinimumHeight(3 * self.fontMetrics().height() + 12)
        self.description_edit.setMaximumHeight(8 * self.fontMetrics().height())
        self.description_edit.textChanged.connect(self.changed)
        self.add_row(form, "description", "po_description", self.description_edit)
        box.addWidget(group)
        # the list of the positions, written once in raw Typst and added to (spec 2026-10-21-commandes-typst-refonte, Q-008)
        self.list_card = list_file_card.ListFileCard(self.app, "position-list")
        box.addWidget(self.list_card.card)
        box.addStretch(1)
        shell.addWidget(area, 1)

        actions = QHBoxLayout()
        actions.addStretch(1)
        revert = QPushButton(self.t("po_revert"))
        revert.clicked.connect(self.revert)
        actions.addWidget(revert)
        save = QPushButton(self.t("po_save"))
        save.setDefault(True)
        save.clicked.connect(self.save)
        actions.addWidget(save)
        shell.addLayout(actions)
        return outer

    def read_quantities(self):
        """The length the plans draw each position with, read from the export (`data/quantities.json`'s rows, added up by `quantities.length_by_position`) -- nothing measured in the window since the «Métré» tab took the card «Métrés» (spec 2026-10-21-commandes-typst-refonte, UI-003). An export not written yet, or one that does not read, gives no length."""
        self.quantity_rows, self.lengths = [], {}
        try:
            data = json.loads((project.current().data_dir / "quantities.json").read_text(encoding="utf-8"))
        except (OSError, ValueError, project.ProjectError):
            return
        self.quantity_rows = data.get("rows", [])
        self.lengths = quantities.length_by_position(self.quantity_rows)

    def add_row(self, form, header, key, widget, note=None):
        caption = QLabel(self.t(key))
        if note is None:
            form.addRow(caption, widget)
        else:
            cell = QWidget()
            column = QVBoxLayout(cell)
            column.setContentsMargins(0, 0, 0, 0)
            column.setSpacing(2)
            column.addWidget(widget)
            column.addWidget(note)
            form.addRow(caption, cell)
        self.fields[header], self.captions[header] = widget, caption

    # -- the positions read --------------------------------------------------------------

    def read_positions(self):
        """The project's positions read afresh, and the banner saying where they cannot be. Never raises: a file that cannot be read is said, lists nothing, and is not written over (positions_store refuses to)."""
        self.error = None
        self.type_language = store.project_language(fallback=self.app.lang)
        try:
            self.rows = store.read()
        except store.PositionsError as exc:
            self.rows, self.error = [], exc
        self.read_quantities()
        self.fill_choices()
        self.update_banner()

    def update_banner(self):
        text = self.t("po_banner_unreadable", error=self.error) if self.error is not None else ""
        self.banner.setText(text)
        self.banner.setProperty("callout", "danger" if text else "info")
        self.banner.style().unpolish(self.banner)
        self.banner.style().polish(self.banner)
        self.banner.setVisible(bool(text))

    def row_of(self, pid):
        return next((row for row in self.rows if row["position"] == pid), None)

    def ids(self):
        return [row["position"] for row in self.rows if row["position"]]

    def lists_object(self, ident):
        """Whether position `ident` is one of the project's (MainWindow.open_object): its rows, Woodcore's own positions.json, and not a folder of sources."""
        return ident in self.ids()

    def open_object(self, ident):
        """Position `ident` opened in the form, the draft open left as choosing another row leaves it (`confirm_leave`)."""
        if ident == self.current_id or ident not in self.ids() or not self.confirm_leave():
            return
        self.load(ident)
        self.reload_list(ident)

    def fill_choices(self):
        """What the type, material, strength class and units offer: the STE types, a few materials, SIA 265's and SIA 263's classes, the timber units -- and whatever the project's positions already hold."""
        def offered(header, base=()):
            values = list(base) + [cell_text(row.get(header)) for row in self.rows]
            return list(dict.fromkeys(v for v in values if v))

        loading, self.loading = self.loading, True
        for combo, header, base in ((self.type_combo, "type", store.types()), (self.material_combo, "material", store.MATERIALS),
                                    (self.strength_combo, STRENGTH, strength_classes()), (self.units_combo, "units", ("mm", "cm", "m"))):
            if combo is self.type_combo:
                key = self.type_key()
                combo.clear()
                combo.addItem("", "")
                for name in offered(header, base):
                    combo.addItem(self.type_text(name), name)   # shown in the project's language, stored as the key (German, the STE name); a free type is its own key and text
                combo.setCurrentText(self.type_text(key))
                continue
            text = combo.currentText()
            combo.clear()
            combo.addItem("")
            combo.addItems(offered(header, base))
            combo.setCurrentText(text)
        self.loading = loading

    # -- the list ------------------------------------------------------------------------

    def fill_list(self, select=None):
        loading, self.loading = self.loading, True
        self.list.clear()
        for row in self.rows:
            pid = row["position"]
            length = self.lengths.get(pid)
            item = QTreeWidgetItem([self.type_text(row.get(header)) if header == "type" else cell_text(row.get(header)) for header, _key in COLUMNS]
                                   + ["" if length is None else quantities.metres(length)])   # empty where nothing of it is drawn with a length, or its plan has no scale
            item.setTextAlignment(LENGTH_COLUMN, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            item.setData(0, PositionList.ID_ROLE, pid)
            item.setToolTip(0, row["description"])
            item.setIcon(0, self.app.dirty_mark(False))   # its mark's room, before the column is sized to what it holds
            self.list.addTopLevelItem(item)
        if self.current_id is None:    # the position not written yet, where it can be seen
            item = QTreeWidgetItem([self.t("po_new_item")] + [""] * (len(COLUMNS) - 1))
            item.setData(0, PositionList.ID_ROLE, NEW_ROW)
            item.setIcon(0, self.app.dirty_mark(False))
            self.list.addTopLevelItem(item)
            item.setFirstColumnSpanned(True)   # its words across the row, not cut to the ID column's width
        if not self.fitted and self.rows:
            for column in range(len(COLUMNS) + 1):
                self.list.resizeColumnToContents(column)
            self.fitted = True
        target = select if select is not None else (self.current_id if self.current_id is not None else NEW_ROW)
        item = self.list.item_of(target)
        if item is not None:
            self.list.setCurrentItem(item)
        self.apply_search()
        self.loading = loading
        self.update_list_marker()
        self.list_card.refresh()

    def apply_search(self, _text=None):
        words = self.search.text().strip().lower().split()
        for item, pid in self.list.rows():
            row = self.row_of(pid) if pid != NEW_ROW else None
            text = " ".join(cell_text(v) for v in row.values()).lower() if row else ""
            if row:
                text += " " + self.type_text(row.get("type")).lower()    # a position is found by the type it is shown with too
            item.setHidden(bool(words) and pid != NEW_ROW and not all(word in text for word in words))

    def update_list_marker(self):
        """A dot at the left of the row being edited while it has unsaved changes, and the tab's own; every row carries a mark, dot or blank, so none moves sideways."""
        for item, pid in self.list.rows():
            mine = pid == self.current_id or (self.current_id is None and pid == NEW_ROW)
            item.setIcon(0, self.app.dirty_mark(mine and self.dirty))
        self.app.update_tab_marks()

    def on_list_change(self, item, _previous=None):
        if self.loading or item is None:
            return
        pid = item.data(0, PositionList.ID_ROLE)
        if pid == NEW_ROW or pid == self.current_id:
            return
        if not self.confirm_leave():
            self.fill_list()
            return
        self.load(pid)

    # -- the form ------------------------------------------------------------------------

    def form_values(self):
        return {
            "position": self.id_edit.text().strip(),
            "type": self.type_key(),
            "material": self.material_combo.currentText().strip(),
            STRENGTH: self.strength_combo.currentText().strip(),
            SECTION: self.section_combo.currentData() or "",
            "dimension": self.dimension_edit.text().strip(),
            "units": self.units_combo.currentText().strip(),
            MOISTURE: self.moisture_combo.currentData(),
            "description": self.description_edit.toPlainText().strip(),
        }

    def fill_form(self, values):
        self.loading = True
        self.id_edit.setText(values.get("position", "") or "")
        self.type_combo.setCurrentText(self.type_text(values.get("type", "")))
        self.material_combo.setCurrentText(values.get("material", "") or "")
        self.strength_combo.setCurrentText(values.get(STRENGTH, "") or "")
        code = values.get(SECTION, "") or ""
        self.section_combo.setCurrentIndex(self.index_of(self.section_combo, section.code_of(code) or code))
        self.dimension_edit.setText(values.get("dimension", "") or "")
        self.units_combo.setCurrentText(values.get("units", "") or "")
        self.refresh_dimension_mode()
        moisture = values.get(MOISTURE)
        self.moisture_combo.setCurrentIndex(0 if moisture is None else self.index_of(self.moisture_combo, moisture))
        self.description_edit.setPlainText(values.get("description", "") or "")
        self.loading = False
        self.update_notes()

    def on_section(self, _index):
        """The section type chosen: the dimension's fields follow it (a text that does not read as the new type stays the line it was, with its problem said), and the form has changed."""
        if self.loading:
            return
        self.refresh_dimension_mode()
        self.changed()

    def refresh_dimension_mode(self):
        """The dimension typed in boxes -- those of the section type chosen, filled from the text -- or as the line of text it is: boxes only for a type that has them, and where the text is empty or reads as that type's form (domains/section.py split_dimension). A text that does not -- a descriptive one, «100/200» under a plate -- is left alone, on its line, where it can be seen and mended. Decided here, when a position is loaded or its type changes, and not at every key: typing «100/» must not turn the boxes into a line."""
        code = section.code_of(self.section_combo.currentData() or "") or ""
        self.dim_by_fields = self.dimension_fields.set_code(code, self.dimension_edit.text())
        self.sync_dim_fields()
        self.captions["dimension"].setVisible(not self.dim_by_fields)
        self.dimension_edit.setVisible(not self.dim_by_fields)

    def sync_dim_fields(self):
        """`dim_fields` brought to the boxes the shared widget shows, in place."""
        self.dim_fields.clear()
        for n, (caption, edit) in enumerate(self.dimension_fields.edits, start=1):
            field = caption.property("field")
            self.dim_fields[f"layer{n}" if field == "layer" else field] = (caption, edit)

    def on_dimension_field(self, _text=None):
        """A box typed in, a form chosen, a layer added or taken away: the line the form reads is written from the boxes -- and only now, so that a dimension nobody touched is never rewritten (a «100 x 200» stays «100 x 200»)."""
        if not self.dim_by_fields:
            return
        self.sync_dim_fields()
        self.dimension_edit.setText(self.dimension_fields.text())
        self.changed()

    @staticmethod
    def index_of(combo, value):
        """The entry of `value` in a combo that is not typed into; a value it does not offer -- a section type or a moisture class an imported workbook held that the list does not carry -- is added and marked «(?)», never replaced by the first entry, and the one such entry an earlier row added is taken out first."""
        for i in reversed(range(combo.count())):
            if combo.itemText(i).endswith(" (?)") and combo.itemData(i) != value:
                combo.removeItem(i)
        index = combo.findData(value)
        if index < 0:
            combo.addItem(f"{value} (?)", value)
            index = combo.count() - 1
        return index

    def changed(self, *_args):
        if self.loading:
            return
        self.dirty = True
        self.update_notes()
        self.update_list_marker()

    def on_id_edited(self, text):
        """An ID typed over is the engineer's: the proposal no longer follows the type."""
        if self.current_id is None:
            self.proposed = self.proposed if text.strip() == self.proposed else ""
        self.changed()

    def on_type(self, _text):
        if self.loading:
            return
        if self.current_id is None:
            self.propose()
        self.changed()

    def on_floor(self, _text):
        if self.current_id is None:
            self.propose()
        self.changed()

    def type_text(self, type_):
        """A stored type as the form and the list show it: an STE type in the project's language, a free type as typed (positions_store.type_label, v0.116)."""
        return store.type_label(cell_text(type_), self.type_language)

    def type_key(self):
        """The stored type of what the type field holds: the STE key of a name shown (or typed) in any language, else the free type as typed (positions_store.type_key)."""
        return store.type_key(self.type_combo.currentText().strip(), self.type_language)

    def symbol_for(self, type_):
        """The symbol an id of this type starts with: the STE letter whose name it is, else the first letter of a position of that type (positions_store.symbol_for)."""
        return store.symbol_for(type_, self.rows)

    def type_for(self, symbol):
        """The type a position of `symbol` is: the STE name of that letter, else the type of a position whose id starts with it (positions_store.type_for)."""
        return store.type_for(symbol, self.rows)

    def propose(self):
        """A new position's ID, proposed from its type's symbol and its floor (positions_store.propose_id, the STE numbering) while the ID field still holds the last proposal -- one typed over is left alone."""
        if self.current_id is not None or self.id_edit.text().strip() not in ("", self.proposed):
            return
        symbol = self.symbol_for(self.type_key()) or self.draft_symbol
        if not symbol:
            return
        floor = self.floor_edit.text().strip() or None
        try:
            pid = store.propose_id(self.ids(), symbol, floor)
        except store.PositionsError:
            return
        self.proposed = pid
        loading, self.loading = self.loading, True
        self.id_edit.setText(pid)
        self.floor_edit.setPlaceholderText(floor_of(pid, symbol) or "")
        self.loading = loading

    def update_notes(self):
        values = self.form_values()
        self.show_note(self.id_note, *self.id_problem(values))
        self.show_note(self.type_note, self.t("po_type_missing") if not values["type"] else "", True)
        self.show_note(self.section_note, *self.section_problem(values))

    def show_note(self, label, text, blocking):
        label.setText(text)
        label.setStyleSheet("color: %s;" % (theme.colour("danger") if blocking else self.app.muted))
        label.setVisible(bool(text))

    def id_problem(self, values):
        """(sentence, blocking) of the ID: empty, not an ID, or taken by another position, ignoring case as Windows does."""
        pid = values["position"]
        if not pid:
            return self.t("po_refused_no_id"), True
        if not store.ID_PATTERN.match(pid):
            return self.t("po_id_invalid"), True
        for other in self.ids():
            if other.lower() == pid.lower() and other != self.current_id:
                return self.t("po_id_taken", existing=other), True
        return "", False

    def section_problem(self, values):
        """(sentence, flagged) of the section its type and dimension state -- read by domains/section.py, the export's own reader, and said in the window's language: what it reads as, or why it does not read. Flagged in the danger colour, and never blocking (v0.114): the position saves all the same, and the export writes it without a section, with a warning -- which the sentence says."""
        raw, dimension, units = values[SECTION], values["dimension"], values["units"]
        code = section.code_of(raw)
        later = "\n" + self.t("po_section_export")
        if code is None:
            return self.t("po_section_unknown", code=raw) + later, True
        if code == "":
            if not dimension:
                return "", False
            deduced = section.deduce(dimension, units)
            return (self.t("po_section_deduced", text=deduced["text"]) if deduced else self.t("po_section_text")), False
        if not dimension:
            return self.t("po_dim_missing", code=code) + later, True
        timber = section.kind_of(code) == "timber"
        allowed = [u for u in section.UNIT_FACTORS if u] if timber else ["mm"]
        if units.strip().lower() not in [""] + allowed:
            return self.t("po_units_bad", code=code, units=", ".join(allowed)) + later, True
        try:
            parsed = section.parse(code, dimension, units, where=values["position"] or "?")
        except validation.ValidationError:
            if timber:
                form = self.t(TIMBER_FORMS[code])
            else:
                form = self.t("po_form_steel", form=re.sub(r",? or ", " / ", section.STEEL_FORMS.get(code, "h")))
            return self.t("po_dim_bad", dimension=dimension, code=code, name=section.name(code, self.app.lang), form=form) + later, True
        return self.t("po_section_ok", text=parsed["text"]), False

    # -- the positions -------------------------------------------------------------------

    def load(self, pid):
        """The position `pid` into the form; the first where the project no longer has it."""
        row = self.row_of(pid)
        if row is None:
            self.load_first()
            return
        self.current_id, self.original = pid, dict(row)
        self.proposed, self.draft_symbol = "", ""
        self.dirty = False
        self.show_floor(False)
        self.fill_form(self.original)
        self.fill_list(select=pid)

    def load_first(self):
        ids = self.ids()
        if ids:
            self.load(ids[0])
        else:
            self.open_draft({}, dirty=False)

    def show_floor(self, on):
        self.floor_caption.setVisible(on)
        self.floor_edit.setVisible(on)

    def open_draft(self, values, floor=None, symbol=None, dirty=True):
        """A position not written yet in the form: `values` filled in, its ID proposed from its type's symbol -- or from `symbol` where the type names none -- and its floor."""
        self.current_id, self.original = None, None
        self.draft_symbol = symbol or ""
        self.proposed = ""
        blank = {header: "" for header in FIELDS}
        blank[MOISTURE] = None
        blank.update(values)
        blank["position"] = values.get("position", "")
        self.fill_form(blank)
        self.show_floor(True)
        self.loading = True
        self.floor_edit.setText(floor or "")
        self.floor_edit.setPlaceholderText("")
        self.loading = False
        self.propose()
        self.dirty = dirty
        self.draft_start = self.form_values()   # what an untouched draft holds: it is let go of rather than saved (autosave.py)
        self.update_notes()
        self.fill_list(select=NEW_ROW)

    def untouched_draft(self):
        """Whether the draft is a new position the engineer has not typed into: its ID and type are proposed, so it would save -- as a position nobody asked for."""
        return self.current_id is None and self.form_values() == getattr(self, "draft_start", None)

    def new_position(self, symbol=None, floor=None):
        """A new position in the form, this tab brought forward -- what the other tabs open through the window (`MainWindow.new_position`): the schemas tab's element panel, with no symbol. Without a symbol, the type of the position selected, so an ID is proposed at once. True where the draft was opened."""
        widget = getattr(self.app, "tab_widget", None)
        if widget is not None:
            widget.setCurrentWidget(self)
        if not self.confirm_leave():
            return False
        type_ = self.type_for(symbol) if symbol else self.type_key()
        self.open_draft({"type": type_}, floor=floor, symbol=symbol)
        self.id_edit.setFocus()
        return True

    def new(self):
        self.new_position()

    def duplicate(self):
        """A new position holding what the form holds, its ID proposed afresh on the same floor."""
        if not self.confirm_leave():
            return
        values = self.form_values()
        symbol = self.symbol_for(values["type"])
        floor = floor_of(values["position"], symbol) if symbol else None
        values["position"] = ""
        self.open_draft(values, floor=floor, symbol=symbol)

    def revert(self):
        if self.current_id is None:
            self.dirty = False
            self.load_first()
        else:
            self.load(self.current_id)

    def on_shown(self):
        """Brought to the front: the positions read again -- the plan tab may have written a blank one since -- the form kept where it holds unsaved changes."""
        self.read_positions()
        if self.dirty:
            self.fill_list()
        elif self.current_id is not None:
            self.load(self.current_id)
        else:
            self.fill_list()

    # -- writing -------------------------------------------------------------------------

    def fail(self, message):
        return autosave.refuse(self, self.t("po_refused_title"), message)

    def refusal_text(self, exc):
        """A refusal of positions_store in the window's language, from its code and detail (`schema.Refused`'s arrangement); a code with no sentence of its own is said with the module's English sentence inside the window's."""
        detail = {"file": store.FILE, "position": "", "existing": "", "value": "", "error": str(exc)}
        detail.update({key: value for key, value in getattr(exc, "detail", {}).items() if isinstance(value, str)})
        return self.t(REFUSALS.get(getattr(exc, "code", ""), "po_refused_other"), **detail)

    def write(self, change):
        """`change()` run on the project's positions, a refusal said in the window's language. Returns what `change` returns, or None where nothing was written."""
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        result = error = None
        try:
            result = change()
        except (store.PositionsError, OSError) as exc:
            error = exc
        finally:
            QApplication.restoreOverrideCursor()
        if error is not None:
            self.fail(self.refusal_text(error) if isinstance(error, store.PositionsError) else self.t("po_refused_other", error=error))
            return None
        return result

    def named_text(self, pid):
        words = {"plan": "po_ref_plan", "schema": "po_ref_schema"}
        names = [self.t(words[kind], id=name) for kind, name in references(pid)]
        return self.t("po_named", names=", ".join(names)) if names else ""

    def blocking(self, values):
        """The first reason the form cannot be written, checked before anything is: the ID and the type, and nothing else -- a section that does not read is said under its field and saved all the same (v0.114)."""
        problem, stop = self.id_problem(values)
        if stop:
            return problem
        if not values["type"]:
            return self.t("po_type_missing")
        return None

    def save(self):
        """Writes the form into the project's positions -- a new position, or the one the form holds -- and imports, as «Import données» does. True when written (or when there was nothing to write)."""
        values = self.form_values()
        new = self.current_id is None
        problem = self.blocking(values)
        if problem:
            return self.fail(problem)
        if not new and store.normalise(values) == store.normalise(self.original):
            self.dirty = False
            self.update_list_marker()
            self.app.set_status(self.t("po_unchanged"))
            return True
        old = self.current_id
        renaming = not new and values["position"] != old
        if renaming and not autosave.ask_rename(self, self.t("po_save"), self.t("po_rename", old=old, new=values["position"], named=self.named_text(old))):
            return False
        if new:
            result = self.write(lambda: (store.add(None, values), None))
        elif renaming:
            # renamed everywhere it is cited -- plans, checks, schemas, the .typ files -- by the renumbering's own table of one entry, then its other fields written (issue #9, ARCH-001)
            def rename():
                renumbering.apply(project.current(), renumbering.rename_preview(project.current(), old, values["position"]))
                return store.update(None, values["position"], values)[0], old
            result = self.write(rename)
        else:
            result = self.write(lambda: store.update(None, old, values))
        if result is None:
            return False
        row, renamed_from = result
        self.dirty = False
        self.read_positions()
        self.load(row["position"])
        done = self.t("po_renamed", old=renamed_from, new=row["position"]) if renamed_from else self.t("po_saved", id=row["position"])
        self.reimport(done)
        return True

    def delete(self):
        """«Supprimer»: the position selected taken out of the project, after a yes -- the question saying what names it, which will warn -- and the project imported. A position never written is simply discarded."""
        if self.current_id is None:
            self.dirty = False
            self.load_first()
            return True
        pid = self.current_id
        ids = self.ids()
        index = ids.index(pid) if pid in ids else 0
        # the plan's own path (issue #9): refused while a plan draws it or something cites it, unless its values are kept; the ones after it numbered again everywhere, once the engineer has seen where
        if renumber_dialog.ask(self, self.app, [pid]) is None:
            return False
        self.dirty = False
        self.read_positions()
        rest = self.ids()
        if rest:
            self.load(rest[min(index, len(rest) - 1)])
        else:
            self.open_draft({}, dirty=False)
        self.reimport(self.t("po_deleted", id=pid))
        return True

    # -- an old workbook -------------------------------------------------------------------

    def default_workbook(self):
        """Where «Importer depuis Excel…» opens: the project's own Positionen.xlsx where it is still there, else the newest one its archives hold (positions_store.migrate moved it there), else the project's folder."""
        here = project.current()
        book = store.workbook(here)
        if book.is_file():
            return book
        archived = sorted(here.archives_dir.glob(f"*{store.WORKBOOK}")) if here.archives_dir.is_dir() else []
        return archived[-1] if archived else here.root

    def choose_workbook(self):
        """The workbook to import, chosen in a file dialog -- None where none was. A method of its own, which a test replaces: a modal off-screen never comes back."""
        name, _filter = QFileDialog.getOpenFileName(self, self.t("po_import_title"), str(self.default_workbook()), self.t("po_import_filter"))
        return name or None

    def ask_import(self, file, count, existing):
        """«replace», «add» or None: what to do with the positions of `file` the project already has (`existing`, their ids). A method of its own, which a test replaces."""
        box = QMessageBox(QMessageBox.Icon.Question, self.t("po_import_title"),  # dialog-ok: a decision -- which positions to take over -- that waits for its answer
                          self.t("po_import_ask", file=file, count=count, existing=len(existing), ids=", ".join(existing[:8]) + (" …" if len(existing) > 8 else "")),
                          parent=self)
        replace = box.addButton(self.t("po_import_replace"), QMessageBox.ButtonRole.DestructiveRole)
        add = box.addButton(self.t("po_import_add"), QMessageBox.ButtonRole.AcceptRole)
        box.addButton(QMessageBox.StandardButton.Cancel)
        box.setDefaultButton(add)
        box.exec()
        clicked = box.clickedButton()
        return "replace" if clicked is replace else "add" if clicked is add else None

    def import_excel(self, file=None):
        """«Importer depuis Excel…»: the positions of a workbook laid out as Positionen.xlsx was (positions_store.import_workbook), merged into the project's -- the ones it lacks added, and where it has some of them already, those written over or left as they are, as the engineer answers. What the import left out or completed is said; the project is then imported as after every write. True where something was written."""
        if getattr(self.app, "read_only", False):
            self.app.refuse_read_only()
            return False
        if not self.confirm_leave():
            return False
        file = file or self.choose_workbook()
        if not file:
            return False
        from pathlib import Path
        name = Path(file).name
        try:
            imported, notes = store.import_workbook(None, file)
        except store.PositionsError as exc:
            return self.fail(self.t("po_import_failed", file=name, error=exc))
        if notes:
            for note in notes:   # each a notice of its own, in the window's words whatever language it is switched to (v0.117)
                notifications.report_note(note, notifications.WARNING, source="positions import")
        if not imported:
            self.app.set_status(self.t("po_import_nothing", file=name))
            return False
        have = {pid.lower() for pid in self.ids()}
        existing = [row["position"] for row in imported if row["position"].lower() in have]
        replace = False
        if existing:
            answer = self.ask_import(name, len(imported), existing)
            if answer is None:
                return False
            replace = answer == "replace"
        merged, added, replaced = store.merge(self.rows, imported, replace=replace)
        if not added and not replaced:
            self.app.set_status(self.t("po_import_done", file=name, added=0, replaced=0))
            return False
        if self.write(lambda: store.write(None, merged)) is None:
            return False
        self.dirty = False
        self.read_positions()
        self.load(self.current_id if self.current_id in self.ids() else (added or replaced or self.ids())[0])
        self.reimport(self.t("po_import_done", file=name, added=len(added), replaced=len(replaced)))
        return True

    def reimport(self, done):
        """The positions written, imported as «Import données» imports them -- the window's own export, whose failure it shows with the exporter's message, the position staying written -- so data/ and every tab follow. While another export runs, the status line says to import afterwards."""
        self.app.set_status(done)
        if getattr(self.app, "process", None) is not None:
            self.app.set_status(self.t("po_import_later", done=done))
            return
        self.app.reexport(light=True)   # the window is not built again after it: the tab in front is, the others when they are shown (MainWindow.refresh_lightly, v0.117)

    # -- surviving a rebuild -------------------------------------------------------------

    def view_state(self):
        return {
            "current_id": self.current_id,
            "dirty": self.dirty,
            "draft": self.form_values() if self.dirty or self.current_id is None else None,
            "floor": self.floor_edit.text(),
            "symbol": self.draft_symbol,
            "proposed": self.proposed,
            "search": self.search.text(),
            "splitter": self.splitter.sizes(),
            "columns": [self.list.columnWidth(i) for i in range(len(COLUMNS))],
        }

    def restore(self, state):
        self.read_positions()
        if state:
            self.loading = True
            self.search.setText(state.get("search", ""))
            self.loading = False
            if state.get("columns"):
                for i, width in enumerate(state["columns"]):
                    self.list.setColumnWidth(i, width)
                self.fitted = True
            current, draft = state.get("current_id"), state.get("draft")
            if current is not None and self.row_of(current) is not None:
                self.load(current)
                if state.get("dirty") and draft:
                    self.fill_form(draft)
                    self.dirty = True
                    self.update_list_marker()
            elif current is None and draft:
                self.open_draft(draft, floor=state.get("floor"), symbol=state.get("symbol"), dirty=state.get("dirty", False))
                self.proposed = state.get("proposed", "")
            else:
                self.load_first()
            if state.get("splitter"):
                self.splitter.setSizes(state["splitter"])
        else:
            self.splitter.setSizes([6000, 4000])
            self.load_first()
