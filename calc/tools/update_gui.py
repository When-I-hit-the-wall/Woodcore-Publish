"""The window's side of an update (docs/ui/window.md §10quater, v0.89): the question at the start, the download, the installer started.

The engineer's choices: a **window at the start**, once per new version, rather than a banner that can go unseen -- «Installer», «Plus tard», «Ignorer cette version» -- and «Installer» **downloads and starts the installer** from here, checked against the SHA-256 the site states (updates.py), rather than sending him to a web page. The manifest is asked for in a thread of its own, so a window opens exactly as fast without a network, and says nothing at all where there is none. A modal already up -- the lock's question, the engine's -- is let finish first: two questions on top of each other are one too many.

Nothing is replaced. Versions install side by side (packaging/woodcore.iss), the new one opens at the end of its installer, and a project pinned to an older version still opens with it. This window may stay open; the Start menu's «Woodcore» starts the newest from then on (packaging/launcher.py).
"""

import html
import threading

import project
import updates
import usersettings
import notifications  # every error, warning and information, gathered in one place (calc/notifications.py, v0.117)
import notices_ui  # what was a message box is a notice since v0.117 (notices_ui.tell)
from PySide6.QtCore import QObject, Qt, QTimer, Signal
from PySide6.QtWidgets import QApplication, QMessageBox, QProgressDialog

LANGUAGES = ("fr", "de", "en")

STRINGS = {
    "fr": {
        "title": "Mise à jour de Woodcore",
        "available": "Woodcore {version} est disponible — vous utilisez la version {current}.",
        "whatsnew": "Nouveautés :",
        "details": "Ce qui change pour vous, et ce qu'il faut faire",
        "sidebyside": "La nouvelle version s'installe à côté de celle-ci : vos projets épinglés à une version s'ouvrent toujours avec la leur.",
        "install": "Installer",
        "later": "Plus tard",
        "skip": "Ignorer cette version",
        "downloading": "Téléchargement de Woodcore {version}…",
        "cancel": "Annuler",
        "started": "L'installateur de Woodcore {version} est lancé. À la fin, la nouvelle version s'ouvre ; vous pouvez fermer cette fenêtre-ci.",
        "failed": "La mise à jour n'a pas pu être téléchargée : {reason}\n\nVous pouvez la télécharger depuis {page}",
        "reason_network": "le site n'a pas répondu ({error}).",
        "reason_size": "le fichier reçu n'a pas la taille annoncée.",
        "reason_sha256": "le fichier reçu n'est pas celui que le site annonce (empreinte SHA-256 différente) ; il a été supprimé.",
        "reason_launch": "l'installateur n'a pas pu être lancé ({error}).",
    },
    "de": {
        "title": "Woodcore-Aktualisierung",
        "available": "Woodcore {version} ist verfügbar — Sie verwenden die Version {current}.",
        "whatsnew": "Neu:",
        "details": "Was sich für Sie ändert, und was zu tun ist",
        "sidebyside": "Die neue Version wird neben dieser installiert: Projekte, die auf eine Version festgelegt sind, öffnen sich weiterhin mit ihrer.",
        "install": "Installieren",
        "later": "Später",
        "skip": "Diese Version überspringen",
        "downloading": "Woodcore {version} wird heruntergeladen…",
        "cancel": "Abbrechen",
        "started": "Das Installationsprogramm von Woodcore {version} läuft. Am Ende öffnet sich die neue Version; dieses Fenster können Sie schliessen.",
        "failed": "Die Aktualisierung konnte nicht heruntergeladen werden: {reason}\n\nSie können sie hier herunterladen: {page}",
        "reason_network": "die Website hat nicht geantwortet ({error}).",
        "reason_size": "die erhaltene Datei hat nicht die angegebene Grösse.",
        "reason_sha256": "die erhaltene Datei ist nicht die, welche die Website angibt (andere SHA-256-Prüfsumme); sie wurde gelöscht.",
        "reason_launch": "das Installationsprogramm konnte nicht gestartet werden ({error}).",
    },
    "en": {
        "title": "Woodcore update",
        "available": "Woodcore {version} is available — you are using version {current}.",
        "whatsnew": "What's new:",
        "details": "What changes for you, and what to do",
        "sidebyside": "The new version installs beside this one: projects pinned to a version still open with theirs.",
        "install": "Install",
        "later": "Later",
        "skip": "Skip this version",
        "downloading": "Downloading Woodcore {version}…",
        "cancel": "Cancel",
        "started": "The installer of Woodcore {version} is running. The new version opens at its end; you may close this window.",
        "failed": "The update could not be downloaded: {reason}\n\nYou can download it from {page}",
        "reason_network": "the site did not answer ({error}).",
        "reason_size": "the file received is not the size stated.",
        "reason_sha256": "the file received is not the one the site states (another SHA-256); it was deleted.",
        "reason_launch": "the installer could not be started ({error}).",
    },
}

# Held for the life of the process: a QObject nothing refers to is collected, and its signal with it.
_KEEP = []


def _lang():
    lang = usersettings.read().get("lang")
    return lang if lang in LANGUAGES else "fr"


def _t(lang, key, **values):
    return STRINGS[lang][key].format(**values)


def _parent(app):
    """The window to sit on: the one in front, else any shown -- the start page may have closed on a project opened meanwhile."""
    window = app.activeWindow()
    if window is not None and window.isVisible():
        return window
    return next((w for w in app.topLevelWidgets() if w.isVisible() and w.isWindow() and not isinstance(w, QProgressDialog)), None)


