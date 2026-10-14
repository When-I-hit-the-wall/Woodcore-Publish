"""«Changer de template de fond…»: a document of the project compared with another content template, section by section, and what the engineer keeps, takes or drops written back (the engineer's decision of 06.10.2026, calc/content_switch.py; opened from the «Structure du document» tab, structure_tab.py).

A **content template** («template de fond», «Inhaltsvorlage») is the sections, objects and texts of a document; it is chosen when a project is made, and switching it afterwards is rare and must be possible without losing a word the engineer wrote. So the dialog is a comparison and never a copy:

* at the top, the content templates this document may take (content_switch.templates_for: every place's, in the document's language), the builtin standard one chosen at first;
* a tree of four columns -- «Section / objet» | «Ce document» | «Template» | «Choix» --: the chapters and sections of the comparison, each with what each side holds said by a mark **and** a word (`=` the same, `≠` different, `●` there, `○` not there) in the theme's colours -- never a colour alone --, and under each section its objects, greyed, their status only: they say *where* two versions part, and nothing is chosen object by object;
* each section's choice in a combo of what its status allows (`node.choices`: «Garder le mien», «Prendre celui du template», «Retirer», «Ne pas ajouter»), at its default (`node.default`), which keeps the document as it stands and adds what only the template has;
* «Afficher seulement les différences», a line counting the sections by status, and a banner that says a refusal in the window's words by its code (`cs_why_<code>`, every code of content_switch.CODES held by a test) -- never the English sentence;
* «Appliquer» asks first, listing what is replaced, removed and added and saying that nothing is erased -- what is replaced or removed goes into `Sections/archives/` --, then runs content_switch.apply; «Annuler» writes nothing.

A convention or a base whose headings are still written with offsets (`legacy_headings` on the document's side) is offered the conversion the tab offers (`convert`, the tab's own «Écrire les titres à leur niveau réel…», structure.make_absolute), then compared again. A project held read-only compares and writes nothing: «Appliquer» is closed, its reason in its tooltip.

Every question is a method (`ask_confirm`), so that a test answers it without a modal: a modal off-screen never comes back. No colour is written here as a hex: theme.colour names a token.
"""

import collections

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor, QFont
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QHBoxLayout, QHeaderView, QLabel, QMessageBox, QPushButton, QTreeWidget, QTreeWidgetItem, QVBoxLayout,
)

import cards
import content_switch
import doc_templates
import documents
import settings_dialog
import structure_words
import theme

LANGUAGES = ("fr", "de", "en")
COLUMNS = ("node", "document", "template", "choice")
NODE, DOCUMENT, TEMPLATE, CHOICE = range(4)
ID_ROLE = Qt.ItemDataRole.UserRole
# What each side of a node says, by its status: (the document's column, the template's column), each a key of STRINGS -- a mark and a word.
SIDES = {
    "same": ("cs_side_same", "cs_side_same"),
    "differs": ("cs_side_differs", "cs_side_differs"),
    "document_only": ("cs_side_present", "cs_side_absent"),
    "template_only": ("cs_side_absent", "cs_side_present"),
}
# The colour token of each word: a section the same muted, one that differs in the orange of a value written over, one on one side alone in the accent.
INKS = {"cs_side_same": "muted", "cs_side_differs": "override", "cs_side_present": "accent", "cs_side_absent": "muted"}

