"""The window's side of the Typst check (docs/ui/window.md §10quater, v0.94): a modal where the Typst found is missing or not the one pinned, a banner where a newer one is published, and winget run on a yes with its output shown.

calc/tools/typst_check.py asks the questions; this module asks the engineer. At the start of a window run from its sources -- `check_at_start`, queued by open_project after the engine's and the packages' checks -- the Typst found is compared with requirements.txt's pin, offline: missing or another version, a modal offers to install the pinned one; then GitHub is asked in a thread, and a newer version comes back as a banner with its button, in the quieter blue of the packages' own (the window rebuilt to show it, as `on_updates` does). A question already up -- the engine's, the packages' -- is let finish first, as update_gui.py lets it.

Installing runs `winget` in a process of its own, its output in a window of its own, and nothing runs before the engineer's yes. The newer version is then pinned (typst_check.pin: typst-version.txt, the one file the pin lives in), and the window says which Typst the PATH now gives -- a Typst installed otherwise may come first and hide winget's -- and that Woodcore compiles with it once started again. An installed Woodcore asks nothing (typst_check.enabled).
"""

import html
import re
import subprocess
import threading

from PySide6.QtCore import QObject, QProcess, QTimer, Qt, Signal
from PySide6.QtWidgets import (
    QApplication, QDialog, QDialogButtonBox, QHBoxLayout, QLabel, QMessageBox, QPlainTextEdit, QPushButton, QVBoxLayout,
)

import proc
import theme
import typst_check
import usersettings
import notifications  # every error, warning and information, gathered in one place (calc/notifications.py, v0.117)
import notices_ui  # what was a message box is a notice since v0.117 (notices_ui.tell)

LANGUAGES = ("fr", "de", "en")

