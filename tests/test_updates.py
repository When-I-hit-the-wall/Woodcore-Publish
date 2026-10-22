"""An installed Woodcore asks the website whether a newer version is published, and installs it on a yes (calc/tools/updates.py, calc/tools/update_gui.py, docs/ui/window.md §10quater, docs/conventions/build-and-release.md §12, v0.89).

What is held: the manifest is read only when it has its shape and names an installer over HTTPS on its own host or exactly in Woodcore's Releases on GitHub (v0.117: the installer is too large for the site); a version is offered only when it is newer, not installed, not set aside and not put off for the day; the download is refused -- and leaves nothing behind -- where it is cut short, cancelled, or not the file the manifest states; a checkout and a test run ask nothing; and the window's question, its three answers and its install, driven off-screen with the network and the installer replaced. A real HTTP server on 127.0.0.1 stands in for the site, so the network code is the one that runs.
"""

TIER = "fast"  # tests/run_tests.py --fast

import hashlib
import http.server
import json
import os
import sys
import threading
import time
from pathlib import Path

import conftest
from conftest import ROOT

TOOLS = ROOT / "calc" / "tools"
PACKAGING = ROOT / "packaging"
for path in (TOOLS, PACKAGING):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import launcher  # noqa: E402
import updates  # noqa: E402
import usersettings  # noqa: E402

PAYLOAD = b"MZ-this-is-not-an-installer" * 1000
DIGEST = hashlib.sha256(PAYLOAD).hexdigest()


RELEASES = "https://github.com" + updates.INSTALLER_PREFIX


def _manifest(version="9.1.0", url=RELEASES + "v9.1.0/Woodcore-9.1.0-setup.exe", **installer):
    data = {"url": url, "sha256": DIGEST, "size": len(PAYLOAD)}
    data.update(installer)
    return {"schema_version": updates.SCHEMA_VERSION, "version": version, "installer": data,
            "notes": {"fr": "Nouveau.", "de": "Neu.", "en": "New."}}


class _Site:
    """A little website on 127.0.0.1: serves `files` by path and counts what is asked for."""

    def __init__(self, files):
        self.files, self.asked, self.redirects = files, [], {}
        site = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                site.asked.append(self.path)
                if self.path in site.redirects:   # what GitHub does with a release asset: an answer that sends on to a signed address
                    self.send_response(302)
                    self.send_header("Location", site.redirects[self.path])
                    self.end_headers()
                    return
                body = site.files.get(self.path)
                if body is None:
                    self.send_response(404)
                    self.end_headers()
                    return
                self.send_response(200)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args):
                pass

        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"

    def close(self):
        self.server.shutdown()
        self.server.server_close()


# --- what is asked, and when ---------------------------------------------------------------------------------

def test_the_updates_look_where_the_launcher_installs():
    assert updates.INSTALL_ROOT == launcher.INSTALL_ROOT
    for text in ("0.89.0", "0.9.10", "1.0.0", "0.89"):
        assert updates.version_tuple(text) == launcher.version_tuple(text)
    assert updates.version_tuple("0.89.0") < updates.version_tuple("0.89.1") < updates.version_tuple("0.90.0")


def test_the_feed_is_the_website_s_own_manifest():
    import importlib.util
    spec = importlib.util.spec_from_file_location("website_build", ROOT / "website" / "build.py")
    site = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(site)
    assert updates.FEED_URL == site.CONFIG["base_url"] + "version.json"
    assert site.MANIFEST_SCHEMA == updates.SCHEMA_VERSION
    assert updates.INSTALLER_HOST == "github.com"
    assert updates.INSTALLER_PREFIX == f"/{site.CONFIG['releases_repo']}/releases/download/", "the program's own list of where an installer may come from is the site's releases repository"