STRINGS = {
    "fr": {
        "cs_title": "Changer de template de fond — {document}",
        "cs_intro": "Un template de fond porte les sections, objets et textes d'un document. « {document} » est comparé ici à un autre template de fond, section par section : gardez les vôtres, prenez celles du template ou retirez-les. Rien n'est effacé : ce qui est remplacé ou retiré est archivé dans Sections/archives/.",
        "cs_template_label": "Template de fond :",
        "cs_col_node": "Section / objet",
        "cs_col_document": "Ce document",
        "cs_col_template": "Template",
        "cs_col_choice": "Choix",
        "cs_side_same": "= identique",
        "cs_side_differs": "≠ différente",
        "cs_side_present": "● présente",
        "cs_side_absent": "○ absente",
        "cs_choice_keep": "Garder le mien",
        "cs_choice_take": "Prendre celui du template",
        "cs_choice_drop": "Retirer",
        "cs_choice_skip": "Ne pas ajouter",
        "cs_only_differences": "Afficher seulement les différences",
        "cs_summary": "{same} identique(s) · {differs} différente(s) · {document_only} seulement dans ce document · {template_only} seulement dans le template",
        "cs_apply": "Appliquer",
        "cs_apply_tip": "Écrit les choix dans ce document, après confirmation. Ce qui est remplacé ou retiré est archivé, jamais effacé.",
        "cs_cancel": "Annuler",
        "cs_convert": "Écrire les titres à leur niveau réel…",
        "cs_no_template": "Aucun template de fond n'existe pour ce document dans sa langue.",
        "cs_read_only": "Le projet est ouvert en lecture seule : la comparaison est montrée, rien n'est écrit.",
        "cs_confirm_intro": "Appliquer le template de fond « {template} » à « {document} » ?",
        "cs_confirm_replaced": "Remplacées par celles du template (les vôtres archivées) : {titles}",
        "cs_confirm_dropped": "Retirées du document (archivées) : {titles}",
        "cs_confirm_added": "Ajoutées depuis le template : {titles}",
        "cs_confirm_nothing": "Aucune section n'est remplacée, retirée ni ajoutée : l'ordre et les chapitres suivent le template.",
        "cs_confirm_archive": "Rien n'est effacé : ce qui est remplacé ou retiré est déplacé dans Sections/archives/.",
        "cs_why_bad_mode": "« {mode} » n'est pas un document : la convention d'utilisation (cu), la base de projet (bp) ou le rapport de statique (rs).",
        "cs_why_no_such_document": "Le projet n'a pas ce document : seul un projet en trois documents change de template de fond.",
        "cs_why_bad_language": "« {language} » n'est pas une langue de Woodcore : fr, de ou en.",
        "cs_why_no_such_template": "Aucun template de fond ne s'appelle « {name} ».",
        "cs_why_template_unusable": "Le template de fond {ref} ne peut pas servir : {error}",
        "cs_why_mode_mismatch": "Le template de fond {ref} est celui d'un autre document.",
        "cs_why_language_missing": "Le template de fond {ref} existe en {languages} et pas en {language}, la langue de ce document.",
        "cs_why_legacy_headings": "Les titres de ce document sont écrits avec les décalages d'une version précédente : écrivez-les d'abord à leur niveau réel, puis comparez.",
        "cs_why_legacy_headings_template": "Les titres de ce template de fond sont écrits avec les décalages d'une version précédente : il ne peut pas être comparé. Choisissez-en un autre.",
        "cs_why_structure_unreadable": "La structure de ce document (structure.json) ne peut pas être lue : {error}",
        "cs_why_entry_unreadable": "Le fichier d'entrée {file} de ce document ne peut pas être lu, ou ses balises non plus.",
        "cs_why_section_unreadable": "Le fichier de section {file} ne peut pas être lu.",
        "cs_why_kind_clash": "« {id} » est un chapitre d'un côté et une section de l'autre : les deux ne peuvent pas être comparés.",
        "cs_why_duplicate_section": "Le rapport inclut deux sections nommées « {name} » une fois leurs numéros ôtés : renommez l'une d'elles.",
        "cs_why_unknown_node": "« {id} » n'est ni une section ni un chapitre de la comparaison.",
        "cs_why_bad_choice": "« {choice} » n'est pas un choix possible pour « {id} ».",
        "cs_why_wrong_comparison": "La comparaison est celle d'un autre document : elle a été refaite.",
        "cs_why_changed_meanwhile": "Le fichier {file} a changé depuis la comparaison : rien n'a été écrit, et la comparaison a été refaite. Vérifiez vos choix.",
        "cs_why_invalid_result": "Ce que ces choix donneraient n'est pas une structure valable : {error}",
        "cs_why_too_deep": "Ce que ces choix donneraient descend trop profond ({depth} niveaux).",
        "cs_why_write_failed": "Le disque a refusé l'écriture : tout a été remis comme avant. {error}",
    },
    "de": {
        "cs_title": "Inhaltsvorlage wechseln — {document}",
        "cs_intro": "Eine Inhaltsvorlage trägt die Abschnitte, Objekte und Texte eines Dokuments. «{document}» wird hier Abschnitt für Abschnitt mit einer anderen Inhaltsvorlage verglichen: die eigenen behalten, die der Vorlage übernehmen oder sie entfernen. Nichts wird gelöscht: was ersetzt oder entfernt wird, kommt in Sections/archives/.",
        "cs_template_label": "Inhaltsvorlage:",
        "cs_col_node": "Abschnitt / Objekt",
        "cs_col_document": "Dieses Dokument",
        "cs_col_template": "Vorlage",
        "cs_col_choice": "Wahl",
        "cs_side_same": "= gleich",
        "cs_side_differs": "≠ verschieden",
        "cs_side_present": "● vorhanden",
        "cs_side_absent": "○ fehlt",
        "cs_choice_keep": "Meinen behalten",
        "cs_choice_take": "Den der Vorlage übernehmen",
        "cs_choice_drop": "Entfernen",
        "cs_choice_skip": "Nicht hinzufügen",
        "cs_only_differences": "Nur die Unterschiede zeigen",
        "cs_summary": "{same} gleich · {differs} verschieden · {document_only} nur in diesem Dokument · {template_only} nur in der Vorlage",
        "cs_apply": "Anwenden",
        "cs_apply_tip": "Schreibt die Wahl in dieses Dokument, nach einer Bestätigung. Was ersetzt oder entfernt wird, wird archiviert, nie gelöscht.",
        "cs_cancel": "Abbrechen",
        "cs_convert": "Titel auf ihrer wirklichen Ebene schreiben…",
        "cs_no_template": "Für dieses Dokument gibt es in seiner Sprache keine Inhaltsvorlage.",
        "cs_read_only": "Das Projekt ist schreibgeschützt geöffnet: der Vergleich wird gezeigt, geschrieben wird nichts.",
        "cs_confirm_intro": "Die Inhaltsvorlage «{template}» auf «{document}» anwenden?",
        "cs_confirm_replaced": "Durch die der Vorlage ersetzt (die eigenen archiviert): {titles}",
        "cs_confirm_dropped": "Aus dem Dokument entfernt (archiviert): {titles}",
        "cs_confirm_added": "Aus der Vorlage hinzugefügt: {titles}",
        "cs_confirm_nothing": "Kein Abschnitt wird ersetzt, entfernt oder hinzugefügt: die Reihenfolge und die Kapitel folgen der Vorlage.",
        "cs_confirm_archive": "Nichts wird gelöscht: was ersetzt oder entfernt wird, wird nach Sections/archives/ verschoben.",
        "cs_why_bad_mode": "«{mode}» ist kein Dokument: die Nutzungsvereinbarung (cu), die Projektbasis (bp) oder der statische Bericht (rs).",
        "cs_why_no_such_document": "Das Projekt hat dieses Dokument nicht: nur ein Projekt in drei Dokumenten wechselt die Inhaltsvorlage.",
        "cs_why_bad_language": "«{language}» ist keine Sprache von Woodcore: fr, de oder en.",
        "cs_why_no_such_template": "Keine Inhaltsvorlage heisst «{name}».",
        "cs_why_template_unusable": "Die Inhaltsvorlage {ref} ist unbrauchbar: {error}",
        "cs_why_mode_mismatch": "Die Inhaltsvorlage {ref} gehört zu einem anderen Dokument.",
        "cs_why_language_missing": "Die Inhaltsvorlage {ref} gibt es auf {languages} und nicht auf {language}, der Sprache dieses Dokuments.",
        "cs_why_legacy_headings": "Die Titel dieses Dokuments sind mit den Versätzen einer früheren Version geschrieben: sie zuerst auf ihrer wirklichen Ebene schreiben, dann vergleichen.",
        "cs_why_legacy_headings_template": "Die Titel dieser Inhaltsvorlage sind mit den Versätzen einer früheren Version geschrieben: sie kann nicht verglichen werden. Eine andere wählen.",
        "cs_why_structure_unreadable": "Die Struktur dieses Dokuments (structure.json) kann nicht gelesen werden: {error}",
        "cs_why_entry_unreadable": "Die Einstiegsdatei {file} dieses Dokuments kann nicht gelesen werden, oder ihre Markierungen nicht.",
        "cs_why_section_unreadable": "Die Abschnittsdatei {file} kann nicht gelesen werden.",
        "cs_why_kind_clash": "«{id}» ist auf der einen Seite ein Kapitel und auf der anderen ein Abschnitt: die beiden können nicht verglichen werden.",
        "cs_why_duplicate_section": "Der Bericht bindet zwei Abschnitte namens «{name}» ein, sobald ihre Nummern weg sind: einen davon umbenennen.",
        "cs_why_unknown_node": "«{id}» ist weder ein Abschnitt noch ein Kapitel des Vergleichs.",
        "cs_why_bad_choice": "«{choice}» ist für «{id}» keine mögliche Wahl.",
        "cs_why_wrong_comparison": "Der Vergleich gehört zu einem anderen Dokument: er wurde neu gemacht.",
        "cs_why_changed_meanwhile": "Die Datei {file} hat sich seit dem Vergleich geändert: nichts wurde geschrieben, und der Vergleich wurde neu gemacht. Die Wahl prüfen.",
        "cs_why_invalid_result": "Was diese Wahl ergäbe, ist keine gültige Struktur: {error}",
        "cs_why_too_deep": "Was diese Wahl ergäbe, geht zu tief ({depth} Ebenen).",
        "cs_why_write_failed": "Das Laufwerk hat das Schreiben verweigert: alles wurde wiederhergestellt. {error}",
    },
    "en": {
        "cs_title": "Switch content template — {document}",
        "cs_intro": "A content template holds the sections, objects and texts of a document. «{document}» is compared here with another content template, section by section: keep your own, take the template's or drop them. Nothing is erased: what is replaced or dropped is archived in Sections/archives/.",
        "cs_template_label": "Content template:",
        "cs_col_node": "Section / object",
        "cs_col_document": "This document",
        "cs_col_template": "Template",
        "cs_col_choice": "Choice",
        "cs_side_same": "= the same",
        "cs_side_differs": "≠ different",
        "cs_side_present": "● there",
        "cs_side_absent": "○ missing",
        "cs_choice_keep": "Keep mine",
        "cs_choice_take": "Take the template's",
        "cs_choice_drop": "Drop",
        "cs_choice_skip": "Do not add",
        "cs_only_differences": "Show only the differences",
        "cs_summary": "{same} the same · {differs} different · {document_only} only in this document · {template_only} only in the template",
        "cs_apply": "Apply",
        "cs_apply_tip": "Writes the choices into this document, once confirmed. What is replaced or dropped is archived, never erased.",
        "cs_cancel": "Cancel",
        "cs_convert": "Write the headings at their real level…",
        "cs_no_template": "No content template exists for this document in its language.",
        "cs_read_only": "The project is open read-only: the comparison is shown and nothing is written.",
        "cs_confirm_intro": "Apply the content template «{template}» to «{document}»?",
        "cs_confirm_replaced": "Replaced by the template's (yours archived): {titles}",
        "cs_confirm_dropped": "Dropped from the document (archived): {titles}",
        "cs_confirm_added": "Added from the template: {titles}",
        "cs_confirm_nothing": "No section is replaced, dropped or added: the order and the chapters follow the template.",
        "cs_confirm_archive": "Nothing is erased: what is replaced or dropped is moved into Sections/archives/.",
        "cs_why_bad_mode": "«{mode}» is not a document: the service criteria agreement (cu), the basis of design (bp) or the statical report (rs).",
        "cs_why_no_such_document": "The project has no such document: only a project in three documents switches its content template.",
        "cs_why_bad_language": "«{language}» is not a language of Woodcore: fr, de or en.",
        "cs_why_no_such_template": "No content template is called «{name}».",
        "cs_why_template_unusable": "The content template {ref} cannot be used: {error}",
        "cs_why_mode_mismatch": "The content template {ref} belongs to another document.",
        "cs_why_language_missing": "The content template {ref} exists in {languages} and not in {language}, the language of this document.",
        "cs_why_legacy_headings": "The headings of this document are written with the offsets of an earlier version: write them at their real level first, then compare.",
        "cs_why_legacy_headings_template": "The headings of this content template are written with the offsets of an earlier version: it cannot be compared. Choose another one.",
        "cs_why_structure_unreadable": "The structure of this document (structure.json) cannot be read: {error}",
        "cs_why_entry_unreadable": "The entry file {file} of this document cannot be read, or its tags cannot.",
        "cs_why_section_unreadable": "The section file {file} cannot be read.",
        "cs_why_kind_clash": "«{id}» is a chapter on one side and a section on the other: the two cannot be compared.",
        "cs_why_duplicate_section": "The report includes two sections called «{name}» once their numbers are taken off: rename one of them.",
        "cs_why_unknown_node": "«{id}» is neither a section nor a chapter of the comparison.",
        "cs_why_bad_choice": "«{choice}» is not a choice «{id}» may be given.",
        "cs_why_wrong_comparison": "The comparison was of another document: it has been made again.",
        "cs_why_changed_meanwhile": "The file {file} changed since the comparison: nothing was written, and the comparison has been made again. Check your choices.",
        "cs_why_invalid_result": "What these choices would make is no valid structure: {error}",
        "cs_why_too_deep": "What these choices would make goes too deep ({depth} levels).",
        "cs_why_write_failed": "The disk refused the write: everything has been put back as it was. {error}",
    },
}

