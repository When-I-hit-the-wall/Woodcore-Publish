"""The right pane of a text placed with the Text tool, the same in the four drawing engines -- the schemas, the static models, the position plans and the fire-protection plans (spec docs/requirements/completed/2026-10-11-variables-liees-champs-et-textes.md, UI-004, REQ-011, ARCH-003).

* **The content**, typed as it prints, a line per line. A variable inserted is a token, `{1}`, which the content shows where it stands; a literal brace is typed twice, `{{` (D-13). What is typed is taken a moment after the last key, as one step of «Annuler»; a content the file could not hold -- a brace alone, a token naming no variable -- is said under the field and not taken.
* **«Insérer une variable»** brings the «Variables» tab forward in its choosing mode, every number of the export and of a «Formule» domain offered, whatever its unit (D-08), and inserts the one chosen where the cursor stands.
* **A card per variable**: its token, its symbol and its domain, what it prints now, «valeur» or «symbole = valeur» (D-09), and «Retirer», which takes its token with it. A variable that can no longer be read prints its last value, in the theme's warning colour (D-06).
* **The size** is the drawing's own `text` factor, which the entry may state over it in the style card every engine already shows (figure_style, `texts`).

What a text prints is `calc/domains/figure_text.py`'s, resolved against the export's values (`linkable_spin.current_values`): the pane shows what the report will print. Nothing is computed here.
"""

import html

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QPlainTextEdit, QPushButton, QToolButton, QVBoxLayout, QWidget

import cards
import linkable_spin
import theme
import variable_sources
from domains import figure_text, links

STRINGS = {
    "fr": {
        "tx_card": "Texte",
        "tx_content": "Contenu",
        "tx_content_tip": "Le texte tel qu’il s’imprime, une ligne par ligne. Une variable insérée s’y montre comme {1} ; une accolade se tape deux fois, {{. Un _ met la suite en indice.",
        "tx_insert": "Insérer une variable",
        "tx_insert_tip": "Choisir une variable de l’export ou de l’onglet « Formules » ; elle s’insère où se trouve le curseur",
        "tx_pick_title": "Choisir une variable à insérer dans le texte {id}",
        "tx_var": "{token} — {symbol} — {domain}",
        "tx_show": "Afficher",
        "tx_show_value": "valeur",
        "tx_show_symbol": "symbole = valeur",
        "tx_remove": "Retirer",
        "tx_remove_tip": "Retirer cette variable du texte, avec son jeton",
        "tx_prints": "Imprime : {text}",
        "tx_missing": "Introuvable : {ref} — dernière valeur imprimée",
        "tx_refused": "Non repris : {reason}",
        "tx_unavailable": "L’onglet « Variables » n’est pas disponible.",
    },
    "de": {
        "tx_card": "Text",
        "tx_content": "Inhalt",
        "tx_content_tip": "Der Text, wie er gedruckt wird, Zeile für Zeile. Eine eingefügte Variable erscheint als {1}; eine geschweifte Klammer wird doppelt getippt, {{. Ein _ setzt das Folgende tief.",
        "tx_insert": "Variable einfügen",
        "tx_insert_tip": "Eine Variable des Exports oder des Reiters «Formeln» wählen; sie wird an der Cursorposition eingefügt",
        "tx_pick_title": "Variable für den Text {id} wählen",
        "tx_var": "{token} — {symbol} — {domain}",
        "tx_show": "Anzeigen",
        "tx_show_value": "Wert",
        "tx_show_symbol": "Symbol = Wert",
        "tx_remove": "Entfernen",
        "tx_remove_tip": "Diese Variable samt ihrem Platzhalter aus dem Text entfernen",
        "tx_prints": "Druckt: {text}",
        "tx_missing": "Nicht gefunden: {ref} – letzter Wert gedruckt",
        "tx_refused": "Nicht übernommen: {reason}",
        "tx_unavailable": "Der Reiter «Variablen» ist nicht verfügbar.",
    },
    "en": {
        "tx_card": "Text",
        "tx_content": "Content",
        "tx_content_tip": "The text as it prints, a line per line. A variable inserted shows as {1}; a brace is typed twice, {{. An _ sets what follows as a subscript.",
        "tx_insert": "Insert a variable",
        "tx_insert_tip": "Choose a variable of the export or of the «Formulas» tab; it is inserted where the cursor is",
        "tx_pick_title": "Choose a variable to insert into text {id}",
        "tx_var": "{token} — {symbol} — {domain}",
        "tx_show": "Show",
        "tx_show_value": "value",
        "tx_show_symbol": "symbol = value",
        "tx_remove": "Remove",
        "tx_remove_tip": "Remove this variable from the text, with its token",
        "tx_prints": "Prints: {text}",
        "tx_missing": "Not found: {ref} — last value printed",
        "tx_refused": "Not taken: {reason}",
        "tx_unavailable": "The «Variables» tab is not available.",
    },
}