def test_a_checkout_and_a_test_run_ask_nothing_unless_told_to():
    saved = os.environ.pop(updates.ENV_CHECK, None)
    try:
        assert not updates.enabled({}), "a checkout (not frozen) must not ask"
        os.environ[updates.ENV_CHECK] = "1"
        assert updates.enabled({})
        assert not updates.enabled({"updates": {"enabled": False}}), "the settings may turn it off"
        os.environ[updates.ENV_CHECK] = "0"
        sys.frozen = True
        try:
            assert not updates.enabled({}), "0 wins even in an installed program"
            del os.environ[updates.ENV_CHECK]
            assert updates.enabled({}), "an installed program asks"
        finally:
            del sys.frozen
    finally:
        os.environ.pop(updates.ENV_CHECK, None)
        if saved is not None:
            os.environ[updates.ENV_CHECK] = saved


def test_a_manifest_is_acted_on_only_with_its_shape_and_its_own_host():
    feed = updates.FEED_URL
    assert updates.validate(_manifest(), feed) == []
    bad = {
        "http": _manifest(url="http://woodcore.pages.dev/x.exe"),
        "elsewhere": _manifest(url="https://example.com/x.exe"),
        "version": _manifest(version="0.89"),
        "sha": _manifest(sha256="abc"),
        "size": _manifest(size=0),
    }
    for name, manifest in bad.items():
        assert updates.validate(manifest, feed), f"{name}: accepted"
    wrong = _manifest()
    wrong["schema_version"] = "2.0"
    assert updates.validate(wrong, feed)
    assert updates.validate([], feed) == ["not a JSON object"]


def test_an_installer_may_come_from_the_site_or_from_woodcore_s_releases_and_from_nowhere_else():
    feed = updates.FEED_URL
    asset = RELEASES + "v9.1.0/Woodcore-9.1.0-setup.exe"
    for url in (asset, "https://woodcore.pages.dev/download/Woodcore-9.1.0-setup.exe"):
        assert updates.installer_address_problem(url, feed) == "", url
        assert updates.validate(_manifest(url=url), feed) == [], url
    refused = {
        "http": asset.replace("https://", "http://"),
        "a look-alike host": asset.replace("github.com", "github.com.evil.example"),
        "a user name that names github.com": asset.replace("https://github.com", "https://github.com@evil.example"),
        "a port": asset.replace("github.com", "github.com:8443"),
        "another repository": asset.replace("woodcore-releases", "other-releases"),
        "another account": asset.replace("When-I-hit-the-wall", "someone-else"),
        "another case of the account": asset.replace("When-I-hit-the-wall", "when-i-hit-the-wall"),
        "a parent folder": RELEASES + "../../../evil/x.exe",
        "an encoded parent folder": RELEASES + "%2e%2e/x.exe",
        "an encoded separator": RELEASES + "v9%2F..%2Fx.exe",
        "a backslash": RELEASES + "v9\\x.exe",
        "a query": asset + "?token=1",
        "a fragment": asset + "#x",
        "a raw file": asset.replace("https://github.com", "https://raw.githubusercontent.com"),
        "nothing after the folder": RELEASES,
        "the repository's page": "https://github.com/When-I-hit-the-wall/woodcore-releases",
        "a missing address": None,
    }
    for name, url in refused.items():
        assert updates.installer_address_problem(url, feed), f"{name}: accepted"
        assert updates.validate(_manifest(url=url), feed), f"{name}: the manifest was accepted"


def test_a_version_is_offered_once_newer_not_installed_not_set_aside_nor_put_off():
    root = conftest.tmpdir("updates_installed")
    manifest = _manifest("9.1.0")
    assert updates.offer(manifest, "0.89.0", {}, root=root)
    assert not updates.offer(manifest, "9.1.0", {}, root=root), "the same version"
    assert not updates.offer(manifest, "9.2.0", {}, root=root), "an older one"
    assert not updates.offer(None, "0.89.0", {}, root=root)
    (root / "9.1.0").mkdir()
    (root / "9.1.0" / "Woodcore.exe").write_bytes(b"")
    assert not updates.offer(manifest, "0.89.0", {}, root=root), "installed already: the launcher starts it"
    (root / "9.1.0" / "Woodcore.exe").unlink()
    settings = updates.skip({}, "9.1.0")
    assert not updates.offer(manifest, "0.89.0", settings, root=root)
    assert updates.offer(_manifest("9.2.0"), "0.89.0", settings, root=root), "the next one is offered"
    now = 1_000_000.0
    settings = updates.snooze({}, "9.1.0", now=now)
    assert not updates.offer(manifest, "0.89.0", settings, now=now + 3600, root=root)
    assert updates.offer(manifest, "0.89.0", settings, now=now + 25 * 3600, root=root), "put off for a day, not for ever"
    assert updates.offer(_manifest("9.2.0"), "0.89.0", settings, now=now + 3600, root=root), "a snooze is for its own version"