for _lang in LANGUAGES[1:]:
    assert set(STRINGS[_lang]) == set(STRINGS["fr"]), f"content_switch_dialog.STRINGS[{_lang!r}] does not carry the same keys as French"

# French puts a narrow no-break space before its colons and inside its guillemets, as structure_words does for the tab.
STRINGS["fr"] = {key: structure_words._french(value) for key, value in STRINGS["fr"].items()}


def t(lang, key, **values):
    text = STRINGS[lang if lang in STRINGS else "fr"][key]
    return text.format(**values) if values else text


def error_key(exc):
    """The key of the sentence that says a ContentSwitchError: `cs_why_<code>`, the template's side of `legacy_headings` a sentence of its own; None for a code this table does not know."""
    code = getattr(exc, "code", "")
    if code == "legacy_headings" and (getattr(exc, "values", None) or {}).get("side") == "template":
        return "cs_why_legacy_headings_template"
    key = f"cs_why_{code}"
    return key if code and key in STRINGS["en"] else None


def error_text(lang, exc):
    """A ContentSwitchError in `lang`, by its code, with the values it states -- a list written as its items, a document's code as its name, a value it has none of left empty; the English sentence itself only where the code is none this table knows: a window never says nothing."""
    key = error_key(exc)
    if key is None:
        return str(exc)
    values = collections.defaultdict(str, error=str(exc))
    for name, value in (getattr(exc, "values", None) or {}).items():
        if isinstance(value, (list, tuple)):
            value = ", ".join(map(str, value))
        elif name == "mode" and value in documents.MODE_NAMES["en"]:
            value = documents.mode_name(value, lang)
        values[name] = value
    return t(lang, key).format_map(values)