STRINGS = {
    "fr": {
        "typst_title": "Typst",
        "typst_missing": "Typst est introuvable : ce rapport se compile avec Typst {wanted}, la version que requirements.txt nomme.\n\nL'installer maintenant avec winget ?",
        "typst_other": "Typst {found} est installé ; ce rapport est vérifié avec Typst {wanted}, la version que requirements.txt nomme.\n\nInstaller Typst {wanted} maintenant avec winget ?",
        "typst_install": "Installer",
        "typst_later": "Plus tard",
        "typst_no_winget": "winget est introuvable sur ce poste : installez Typst {version} vous-même depuis <a href=\"{page}\">la page des versions de Typst</a>, puis relancez Woodcore.",
        "typst_banner": "Typst {available} est disponible — ce rapport est vérifié avec Typst {pinned} (requirements.txt).",
        "typst_banner_button": "Installer Typst {version}",
        "typst_update_ask": "Installer Typst {version} avec winget, et en faire la version de ce rapport ?\n\nrequirements.txt et .github/workflows/site.yml nommeront Typst {version} : le site est compilé avec elle, et la construction de l'installateur l'exige. Un rapport déjà exporté peut s'imprimer autrement.",
        "typst_running": "Installation de Typst {version} avec winget…",
        "typst_close": "Fermer",
        "typst_failed": "winget s'est terminé avec le code {code} : Typst {version} n'a pas été installé. Sa sortie est dans la fenêtre d'installation.",
        "typst_done": "Typst {version} est installé : {path}.",
        "typst_pinned": "requirements.txt et .github/workflows/site.yml nomment désormais Typst {version}, et la construction de l'installateur suit ce numéro.",
        "typst_pin_failed": "Typst {version} est installé, mais son numéro n'a pas pu être écrit : {error}",
        "typst_shadowed": "Typst {version} a été installé ({where}), mais le premier typst du PATH reste {path} (Typst {found}) : retirez son dossier du PATH, ou placez {links} avant lui.",
        "typst_not_found": "winget dit avoir installé Typst {version}, mais aucun typst du PATH n'est cette version : voyez {links}.",
        "typst_restart": "Relancez Woodcore pour qu'il compile avec la nouvelle version.",
    },
    "de": {
        "typst_title": "Typst",
        "typst_missing": "Typst ist nicht zu finden: dieser Bericht wird mit Typst {wanted} kompiliert, der Version, die requirements.txt nennt.\n\nJetzt mit winget installieren?",
        "typst_other": "Typst {found} ist installiert; dieser Bericht ist mit Typst {wanted} geprüft, der Version, die requirements.txt nennt.\n\nTypst {wanted} jetzt mit winget installieren?",
        "typst_install": "Installieren",
        "typst_later": "Später",
        "typst_no_winget": "winget ist auf diesem Rechner nicht zu finden: Typst {version} selbst von der <a href=\"{page}\">Versionsseite von Typst</a> installieren und Woodcore neu starten.",
        "typst_banner": "Typst {available} ist verfügbar — dieser Bericht ist mit Typst {pinned} geprüft (requirements.txt).",
        "typst_banner_button": "Typst {version} installieren",
        "typst_update_ask": "Typst {version} mit winget installieren und zur Version dieses Berichts machen?\n\nrequirements.txt und .github/workflows/site.yml nennen dann Typst {version}: die Website wird damit kompiliert, und der Bau des Installationsprogramms verlangt sie. Ein bereits exportierter Bericht kann anders gedruckt werden.",
        "typst_running": "Typst {version} wird mit winget installiert…",
        "typst_close": "Schliessen",
        "typst_failed": "winget endete mit dem Code {code}: Typst {version} wurde nicht installiert. Seine Ausgabe steht im Installationsfenster.",
        "typst_done": "Typst {version} ist installiert: {path}.",
        "typst_pinned": "requirements.txt und .github/workflows/site.yml nennen jetzt Typst {version}, und der Bau des Installationsprogramms folgt dieser Nummer.",
        "typst_pin_failed": "Typst {version} ist installiert, aber seine Nummer konnte nicht geschrieben werden: {error}",
        "typst_shadowed": "Typst {version} wurde installiert ({where}), aber das erste typst im PATH bleibt {path} (Typst {found}): seinen Ordner aus dem PATH entfernen oder {links} davor setzen.",
        "typst_not_found": "winget meldet Typst {version} als installiert, aber kein typst im PATH ist diese Version: siehe {links}.",
        "typst_restart": "Woodcore neu starten, damit es mit der neuen Version kompiliert.",
    },
    "en": {
        "typst_title": "Typst",
        "typst_missing": "Typst cannot be found: this report is compiled with Typst {wanted}, the version requirements.txt names.\n\nInstall it now with winget?",
        "typst_other": "Typst {found} is installed; this report is verified with Typst {wanted}, the version requirements.txt names.\n\nInstall Typst {wanted} now with winget?",
        "typst_install": "Install",
        "typst_later": "Later",
        "typst_no_winget": "winget cannot be found on this machine: install Typst {version} yourself from <a href=\"{page}\">Typst's releases page</a>, then start Woodcore again.",
        "typst_banner": "Typst {available} is available — this report is verified with Typst {pinned} (requirements.txt).",
        "typst_banner_button": "Install Typst {version}",
        "typst_update_ask": "Install Typst {version} with winget, and make it this report's version?\n\nrequirements.txt and .github/workflows/site.yml will name Typst {version}: the website is compiled with it, and building the installer requires it. A report already exported may print otherwise.",
        "typst_running": "Installing Typst {version} with winget…",
        "typst_close": "Close",
        "typst_failed": "winget ended with the code {code}: Typst {version} was not installed. Its output is in the installation window.",
        "typst_done": "Typst {version} is installed: {path}.",
        "typst_pinned": "requirements.txt and .github/workflows/site.yml now name Typst {version}, and building the installer follows that number.",
        "typst_pin_failed": "Typst {version} is installed, but its number could not be written: {error}",
        "typst_shadowed": "Typst {version} was installed ({where}), but the first typst on the PATH is still {path} (Typst {found}): take its folder off the PATH, or put {links} before it.",
        "typst_not_found": "winget says it installed Typst {version}, but no typst on the PATH is that version: see {links}.",
        "typst_restart": "Start Woodcore again for it to compile with the new version.",
    },
}

for _lang in LANGUAGES[1:]:
    assert set(STRINGS[_lang]) == set(STRINGS["fr"]), f"typst_gui.STRINGS[{_lang!r}] does not carry the same keys as French"

# The bridges a thread answers through, kept alive until the process ends -- a QObject collected before its signal arrives would drop it.
_KEEP = []


def _lang(window=None):
    lang = getattr(window, "lang", None) or usersettings.read().get("lang")
    return lang if lang in LANGUAGES else "fr"