def test_the_manifest_is_read_from_the_site_and_nothing_is_said_when_it_cannot_be():
    site = _Site({})
    try:
        manifest = _manifest(url=site.base.replace("http", "https") + "/download/Woodcore-9.1.0-setup.exe")
        site.files["/version.json"] = json.dumps(manifest).encode()
        site.files["/broken.json"] = b"{ not json"
        site.files["/other.json"] = json.dumps(_manifest(url="https://example.com/x.exe")).encode()
        assert updates.fetch(site.base + "/version.json") == manifest
        assert updates.fetch(site.base + "/missing.json") is None
        assert updates.fetch(site.base + "/broken.json") is None
        assert updates.fetch(site.base + "/other.json") is None, "an installer on another host is refused"
    finally:
        site.close()
    assert updates.fetch("http://127.0.0.1:9/version.json", timeout=1) is None, "no server: no answer, no exception"


def test_the_download_checks_the_file_and_leaves_nothing_that_is_not_it():
    site = _Site({"/good.exe": PAYLOAD, "/short.exe": PAYLOAD[:-5], "/other.exe": PAYLOAD[::-1]})
    folder = conftest.tmpdir("updates_download")
    try:
        seen = []
        path = updates.download(_manifest(url=site.base + "/good.exe"), folder=folder, progress=lambda d, t: seen.append((d, t)))
        assert path.read_bytes() == PAYLOAD and seen[-1] == (len(PAYLOAD), len(PAYLOAD))
        asked = len(site.asked)
        assert updates.download(_manifest(url=site.base + "/good.exe"), folder=folder) == path
        assert len(site.asked) == asked, "downloaded before: not downloaded again"
        for name, code in (("short", "size"), ("other", "sha256")):
            try:
                updates.download(_manifest(url=f"{site.base}/{name}.exe"), folder=folder)
            except updates.UpdateError as exc:
                assert exc.code == code
            else:
                raise AssertionError(f"{name}: a file that is not the one stated was accepted")
            assert not (folder / f"{name}.exe").exists() and not (folder / f"{name}.exe.part").exists()
        try:
            updates.download(_manifest(url=site.base + "/missing.exe"), folder=folder)
        except updates.UpdateError as exc:
            assert exc.code == "network"
        else:
            raise AssertionError("a 404 was taken for an installer")
        (folder / "good.exe").unlink()
        try:
            updates.download(_manifest(url=site.base + "/good.exe"), folder=folder, cancelled=lambda: True)
        except updates.UpdateError as exc:
            assert exc.code == "cancelled"
        else:
            raise AssertionError("a cancelled download went on")
        assert not list(folder.iterdir()), "a cancelled download leaves nothing"
    finally:
        site.close()


def test_a_download_follows_the_redirect_of_a_release_but_never_out_of_https():
    site = _Site({"/signed/good.exe": PAYLOAD})
    site.redirects["/download/good.exe"] = "/signed/good.exe"
    folder = conftest.tmpdir("updates_redirect")
    try:
        path = updates.download(_manifest(url=site.base + "/download/good.exe"), folder=folder)
        assert path.name == "good.exe" and path.read_bytes() == PAYLOAD, "the file is named after the address the manifest gives, not the one it was sent on to"
        assert site.asked == ["/download/good.exe", "/signed/good.exe"]
    finally:
        site.close()

    class Answer:
        """What urlopen returns for an https address that GitHub sent on to a plain http one."""
        def __init__(self, final):
            self.final = final

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def geturl(self):
            return self.final

        def read(self, count=-1):
            return b""

    real = updates.urllib.request.urlopen
    try:
        updates.urllib.request.urlopen = lambda request, timeout=None: Answer("http://downgraded.example/x.exe")
        try:
            updates.download(_manifest(), folder=folder)
        except updates.UpdateError as exc:
            assert exc.code == "network" and "HTTPS" in str(exc), exc
        else:
            raise AssertionError("an installer fetched over http after an https address was accepted")
        assert not list(folder.glob("*.part")), "and nothing is left behind"
    finally:
        updates.urllib.request.urlopen = real