class ContentSwitchDialog(QDialog):
    """The comparison of document `mode` of project `here` with a content template, the choices of each section, and «Appliquer». `result_` is content_switch.apply's Result once applied, None before. `convert` is what converts a document whose headings are written with offsets (the tab's own, which asks first and returns whether it converted). `settings` are Woodcore's preferences (usersettings.py), read where not given."""

    def __init__(self, parent, lang, here, mode, read_only=False, settings=None, convert=None, template=None):
        super().__init__(parent)
        theme.ensure()
        self.lang = lang if lang in LANGUAGES else "fr"
        self.here = here
        self.mode = mode
        self.read_only = bool(read_only)
        self.settings = settings
        self.convert = convert
        self.comparison = None
        self.result_ = None
        self.failure = None
        self.found = {}             # ref -> the DocTemplate listed
        self.items = {}             # node id -> its row
        self.choice_combos = {}     # node id -> the combo of its choices, where it has more than one
        self.document_name = documents.mode_name(mode, self.lang)
        self.setWindowTitle(self.t("cs_title", document=self.document_name))
        self.resize(980, 640)
        layout = QVBoxLayout(self)
        layout.addWidget(cards.note(self.t("cs_intro", document=self.document_name)))
        row = QHBoxLayout()
        row.addWidget(QLabel(self.t("cs_template_label")))
        self.combo = QComboBox()
        row.addWidget(self.combo, 1)
        layout.addLayout(row)
        self.banner = QLabel()
        self.banner.setWordWrap(True)
        self.banner.setTextFormat(Qt.TextFormat.PlainText)
        self.banner.setProperty("callout", "danger")
        self.banner.setVisible(False)
        layout.addWidget(self.banner)
        self.convert_button = QPushButton(self.t("cs_convert"))
        self.convert_button.clicked.connect(lambda _checked=False: self.on_convert())
        self.convert_button.setVisible(False)
        layout.addWidget(self.convert_button, 0, Qt.AlignmentFlag.AlignLeft)
        self.only_differences = QCheckBox(self.t("cs_only_differences"))
        self.only_differences.toggled.connect(lambda _on: self.apply_filter())
        layout.addWidget(self.only_differences)
        self.tree = QTreeWidget()
        self.tree.setColumnCount(len(COLUMNS))
        self.tree.setHeaderLabels([self.t("cs_col_" + key) for key in COLUMNS])
        self.tree.setUniformRowHeights(False)
        header = self.tree.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(NODE, QHeaderView.ResizeMode.Stretch)
        for column in (DOCUMENT, TEMPLATE, CHOICE):
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.tree, 1)
        self.summary = QLabel()
        self.summary.setObjectName("meta")
        self.summary.setWordWrap(True)
        layout.addWidget(self.summary)
        buttons = QHBoxLayout()
        buttons.addStretch(1)
        self.apply_button = QPushButton(self.t("cs_apply"))
        self.apply_button.setProperty("primary", True)
        self.apply_button.clicked.connect(lambda _checked=False: self.apply())
        self.cancel_button = QPushButton(self.t("cs_cancel"))
        self.cancel_button.clicked.connect(self.reject)
        buttons.addWidget(self.apply_button)
        buttons.addWidget(self.cancel_button)
        layout.addLayout(buttons)
        self.fill_templates(template)
        self.combo.currentIndexChanged.connect(lambda _index: self.compare())
        self.compare()

    def t(self, key, **values):
        return t(self.lang, key, **values)

    # --- the templates ------------------------------------------------------------------------

    def fill_templates(self, select=None):
        """The content templates this document may take, each named in the window's language -- its place after a name that is not a builtin one's, its description as its tooltip --, `select` (a ref) chosen, else the builtin standard one, else the first."""
        try:
            found = [template for template in content_switch.templates_for(self.here, self.mode, self.settings) if not template.error]
        except content_switch.ContentSwitchError as exc:
            found = []
            self.failure = exc
        self.found = {template.ref: template for template in found}
        self.combo.blockSignals(True)
        self.combo.clear()
        for template in found:
            name = template.name(self.lang)
            if template.place != "builtin":
                name = f"{name} — {settings_dialog.place_label(self.lang, template.place)}"
            self.combo.addItem(name, template.ref)
            self.combo.setItemData(self.combo.count() - 1, template.description(self.lang), Qt.ItemDataRole.ToolTipRole)
        wanted = select if select in self.found else doc_templates.default_ref(self.mode)
        self.combo.setCurrentIndex(max(0, self.combo.findData(wanted)))
        self.combo.blockSignals(False)

    def chosen_template(self):
        return self.found.get(self.combo.currentData())

    def choose_template(self, ref):
        """The template `ref` chosen, and the comparison made again. Returns whether it is listed."""
        index = self.combo.findData(ref)
        if index < 0:
            return False
        if index == self.combo.currentIndex():
            self.compare()
        else:
            self.combo.setCurrentIndex(index)
        return True

    # --- the comparison -----------------------------------------------------------------------

    def compare(self):
        """The document compared with the template chosen (content_switch.compare) and the tree filled -- or, where it is refused, the tree emptied and the refusal said in the banner. Returns the Comparison, or None."""
        template = self.chosen_template()
        self.comparison = None
        error = self.failure
        self.failure = None
        if template is None:
            self.fill_tree()
            self.say(self.t("cs_no_template") if error is None else error_text(self.lang, error))
            return None
        try:
            self.comparison = content_switch.compare(self.here, self.mode, template=template, settings=self.settings)
        except content_switch.ContentSwitchError as exc:
            self.fill_tree()
            self.say(error_text(self.lang, exc), exc)
            return None
        self.say("")
        self.fill_tree()
        return self.comparison

    def say(self, text, exc=None):
        """The banner: `text`, or hidden where it is empty -- with the conversion offered where the refusal is the document's headings written with offsets."""
        self.banner.setText(text)
        self.banner.setVisible(bool(text))
        legacy = exc is not None and getattr(exc, "code", "") == "legacy_headings" and (exc.values or {}).get("side", "document") != "template"
        self.convert_button.setVisible(legacy and self.convert is not None and not self.read_only)
        self.update_apply()

    def on_convert(self):
        """The document's headings written at their real level -- the tab's own conversion, which asks first -- and the comparison made again. Returns whether it converted."""
        if self.convert is None or not self.convert():
            return False
        self.compare()
        return True

    def fill_tree(self):
        """The comparison's nodes in the tree: a chapter bold with its sections under it, a section with its objects under it greyed, each side's word with its mark and its colour, and a section's choice in a combo of what its status allows, at its default."""
        self.tree.clear()
        self.items, self.choice_combos = {}, {}
        if self.comparison is not None:
            for node in self.comparison.nodes:
                self.add_node(node, None)
        self.tree.expandAll()
        self.apply_filter()
        self.update_summary()

    def side_word(self, item, column, key):
        item.setText(column, self.t(key))
        item.setForeground(column, QBrush(QColor(theme.colour(INKS[key]))))
        item.setData(column, ID_ROLE, key)

    def add_node(self, node, parent):
        title = node.title_document or node.title_template or node.id
        item = QTreeWidgetItem([title, "", "", ""])
        item.setData(NODE, ID_ROLE, node.id)
        item.setData(CHOICE, ID_ROLE, node.status)
        doc_key, tpl_key = SIDES[node.status]
        self.side_word(item, DOCUMENT, doc_key)
        self.side_word(item, TEMPLATE, tpl_key)
        tips = [part for part in (node.file_document, node.file_template) if part]
        if node.title_document and node.title_template and node.title_document != node.title_template:
            tips.insert(0, f"{node.title_document}  |  {node.title_template}")
        item.setToolTip(NODE, "\n".join(dict.fromkeys(tips)))
        if node.kind == "group":
            font = QFont(item.font(NODE))
            font.setBold(True)
            item.setFont(NODE, font)
        if parent is None:
            self.tree.addTopLevelItem(item)
        else:
            parent.addChild(item)
        self.items[node.id] = item
        choices = list(node.choices)
        if len(choices) > 1:
            combo = QComboBox()
            for choice in choices:
                combo.addItem(self.t("cs_choice_" + choice), choice)
            combo.setCurrentIndex(max(0, combo.findData(node.default)))
            combo.setEnabled(not self.read_only)
            self.tree.setItemWidget(item, CHOICE, combo)
            self.choice_combos[node.id] = combo
        else:
            item.setText(CHOICE, self.t("cs_choice_" + choices[0]))
            item.setForeground(CHOICE, QBrush(QColor(theme.colour("muted"))))
        if node.kind == "group":
            for child in node.children:
                self.add_node(child, item)
        else:
            muted = QBrush(QColor(theme.colour("muted")))
            kinds = structure_words.STRINGS[self.lang]
            for obj in node.children:
                label = obj.title_document or obj.title_template or obj.id
                kind = kinds.get("st_kind_" + obj.type, obj.type)
                row = QTreeWidgetItem([f"{label}  ({kind})", "", "", ""])
                row.setFlags(Qt.ItemFlag.ItemIsEnabled)
                row.setForeground(NODE, muted)
                row.setData(CHOICE, ID_ROLE, obj.status)
                doc_key, tpl_key = SIDES[obj.status]
                self.side_word(row, DOCUMENT, doc_key)
                self.side_word(row, TEMPLATE, tpl_key)
                item.addChild(row)

    def apply_filter(self):
        """«Afficher seulement les différences»: every row whose status is `same` hidden, and a chapter with nothing left to show under it."""
        only = self.only_differences.isChecked()

        def visit(item):
            visible_child = False
            for index in range(item.childCount()):
                visible_child = visit(item.child(index)) or visible_child
            show = not only or item.data(CHOICE, ID_ROLE) != "same" or visible_child
            item.setHidden(not show)
            return show

        for index in range(self.tree.topLevelItemCount()):
            visit(self.tree.topLevelItem(index))

    def update_summary(self):
        if self.comparison is None:
            self.summary.setText("")
            return
        self.summary.setText(self.t("cs_summary", **self.comparison.counts()))

    def update_apply(self):
        """«Appliquer» open where there is a comparison and the project may be written, closed with its reason otherwise."""
        ok = self.comparison is not None and not self.read_only
        self.apply_button.setEnabled(ok)
        self.apply_button.setToolTip(self.t("cs_read_only") if self.read_only else self.t("cs_apply_tip") if ok else self.banner.text())

    # --- the choices, and applying them -----------------------------------------------------------

    def choices(self):
        """{node id: choice} of every node whose choice is a combo -- each other node takes its default (content_switch.resolve_choices)."""
        return {node_id: combo.currentData() for node_id, combo in self.choice_combos.items()}

    def set_choice(self, node_id, choice):
        """`node_id`'s choice set to `choice`, as a click on its combo does. Returns whether its combo offers it."""
        combo = self.choice_combos.get(node_id)
        index = combo.findData(choice) if combo is not None else -1
        if index < 0:
            return False
        combo.setCurrentIndex(index)
        return True

    def visible_rows(self):
        """{node id: (document word, template word, choice)} of every node row shown -- what a reader sees, for the tests."""
        out = {}
        for node_id, item in self.items.items():
            if item.isHidden():
                continue
            combo = self.choice_combos.get(node_id)
            out[node_id] = (item.text(DOCUMENT), item.text(TEMPLATE), combo.currentData() if combo is not None else item.text(CHOICE))
        return out

    def plan(self):
        """(replaced, dropped, added): the titles of the sections a switch with the choices made would replace by the template's, take out of the document and add from the template."""
        chosen = content_switch.resolve_choices(self.comparison, self.choices())
        replaced, dropped, added = [], [], []
        for node in self.comparison.sections():
            choice = chosen[node.id]
            title = node.title_document or node.title_template or node.id
            if choice == "take" and node.status == "differs":
                replaced.append(title)
            elif choice == "take" and node.status == "template_only":
                added.append(title)
            elif choice == "drop":
                dropped.append(title)
        return replaced, dropped, added

    def confirm_text(self):
        replaced, dropped, added = self.plan()
        template = self.chosen_template()
        lines = [self.t("cs_confirm_intro", template=template.name(self.lang) if template else "", document=self.document_name), ""]
        for key, titles in (("cs_confirm_replaced", replaced), ("cs_confirm_dropped", dropped), ("cs_confirm_added", added)):
            if titles:
                lines.append(self.t(key, titles=", ".join(titles)))
        if not (replaced or dropped or added):
            lines.append(self.t("cs_confirm_nothing"))
        lines += ["", self.t("cs_confirm_archive")]
        return "\n".join(lines)

    def ask_confirm(self, text):
        """Asked before anything is written: a method of its own, so that a test answers it without a modal."""
        return QMessageBox.question(self, self.windowTitle(), text) == QMessageBox.StandardButton.Yes

    def apply(self):
        """«Appliquer»: once confirmed, the choices written (content_switch.apply) and the dialog accepted, the Result kept in `result_`. A refusal is said in the banner by its code -- the comparison made again where a file changed under it. Returns the Result, or None."""
        if self.comparison is None or self.read_only:
            return None
        try:
            text = self.confirm_text()
        except content_switch.ContentSwitchError as exc:
            self.say(error_text(self.lang, exc), exc)
            return None
        if not self.ask_confirm(text):
            return None
        try:
            result = content_switch.apply(self.here, self.mode, self.comparison, self.choices())
        except content_switch.ContentSwitchError as exc:
            if exc.code in ("changed_meanwhile", "wrong_comparison"):
                self.compare()
            self.say(error_text(self.lang, exc), exc)
            return None
        self.result_ = result
        self.accept()
        return result