def _t(lang, key, **values):
    text = STRINGS[lang][key]
    return text.format(**values) if values else text


class _Bridge(QObject):
    """Carries GitHub's answer from its thread back to the one the widgets live in."""
    found = Signal(object)


# --- at the start ------------------------------------------------------------------------------

def check_at_start(window, attempt=0, fetch=None, run=None):
    """Run once, just after a window run from its sources is up: the offline question first -- a modal only where Typst is missing or another version than the pin -- then GitHub asked in a thread. Nothing at all where typst_check.enabled() says no. `fetch` and `run` replace the network and the subprocesses (tests)."""
    if not typst_check.enabled():
        return None
    if QApplication.activeModalWidget() is not None and attempt < 60:
        QTimer.singleShot(1000, lambda: check_at_start(window, attempt + 1, fetch, run) if window.isVisible() else None)
        return None
    what, found, wanted = typst_check.state(**({"run": run} if run else {}))
    if what in ("missing", "other"):
        ask_install(window, what, found, wanted)
    return ask_github(window, fetch)


def ask_github(window, fetch=None):
    """GitHub asked in a thread; a newer Typst than the pin comes back as `window.typst_update` and the window is rebuilt to show its banner. Silent on any failure."""
    bridge = _Bridge()
    _KEEP.append(bridge)
    bridge.found.connect(lambda version: on_found(window, version))

    def ask():
        try:
            version = typst_check.update(fetch=fetch)
        except Exception:  # broad: an answer nobody asked for must never bring the window down
            version = None
        bridge.found.emit(version)

    threading.Thread(target=ask, daemon=True).start()
    return bridge


def on_found(window, version):
    if not version or getattr(window, "typst_update", None) == version:
        return
    window.typst_update = version
    rebuild = getattr(window, "rebuild", None)
    if callable(rebuild):
        rebuild()


def add_banner(window, layout):
    """The banner a newer Typst puts under the window's top bar, with its button: the packages' own arrangement, in the quieter blue of an offer (the `info` callout). Nothing where there is nothing newer. Returns the row, or None."""
    version = getattr(window, "typst_update", None)
    if not version:
        return None
    lang = _lang(window)
    row = QHBoxLayout()
    note = QLabel(_t(lang, "typst_banner", available=version, pinned=typst_check.pinned() or "?"))
    note.setWordWrap(True)
    note.setProperty("callout", "info")
    row.addWidget(note, 1)
    button = QPushButton(_t(lang, "typst_banner_button", version=version))
    button.clicked.connect(lambda: install_newer(window, version))
    row.addWidget(button)
    layout.addLayout(row)
    return row


def ask_install(window, what, found, wanted):
    """The modal of a Typst missing or not the one pinned: «Installer» runs winget for the pinned version, «Plus tard» asks again at the next start."""
    lang = _lang(window)
    text = _t(lang, "typst_missing", wanted=wanted) if what == "missing" else _t(lang, "typst_other", found=found, wanted=wanted)
    box = QMessageBox(QMessageBox.Icon.Warning, _t(lang, "typst_title"), text, parent=window)  # dialog-ok: «Installer» or «Plus tard», a decision that waits for its answer
    install = box.addButton(_t(lang, "typst_install"), QMessageBox.ButtonRole.AcceptRole)
    later = box.addButton(_t(lang, "typst_later"), QMessageBox.ButtonRole.RejectRole)
    box.setDefaultButton(install)
    box.setEscapeButton(later)
    box.exec()
    if box.clickedButton() is install:
        return run_install(window, wanted, pin_after=False)
    return False


def install_newer(window, version):
    """The banner's button: install the newer Typst and pin it, on a yes."""
    lang = _lang(window)
    if QMessageBox.question(window, _t(lang, "typst_title"), _t(lang, "typst_update_ask", version=version)) != QMessageBox.StandardButton.Yes:
        return False
    return run_install(window, version, pin_after=True)


# --- installing --------------------------------------------------------------------------------