def test_the_downloads_go_outside_the_project():
    assert updates.download_dir() == usersettings.cache_dir("updates")


def test_the_page_of_what_changes_is_offered_only_on_the_site_s_own_host():
    feed = updates.FEED_URL
    base = feed.rsplit("/", 1)[0]
    manifest = _manifest()
    assert updates.changes(manifest, "fr", feed) == ""
    manifest["changes"] = {"fr": base + "/fr/changes/9.1.0/", "en": base + "/en/changes/9.1.0/"}
    assert updates.changes(manifest, "fr", feed).endswith("/fr/changes/9.1.0/")
    assert updates.changes(manifest, "de", feed).endswith("/en/changes/9.1.0/"), "another language falls back to English"
    manifest["changes"] = {"fr": "https://example.com/fr/", "en": base.replace("https", "http") + "/en/"}
    assert updates.changes(manifest, "fr", feed) == "" and updates.changes(manifest, "en", feed) == ""


# --- the window ---------------------------------------------------------------------------------------------

def _qt():
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:
        raise conftest.Skip(f"PySide6 is not installed ({exc})")
    return QApplication.instance() or QApplication([])


def test_the_window_speaks_three_languages_and_has_a_sentence_for_every_refusal():
    _qt()
    import update_gui
    keys = set(update_gui.STRINGS["en"])
    for lang in update_gui.LANGUAGES:
        assert set(update_gui.STRINGS[lang]) == keys, lang
        for code in ("network", "size", "sha256", "launch"):
            assert f"reason_{code}" in update_gui.STRINGS[lang]
        assert "ß" not in "".join(update_gui.STRINGS["de"].values())


def test_the_window_asks_nothing_where_the_updates_are_off():
    app = _qt()
    import update_gui
    saved = os.environ.pop(updates.ENV_CHECK, None)
    try:
        assert update_gui.schedule(app, fetch=lambda: _manifest()) is None
    finally:
        if saved is not None:
            os.environ[updates.ENV_CHECK] = saved


def test_the_start_asks_once_the_window_is_up():
    source = conftest.module_source(TOOLS / "woodcore_gui.py")   # with the parts split out of it (issue #30)
    assert "update_gui.schedule(app)" in source
    main = source[source.index("def main("):]   # main(app=None, argv=None, watching=False) since v0.117
    assert main.index("if self_test:") < main.index("update_gui.schedule(app)"), "--self-test asks nothing"


def _answer(app, label):
    """Clicks the button named `label` of the modal box once it is up."""
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QMessageBox

    def click():
        box = app.activeModalWidget()
        if isinstance(box, QMessageBox):
            for button in box.buttons():
                if button.text() == label:
                    button.click()
                    return
        QTimer.singleShot(20, click)

    QTimer.singleShot(20, click)


def test_the_question_s_three_answers():
    app = _qt()
    import update_gui
    from PySide6.QtWidgets import QWidget
    parent = QWidget()
    for lang in update_gui.LANGUAGES:
        for key, expected in (("install", "install"), ("later", "later"), ("skip", "skip")):
            _answer(app, update_gui.STRINGS[lang][key])
            assert update_gui.ask(parent, _manifest(), "0.89.0", lang) == expected, (lang, key)


