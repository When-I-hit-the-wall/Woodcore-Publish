"""Woodcore's copyright, its licence and the third-party notices, as the window shows them: a line at the foot of the start page, and *Fichier → À propos de Woodcore…*.

The texts themselves are legal/LICENSE-fr.txt, -de.txt, -en.txt and legal/THIRD-PARTY-NOTICES.txt (packaging/notices.py writes the last), beside the code in a checkout and in the program's _internal\\legal folder once installed (packaging/woodcore.spec), so `project.APP_ROOT / "legal"` finds them either way. The installer shows the licence before it installs anything (packaging/woodcore.iss) and the website publishes the four files (website/build.py). This module carries its own words in three languages, apart from the window's STRINGS, so that the start page and the window share them.
"""

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QPushButton, QVBoxLayout

import project
import notifications  # every error, warning and information, gathered in one place (calc/notifications.py, v0.117)
import notices_ui  # what was a message box is a notice since v0.117 (notices_ui.tell)

HOLDER = "Florian Lamprecht"
EMAIL = "woodcore@pineo.ch"
YEAR = "2026"
COPYRIGHT = f"© {YEAR} {HOLDER}"
SITE = "https://woodcore.pages.dev/"
LEGAL_DIR = project.APP_ROOT / "legal"
LANGUAGES = ("fr", "de", "en")

TEXTS = {
    "fr": {
        "about_menu": "À propos de Woodcore…",
        "about_title": "À propos de Woodcore",
        "reserved": "Tous droits réservés.",
        "disclaimer": "Woodcore est une version préliminaire, fournie gratuitement et sans garantie. C'est un outil d'aide : l'ingénieur qui signe un rapport reste seul responsable de vérifier les données, les hypothèses et les résultats.",
        "updates": "Au démarrage, une version installée lit version.json sur le site de Woodcore pour savoir si une nouvelle version existe ; aucune donnée de vos projets n'est transmise.",
        "licence": "Conditions de licence…",
        "notices": "Composants tiers…",
        "site": "Site internet",
        "missing": "Le fichier {file} est introuvable.",
    },
    "de": {
        "about_menu": "Über Woodcore…",
        "about_title": "Über Woodcore",
        "reserved": "Alle Rechte vorbehalten.",
        "disclaimer": "Woodcore ist eine Vorabversion, unentgeltlich und ohne Gewährleistung zur Verfügung gestellt. Es ist ein Hilfsmittel: Der Ingenieur, der einen Bericht unterzeichnet, bleibt allein dafür verantwortlich, Daten, Annahmen und Ergebnisse zu prüfen.",
        "updates": "Beim Start liest eine installierte Version version.json auf der Website von Woodcore, um festzustellen, ob eine neue Version besteht; es werden keine Daten Ihrer Projekte übermittelt.",
        "licence": "Lizenzbedingungen…",
        "notices": "Komponenten Dritter…",
        "site": "Website",
        "missing": "Die Datei {file} ist nicht auffindbar.",
    },
    "en": {
        "about_menu": "About Woodcore…",
        "about_title": "About Woodcore",
        "reserved": "All rights reserved.",
        "disclaimer": "Woodcore is a preliminary version, provided free of charge and without warranty. It is an aid: the engineer who signs a report remains solely responsible for checking the data, the assumptions and the results.",
        "updates": "At start-up, an installed version reads version.json on Woodcore's website to find out whether a newer version exists; no data from your projects is sent.",
        "licence": "Licence terms…",
        "notices": "Third-party components…",
        "site": "Website",
        "missing": "The file {file} cannot be found.",
    },
}


def text(lang, key, **values):
    words = TEXTS.get(lang) or TEXTS["en"]
    return words[key].format(**values)


def licence_path(lang):
    return LEGAL_DIR / f"LICENSE-{lang if lang in LANGUAGES else 'en'}.txt"


def notices_path():
    return LEGAL_DIR / "THIRD-PARTY-NOTICES.txt"


def copyright_line():
    """«© 2026 Florian Lamprecht · woodcore@pineo.ch», the line the start page and the dialog carry."""
    return f"{COPYRIGHT} · {EMAIL}"


def copyright_label(parent=None):
    """The start page's line, in the theme's grey (objectName "meta"); the address opens a mail."""
    label = QLabel(f'{COPYRIGHT} · <a href="mailto:{EMAIL}">{EMAIL}</a>', parent)
    label.setObjectName("meta")
    label.setTextFormat(Qt.TextFormat.RichText)
    label.setOpenExternalLinks(True)
    label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
    return label


def open_file(path, parent=None, lang="en"):
    """A licence file opened in the program Windows opens a .txt with; said in a box where it is not there."""
    if path.is_file():
        return QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))
    from PySide6.QtWidgets import QMessageBox
    notices_ui.tell(text(lang, "missing", file=str(path)), notifications.WARNING, source="legal")
    return False


class AboutDialog(QDialog):
    """Woodcore's version, its copyright and contact, the disclaimer, the update check, and the licence and the notices a click away."""

    def __init__(self, parent=None, lang="fr", version=None):
        super().__init__(parent)
        self.lang = lang
        self.setWindowTitle(text(lang, "about_title"))
        layout = QVBoxLayout(self)
        title = QLabel(f"<b>Woodcore {version or project.VERSION}</b>")
        title.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(title)
        owner = QLabel(f'{COPYRIGHT} — {text(lang, "reserved")}<br><a href="mailto:{EMAIL}">{EMAIL}</a> · <a href="{SITE}">{text(lang, "site")}</a>')
        owner.setTextFormat(Qt.TextFormat.RichText)
        owner.setOpenExternalLinks(True)
        layout.addWidget(owner)
        for key in ("disclaimer", "updates"):
            label = QLabel(text(lang, key))
            label.setWordWrap(True)
            label.setObjectName("meta")
            layout.addWidget(label)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        self.licence_button = QPushButton(text(lang, "licence"))
        self.notices_button = QPushButton(text(lang, "notices"))
        buttons.addButton(self.licence_button, QDialogButtonBox.ButtonRole.ActionRole)
        buttons.addButton(self.notices_button, QDialogButtonBox.ButtonRole.ActionRole)
        self.licence_button.clicked.connect(lambda: open_file(licence_path(self.lang), self, self.lang))
        self.notices_button.clicked.connect(lambda: open_file(notices_path(), self, self.lang))
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.setMinimumWidth(460)


def add_about_action(menu, parent, lang):
    """*À propos de Woodcore…* in the *Fichier* menu."""
    return menu.addAction(text(lang, "about_menu"), lambda: AboutDialog(parent, lang).exec())