# The Text tool's button symbol, the same in the four engines: figure_text's, where the schemas' bar, which draws every symbol from its domain, finds it too.
icon_svg = figure_text.icon_svg


# How long after the last key the content is taken, in milliseconds: one step of «Annuler» for a word typed, not one per letter.
COMMIT_MS = 600


class TextPane(QWidget):
    """The card of a selected text (see the module's docstring).

    `entry` is the text as the source holds it, which the pane changes only through `edit(apply)` -- the tab's own single change, one step of «Annuler», which redraws; `rebuild()` is called after a change that adds or takes off a variable, so the tab builds its pane again. `app()` returns the window, whose `begin_variable_pick` the button calls; `values` are the export's, read now where None.
    """

    def __init__(self, entry, app, lang, edit, rebuild=None, values=None, read_only=False, parent=None):
        super().__init__(parent)
        self.entry = entry
        self.app = app
        self.lang = lang if lang in STRINGS else "en"
        self.edit = edit
        self.rebuild = rebuild or (lambda: None)
        self.values = linkable_spin.current_values() if values is None else values
        self.refused = None   # the last content not taken, for a test to read

        column = QVBoxLayout(self)
        column.setContentsMargins(0, 0, 0, 0)
        group = cards.card(self.t("tx_card"))
        form = cards.form(group)
        self.content = QPlainTextEdit()
        self.content.setPlainText(entry.get("text", ""))
        self.content.setToolTip(self.t("tx_content_tip"))
        self.content.setMaximumHeight(90)
        self.content.setReadOnly(read_only)
        form.addRow(self.t("tx_content"), self.content)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(COMMIT_MS)
        self.timer.timeout.connect(self.commit)
        self.content.textChanged.connect(self.timer.start)
        self.problem = QLabel("")
        self.problem.setWordWrap(True)
        self.problem.setStyleSheet(f"color: {theme.colour('warning')};")
        self.problem.setVisible(False)
        form.addRow(self.problem)
        self.insert_button = QPushButton(self.t("tx_insert"))
        self.insert_button.setToolTip(self.t("tx_insert_tip"))
        self.insert_button.clicked.connect(self.pick)
        self.insert_button.setEnabled(not read_only)
        form.addRow(self.insert_button)
        self.prints = QLabel("")
        self.prints.setWordWrap(True)
        form.addRow(self.prints)
        self.cards = []
        for token in figure_text.tokens(entry.get("text", "")):
            var = (entry.get("vars") or {}).get(token)
            if var is not None:
                self.cards.append(self.var_card(form, token, var, read_only))
        self.show_prints()
        column.addWidget(group)

    def t(self, key, **kwargs):
        text = STRINGS[self.lang][key]
        return text.format(**kwargs) if kwargs else text

    # -- the content ------------------------------------------------------------------------

    def show_prints(self):
        try:
            printed = figure_text.lines(self.entry, self.values)
        except (ValueError, KeyError):
            printed = []
        self.prints.setText(html.escape(self.t("tx_prints", text=" / ".join(printed))))

    def commit(self):
        """What is typed, taken as one step -- or, where the file could not hold it, said and not taken. True when taken."""
        self.timer.stop()
        text = self.content.toPlainText()
        if text == self.entry.get("text", ""):
            return True
        trial = {"text": text, "vars": dict(self.entry.get("vars") or {})}

        def fail(message):
            raise ValueError(message)

        try:
            figure_text.check(trial, fail, self.entry.get("id", ""))
        except ValueError as exc:
            self.refused = str(exc)
            self.problem.setText(self.t("tx_refused", reason=str(exc)))
            self.problem.setVisible(True)
            return False
        self.refused = None
        self.problem.setVisible(False)
        dropped = set(self.entry.get("vars") or {}) - set(figure_text.tokens(text))

        def apply():
            self.entry["text"] = text
            figure_text.drop_unused(self.entry)
        self.edit(apply)
        self.show_prints()
        if dropped:
            self.rebuild()   # a token deleted by hand takes its variable's card with it
        return True

    # -- «Insérer une variable» ---------------------------------------------------------------

    def pick(self):
        """The «Variables» tab in its choosing mode, every number of the export offered (D-08)."""
        if not self.commit():
            return
        window = self.app() if self.app is not None else None
        begin = getattr(window, "begin_variable_pick", None)

        def accept(var, domain):
            return variable_sources.linkable(var, domain, None)

        at = self.content.textCursor().position()
        if begin is None or not begin(lambda chosen: self.on_picked(chosen, at), self.t("tx_pick_title", id=self.entry.get("id", "")), accept):
            setter = getattr(window, "set_status", None)
            if setter is not None:
                setter(self.t("tx_unavailable"))

    def on_picked(self, chosen, at=None):
        """What the «Variables» tab gave back, inserted at character `at` of the content (its end where None): (source, domain, variable, its export address), or None where the choice was given up."""
        if chosen is None:
            return
        origin, domain_name, var, address = chosen
        link = links.from_choice(origin, domain_name, var.key, address)
        if link is None:
            return

        def apply():
            key = figure_text.insert(self.entry, link, at)
            figure_text.refresh(self.entry, self.values)
            if not figure_text.resolve_var(self.entry["vars"][key], self.values)["stale"]:
                return
            # the variable chosen is not in the values the pane holds (an export not yet written): its value now, from the choice
            self.entry["vars"][key]["last"] = {"value": var.value, "unit": var.unit or "", "symbol": getattr(var, "symbol", "") or var.key}
        self.edit(apply)
        self.rebuild()

    # -- a card per variable -------------------------------------------------------------------

    def var_card(self, form, token, var, read_only):
        link = figure_text.link_of(var)
        found = figure_text.resolve_var(var, self.values)
        domain = link["instance"] if link.get("origin") == links.FORMULAS else f"{link['domain']} · {link['instance']}"
        box = QWidget()
        column = QVBoxLayout(box)
        column.setContentsMargins(0, 4, 0, 4)
        title = QLabel(html.escape(self.t("tx_var", token="{" + token + "}", symbol=found["symbol"], domain=domain)))
        title.setWordWrap(True)
        column.addWidget(title)
        if found["stale"]:
            missing = QLabel(html.escape(self.t("tx_missing", ref=links.link_text(link))))
            missing.setWordWrap(True)
            missing.setStyleSheet(f"color: {theme.colour('warning')};")
            column.addWidget(missing)
        row = QHBoxLayout()
        row.addWidget(QLabel(self.t("tx_show")))
        show = QComboBox()
        for mode in figure_text.SHOWS:
            show.addItem(self.t("tx_show_" + mode), mode)
        show.setCurrentIndex(figure_text.SHOWS.index(var.get("show", figure_text.DEFAULT_SHOW)))
        show.setEnabled(not read_only)
        show.currentIndexChanged.connect(lambda _i, k=token, c=show: self.set_show(k, c.currentData()))
        row.addWidget(show, 1)
        remove = QToolButton()
        remove.setText(self.t("tx_remove"))
        remove.setToolTip(self.t("tx_remove_tip"))
        remove.setEnabled(not read_only)
        remove.clicked.connect(lambda _c=False, k=token: self.remove(k))
        row.addWidget(remove)
        column.addLayout(row)
        form.addRow(box)
        return {"token": token, "show": show, "remove": remove, "title": title}

    def set_show(self, token, mode):
        self.edit(lambda: self.entry["vars"][token].update(show=mode))
        self.show_prints()

    def remove(self, token):
        """«Retirer»: the variable and its token leave the text."""
        if not self.commit():
            return
        self.edit(lambda: figure_text.remove_var(self.entry, token))
        self.rebuild()