def test_the_question_links_to_what_the_version_changes():
    _qt()
    import update_gui
    from PySide6.QtWidgets import QLabel, QMessageBox
    seen = {}
    real_exec = QMessageBox.exec

    def look(box):
        seen["labels"] = [(label.text(), label.openExternalLinks()) for label in box.findChildren(QLabel)]
        return 0

    QMessageBox.exec = look
    try:
        manifest = _manifest()
        manifest["notes"]["fr"] = "Nouveau <b> & ceci."
        manifest["changes"] = {"fr": updates.FEED_URL.rsplit("/", 1)[0] + "/fr/changes/9.1.0/"}
        update_gui.ask(None, manifest, "0.89.0", "fr")
        linked = [(text, opens) for text, opens in seen["labels"] if "href" in text]
        assert linked and linked[0][1], "the link is shown and opens in the browser"
        assert manifest["changes"]["fr"] in linked[0][0] and "&lt;b&gt; &amp; ceci" in linked[0][0], "the notes are escaped, not read as markup"
        update_gui.ask(None, _manifest(), "0.89.0", "fr")
        assert not any("href" in text for text, _ in seen["labels"]), "no page, no link"
    finally:
        QMessageBox.exec = real_exec


def test_skip_and_later_are_remembered_and_install_downloads_then_starts():
    app = _qt()
    import update_gui
    from PySide6.QtCore import QEventLoop, QTimer
    from PySide6.QtWidgets import QMessageBox, QWidget

    usersettings.write({"lang": "en"})
    parent = QWidget()
    parent.show()
    real_ask, real_info, real_warn = update_gui.ask, QMessageBox.information, QMessageBox.warning
    said = []
    try:
        root = conftest.tmpdir("updates_gui_root")
        real_offer = updates.offer
        updates.offer = lambda m, c, s, now=None, root_=None: real_offer(m, c, s, now=now, root=root)
        update_gui.ask = lambda *a: "skip"
        update_gui._announce(app, _manifest("9.1.0"), "0.89.0")
        assert usersettings.read()["updates"]["skipped"] == "9.1.0"
        update_gui.ask = lambda *a: "later"
        update_gui._announce(app, _manifest("9.2.0"), "0.89.0")
        assert usersettings.read()["updates"]["snoozed"]["version"] == "9.2.0"
        update_gui.ask = lambda *a: (_ for _ in ()).throw(AssertionError("asked about a version set aside"))
        update_gui._announce(app, _manifest("9.1.0"), "0.89.0")

        # said as notices since v0.117 -- an information, then a critical failure --, never in a box (calc/notifications.py)
        import notifications
        notifications.STORE.clear()

        # heard as they are reported: a window another test left open delivers an information to its status line and takes it out of the store
        heard = []
        listening = conftest.notices_said(lambda notice: heard.append((notice.severity, notice.text)))
        listening.__enter__()

        def said_last():
            return heard[-1] if heard else None
        launched = []
        loop = QEventLoop()
        bridge = update_gui.install(parent, _manifest("9.3.0"), "en",
                                    download=lambda m, progress, cancelled: (progress(5, 10), Path("setup.exe"))[1],
                                    launch=launched.append)
        bridge.done.connect(lambda *a: QTimer.singleShot(0, loop.quit))
        QTimer.singleShot(5000, loop.quit)
        loop.exec()
        assert launched == [Path("setup.exe")]
        assert said_last() is not None and said_last()[0] == "info" and "9.3.0" in said_last()[1]

        def refused(m, progress, cancelled):
            raise updates.UpdateError("bad", "sha256")
        loop = QEventLoop()
        bridge = update_gui.install(parent, _manifest("9.3.0"), "fr", download=refused, launch=launched.append)
        bridge.done.connect(lambda *a: QTimer.singleShot(0, loop.quit))
        QTimer.singleShot(5000, loop.quit)
        loop.exec()
        assert said_last()[0] == "critical" and "SHA-256" in said_last()[1] and len(launched) == 1
    finally:
        if "listening" in locals():
            listening.__exit__(None, None, None)
        update_gui.ask, updates.offer = real_ask, real_offer
        QMessageBox.information, QMessageBox.warning = real_info, real_warn
        import notifications
        notifications.STORE.clear()
        usersettings.write({"lang": "en"})
        parent.close()