class InstallDialog(QDialog):
    """winget running, its output shown as it comes, «Fermer» once it has ended. `code` is its exit code, -1 where it could not start."""

    def __init__(self, parent, lang, version, command):
        super().__init__(parent)
        self.lang = lang
        self.command = list(command)
        self.code = None
        self.setWindowTitle(_t(lang, "typst_running", version=version))
        self.resize(760, 420)
        layout = QVBoxLayout(self)
        self.output = QPlainTextEdit()
        self.output.setObjectName("code")   # the site's code ground (theme.py)
        self.output.setReadOnly(True)
        self.output.setFont(theme.mono_font())
        layout.addWidget(self.output, 1)
        self.buttons = QDialogButtonBox()
        self.close_button = self.buttons.addButton(_t(lang, "typst_close"), QDialogButtonBox.ButtonRole.RejectRole)
        self.close_button.setEnabled(False)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)
        self.process = proc.qprocess(self)
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.process.readyReadStandardOutput.connect(self.read_output)
        self.process.finished.connect(self.on_finished)
        self.process.errorOccurred.connect(self.on_error)

    def start(self):
        self.output.appendPlainText("> " + subprocess.list2cmdline(self.command))
        self.process.start(self.command[0], self.command[1:])

    def read_output(self):
        text = bytes(self.process.readAllStandardOutput()).decode("utf-8", "replace")
        # winget draws its progress bars with carriage returns: each line keeps what was drawn last
        lines = [line.rsplit("\r", 1)[-1] for line in text.replace("\r\n", "\n").split("\n")]
        kept = "\n".join(line for line in lines if line.strip())
        if kept:
            self.output.appendPlainText(kept)

    def on_finished(self, code, _status=None):
        self.read_output()
        self.code = code
        self.close_button.setEnabled(True)

    def on_error(self, error):
        if error == QProcess.ProcessError.FailedToStart:   # the one error no `finished` follows
            self.output.appendPlainText(self.process.errorString())
            self.code = -1
            self.close_button.setEnabled(True)

    def reject(self):
        if self.code is None:   # winget is not stopped half way through an installation
            return
        super().reject()

    def run(self):
        """Starts winget, shows the window until the engineer closes it, and returns winget's exit code."""
        self.start()
        self.exec()
        return -1 if self.code is None else self.code


def no_winget(window, version):
    lang = _lang(window)
    # no winget to install Typst with: a warning, the release page named in its technical text, to be copied (v0.117: no box)
    text = _t(lang, "typst_no_winget", version=version, page=typst_check.RELEASES_PAGE)
    notifications.report("typst_no_winget", re.sub(r"<[^>]+>", "", text), notifications.WARNING, technical=typst_check.RELEASES_PAGE, source="typst_gui")


def run_install(window, version, pin_after):
    """winget for Typst `version`, on a yes already given: `winget list` asked first whether the Typst there is winget's (upgrade, else install), the installation shown as it runs; then, for a newer version, the pin rewritten (typst_check.pin); and what the PATH now gives, said. Returns whether winget succeeded."""
    lang = _lang(window)
    if typst_check.winget() is None:
        no_winget(window, version)
        return False
    QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
    try:
        managed, current = typst_check.winget_list()
    finally:
        QApplication.restoreOverrideCursor()
    dialog = InstallDialog(window, lang, version, typst_check.install_command(version, managed, current))
    code = dialog.run()
    if code != 0:
        notices_ui.tell(_t(lang, "typst_failed", code=code, version=version), notifications.WARNING, source="typst_gui")
        return False
    said = []
    if pin_after:
        try:
            typst_check.pin(version)
            said.append(_t(lang, "typst_pinned", version=version))
        except (OSError, typst_check.PinError) as exc:
            said.append(_t(lang, "typst_pin_failed", version=version, error=exc))
    found = typst_check.after_install(version)
    links = str(typst_check.winget_links())
    if found["ok"]:
        said.insert(0, _t(lang, "typst_done", version=version, path=found["first"][0]))
    elif found["found"] and found["first"]:
        said.insert(0, _t(lang, "typst_shadowed", version=version, where=found["found"], path=found["first"][0], found=found["first"][1] or "?", links=links))
    else:
        said.insert(0, _t(lang, "typst_not_found", version=version, links=links))
    said.append(_t(lang, "typst_restart"))
    notices_ui.tell("\n\n".join(said), notifications.INFO, source="typst_gui")
    if pin_after and getattr(window, "typst_update", None):
        window.typst_update = None
        rebuild = getattr(window, "rebuild", None)
        if callable(rebuild):
            rebuild()
    return True