class _Bridge(QObject):
    """Carries an answer from a worker thread back to the one the widgets live in."""
    found = Signal(object)
    progress = Signal(int, int)
    done = Signal(object, object)


def schedule(app, current=None, fetch=None):
    """Asks the site in the background, and announces a newer version once the window is up. Does nothing where updates.enabled() says no (a checkout, a test run). `fetch` replaces the network (tests)."""
    if not updates.enabled(usersettings.read()):
        return None
    current = current or project.VERSION
    bridge = _Bridge()
    _KEEP.append(bridge)
    bridge.found.connect(lambda manifest: _announce(app, manifest, current))

    def ask():
        try:
            manifest = (fetch or updates.fetch)()
        except Exception:  # broad: an answer nobody asked for must never bring the window down
            manifest = None
        bridge.found.emit(manifest)

    threading.Thread(target=ask, daemon=True).start()
    return bridge


def _announce(app, manifest, current, attempt=0):
    settings = usersettings.read()
    if not updates.offer(manifest, current, settings):
        return
    parent = _parent(app)
    if parent is None or QApplication.activeModalWidget() is not None:
        if attempt < 60:   # a question already up, or no window yet: asked again once it is answered
            QTimer.singleShot(2000, lambda: _announce(app, manifest, current, attempt + 1))
        return
    choice = ask(parent, manifest, current, _lang())
    if choice == "skip":
        usersettings.write(updates.skip(usersettings.read(), manifest["version"]))
    elif choice == "later":
        usersettings.write(updates.snooze(usersettings.read(), manifest["version"]))
    elif choice == "install":
        install(parent, manifest, _lang())


def ask(parent, manifest, current, lang):
    """The question itself: "install", "later" or "skip"."""
    box = QMessageBox(parent)  # dialog-ok: install now, later or skip this version -- a decision that waits for its answer
    box.setIcon(QMessageBox.Icon.Information)
    box.setWindowTitle(_t(lang, "title"))
    box.setText(_t(lang, "available", version=manifest["version"], current=current))
    what = updates.notes(manifest, lang)
    link = updates.changes(manifest, lang)
    if link:
        # the page of what the version changes, as a link the box opens in the browser (version.json's `changes`, v0.89)
        def esc(text):
            return html.escape(text).replace("\n", "<br>")
        informative = (f"<p>{esc(_t(lang, 'whatsnew'))}<br>{esc(what)}</p>" if what else "") \
            + f'<p><a href="{html.escape(link)}">{esc(_t(lang, "details"))}</a></p><p>{esc(_t(lang, "sidebyside"))}</p>'
    else:
        informative = (_t(lang, "whatsnew") + "\n" + what + "\n\n" if what else "") + _t(lang, "sidebyside")
    box.setInformativeText(informative)
    install_button = box.addButton(_t(lang, "install"), QMessageBox.ButtonRole.AcceptRole)
    later_button = box.addButton(_t(lang, "later"), QMessageBox.ButtonRole.RejectRole)
    skip_button = box.addButton(_t(lang, "skip"), QMessageBox.ButtonRole.DestructiveRole)
    box.setDefaultButton(install_button)
    box.setEscapeButton(later_button)
    box.exec()
    clicked = box.clickedButton()
    return "install" if clicked is install_button else "skip" if clicked is skip_button else "later"


def install(parent, manifest, lang, download=None, launch=None):
    """Downloads the installer with a progress bar, checks it, starts it. `download` and `launch` replace updates' (tests). Returns the bridge carrying the answer."""
    version = manifest["version"]
    dialog = QProgressDialog(_t(lang, "downloading", version=version), _t(lang, "cancel"), 0, 1000, parent)
    dialog.setWindowTitle(_t(lang, "title"))
    dialog.setWindowModality(Qt.WindowModality.WindowModal)
    dialog.setMinimumDuration(0)
    dialog.setAutoClose(False)
    dialog.setAutoReset(False)
    dialog.setValue(0)
    cancelled = threading.Event()
    dialog.canceled.connect(cancelled.set)
    bridge = _Bridge()
    _KEEP.append(bridge)
    bridge.progress.connect(lambda done, total: dialog.setValue(int(1000 * done / total)) if total else None)

    def finished(path, error):
        dialog.close()
        if error is not None and getattr(error, "code", "") == "cancelled":
            return
        if error is None:
            try:
                (launch or updates.launch)(path)
            except OSError as exc:
                error = updates.UpdateError(str(exc), "launch", error=str(exc))
        if error is None:
            notices_ui.tell(_t(lang, "started", version=version), notifications.INFO, source="update_gui")
            return
        code = getattr(error, "code", "network")
        reason = _t(lang, f"reason_{code}", **{"error": getattr(error, "detail", {}).get("error", str(error))}) if f"reason_{code}" in STRINGS[lang] else str(error)
        notices_ui.tell(_t(lang, "failed", reason=reason, page=updates.page(manifest, lang) or updates.feed_url().rsplit("/", 1)[0] + "/"), notifications.CRITICAL, exc=error, source="update_gui")

    bridge.done.connect(finished)

    def work():
        try:
            path = (download or updates.download)(manifest, progress=lambda d, t: bridge.progress.emit(d, t), cancelled=cancelled.is_set)
            bridge.done.emit(path, None)
        except updates.UpdateError as exc:
            bridge.done.emit(None, exc)
        except Exception as exc:  # broad: said in a box rather than lost in a thread
            bridge.done.emit(None, updates.UpdateError(str(exc), "network", error=str(exc)))

    threading.Thread(target=work, daemon=True).start()
    dialog.show()
    return bridge
