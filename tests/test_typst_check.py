"""Typst checked at every start of Woodcore run from its sources (calc/tools/typst_check.py, typst_gui.py; v0.94, docs/ui/window.md §10quater, docs/conventions/testing.md §11ter).

The Typst found is compared with the one requirements.txt pins, offline -- a modal only where it is missing or another version --, GitHub is asked in a thread for a newer one -- a banner only where there is one, nothing at all where the network does not answer --, and installing is winget's, on a yes, a newer version then pinned in requirements.txt and .github/workflows/site.yml at once, so that tests/test_site.py's equality between the two still holds. An installed Woodcore asks nothing.

Nothing here installs or downloads anything: every subprocess and every request is replaced, and the pin is rewritten in copies of the two files, never in the real ones.
"""

TIER = "fast"  # tests/run_tests.py --fast

import contextlib
import io
import json
import os
import re
import shutil
import sys
import urllib.error

import conftest
from conftest import ROOT

TOOLS = ROOT / "calc" / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import typst_check  # noqa: E402

# What `winget list --id Typst.Typst -e` printed on the engineer's machine on 24.09.2026, where the Typst on the PATH (C:\Program Files (x86)\typst) was installed otherwise -- and what it prints for a package winget manages (read off `winget list --id Git.Git -e` the same day, the id changed).
WINGET_NONE = "   - \r   \\ \r                                                                                                                        \rNo installed package found matching input criteria.\r\n"
WINGET_MANAGED = "   - \r   \\ \r\rName  Id          Version Available Source\r\n-------------------------------------------\r\nTypst Typst.Typst 0.13.1  0.14.2    winget\r\n"


class _Run:
    """A stand-in for subprocess.run: what each command answers, and the commands it was given."""

    def __init__(self, answers):
        self.answers = answers
        self.calls = []

    def __call__(self, command, **_kwargs):
        self.calls.append([str(part) for part in command])
        for key, answer in self.answers.items():
            if key in " ".join(str(part) for part in command):
                if isinstance(answer, BaseException):
                    raise answer
                code, out = answer
                return type("Done", (), {"returncode": code, "stdout": out, "stderr": ""})()
        raise OSError("no such program")


_MISSING = object()


@contextlib.contextmanager
def _patched(obj, **values):
    """`obj`'s attributes set to `values` for the length of a block, and put back after -- taken away again where `obj` had none (`sys.frozen`)."""
    saved = {name: getattr(obj, name, _MISSING) for name in values}
    for name, value in values.items():
        setattr(obj, name, value)
    try:
        yield
    finally:
        for name, value in saved.items():
            if value is _MISSING:
                delattr(obj, name)
            else:
                setattr(obj, name, value)


@contextlib.contextmanager
def _env(**values):
    saved = {name: os.environ.get(name) for name in values}
    for name, value in values.items():
        if value is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = value
    try:
        yield
    finally:
        for name, value in saved.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


def _copies(name):
    """A copy of typst-version.txt in this process's own folder: what a pin is written into here."""
    folder = conftest.tmpdir(name)
    shutil.copyfile(typst_check.VERSION_FILE, folder / typst_check.VERSION_FILE.name)
    return folder / typst_check.VERSION_FILE.name


# --- the version, the pin ----------------------------------------------------------------------

def test_a_version_is_read_off_what_typst_prints():
    assert typst_check.parse_version("typst 0.14.2 (b33de9de)\n") == "0.14.2"
    assert typst_check.parse_version("typst 0.15.0") == "0.15.0"
    assert typst_check.parse_version("") is None and typst_check.parse_version("command not found") is None


def test_the_pin_is_read_from_typst_version_txt_its_one_source():
    """v0.117, issue #26: the pinned Typst is written once, in typst-version.txt; every other file reads it (packaging/build.py, packaging/notices.py, tests/bootstrap.py, the workflows), and no second copy of the number is left to age."""
    pinned = typst_check.pinned()
    assert pinned and re.fullmatch(r"\d+\.\d+\.\d+", pinned), pinned
    assert typst_check.VERSION_FILE.read_text(encoding="utf-8") == pinned + "\n", "typst-version.txt holds the version alone"
    root = typst_check.ROOT
    assert 'TYPST_VERSION = (ROOT / "typst-version.txt")' in (root / "packaging" / "build.py").read_text(encoding="utf-8")
    assert "typst-version.txt" in (root / "packaging" / "notices.py").read_text(encoding="utf-8")
    # the number itself, nowhere else among the files that configure, build or test -- the history (CHANGELOG, docs/, the specs) and the legal notices name the version they were written for
    allowed = {"typst-version.txt", "typst-sha256.json"}
    places = [p for p in (root / "requirements.txt", root / "packaging" / "build.py", root / "packaging" / "notices.py", *(root / ".github" / "workflows").glob("*.yml"), root / "tests" / "bootstrap.py", root / "calc" / "tools" / "typst_check.py")]
    stated = [p.name for p in places if p.name not in allowed and pinned in p.read_text(encoding="utf-8")]
    assert not stated, f"Typst {pinned} written in {stated}: typst-version.txt is its one source"


# The version a pin is written to below. Deliberately one the repository will never pin: `pin()` rewrites only what differs, so pinning the version already
# pinned writes nothing and gives back [] -- which is how this test failed the day the machine's Typst moved to 0.15.1, the literal it used to carry.
NOT_THE_PIN = "0.99.9"


def test_a_pin_rewrites_typst_version_txt_alone_and_refuses_what_is_not_a_version():
    version_file = _copies("typst_pin")
    assert typst_check.pinned() != NOT_THE_PIN, "NOT_THE_PIN is what the repository pins: choose another"
    assert typst_check.pin(NOT_THE_PIN, version_file) == [version_file]
    assert typst_check.pinned(version_file) == NOT_THE_PIN and version_file.read_bytes() == NOT_THE_PIN.encode() + b"\n"
    assert typst_check.pin(NOT_THE_PIN, version_file) == [], "pinning the version pinned writes nothing"
    for wrong in ("", "latest", "v0.15.1 "):
        try:
            typst_check.pin(wrong, version_file)
        except typst_check.PinError:
            pass
        else:
            raise AssertionError(f"{wrong!r} was pinned")
    assert typst_check.pinned(version_file) == NOT_THE_PIN, "a refused pin wrote something"
    version_file.write_text("not a version\n", encoding="utf-8")
    assert typst_check.pinned(version_file) is None, "a file naming no version pins nothing"


def test_the_typst_found_against_the_pin():
    requirements = _copies("typst_state")
    pinned = typst_check.pinned(requirements)
    assert typst_check.state(_Run({"--version": (0, f"typst {pinned} (abc)")}), requirements) == ("ok", pinned, pinned)
    assert typst_check.state(_Run({"--version": (0, "typst 0.12.0 (abc)")}), requirements) == ("other", "0.12.0", pinned)
    assert typst_check.state(_Run({"--version": OSError("not found")}), requirements) == ("missing", None, pinned)
    assert typst_check.state(_Run({"--version": (1, "")}), requirements) == ("missing", None, pinned)
    requirements.write_text("openpyxl==3.1.5\n", encoding="utf-8")
    assert typst_check.state(_Run({"--version": (0, "typst 0.12.0")}), requirements)[0] == "unpinned", "a file naming no Typst asks nothing"


# --- GitHub ------------------------------------------------------------------------------------------

class _Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


def test_github_s_latest_release_and_silence_on_any_failure():
    asked = []

    def opener(request, timeout):
        asked.append((request.full_url, timeout))
        return _Response(json.dumps({"tag_name": "v0.15.0"}).encode())

    assert typst_check.latest(opener=opener) == "0.15.0" and asked[0][0] == typst_check.RELEASES_API
    for failing in (urllib.error.URLError("no network"), TimeoutError("slow proxy"), OSError("refused")):
        def broken(request, timeout, failing=failing):
            raise failing
        assert typst_check.latest(opener=broken) is None
    assert typst_check.latest(opener=lambda r, timeout: _Response(b"<html>rate limited</html>")) is None
    assert typst_check.latest(opener=lambda r, timeout: _Response(b'{"message": "API rate limit exceeded"}')) is None
    assert typst_check.latest(opener=lambda r, timeout: _Response(b'{"tag_name": "v0.15.0-rc.1"}')) is None, "a pre-release is not offered"
    requirements = _copies("typst_update")
    pinned = typst_check.pinned(requirements)
    assert typst_check.update(requirements, fetch=lambda: "99.0.0") == "99.0.0"
    assert typst_check.update(requirements, fetch=lambda: pinned) is None
    assert typst_check.update(requirements, fetch=lambda: "0.1.0") is None, "an older Typst was offered"
    assert typst_check.update(requirements, fetch=lambda: None) is None


def test_an_installed_woodcore_asks_nothing_and_the_suite_nothing_either():
    with _env(WOODCORE_TYPST_CHECK=None), _patched(sys, frozen=True):
        assert not typst_check.enabled()
    with _env(WOODCORE_TYPST_CHECK="0"):
        assert not typst_check.enabled()
    with _env(WOODCORE_TYPST_CHECK=None):
        assert typst_check.enabled(), "from the sources the check runs"
    assert os.environ.get("WOODCORE_TYPST_CHECK") == "0", "conftest.py no longer stands the check down for the suite's windows"


# --- winget -------------------------------------------------------------------------------------------

def test_what_winget_list_says_is_read():
    assert typst_check.parse_winget_list(WINGET_NONE) == (False, None)
    assert typst_check.parse_winget_list(WINGET_MANAGED) == (True, "0.13.1")
    assert typst_check.parse_winget_list("") == (False, None)
    run = _Run({"list --id Typst.Typst -e": (0, WINGET_MANAGED)})
    with _patched(typst_check, winget=lambda: r"C:\winget.exe"):
        assert typst_check.winget_list(run) == (True, "0.13.1")
        assert run.calls == [[r"C:\winget.exe", "list", "--id", "Typst.Typst", "-e"]], "winget list was asked otherwise than read-only"
        assert typst_check.winget_list(_Run({"list": (20, WINGET_NONE)})) == (False, None)
        assert typst_check.winget_list(_Run({"list": OSError("gone")})) == (False, None)
    with _patched(typst_check, winget=lambda: None):
        assert typst_check.winget_list(_Run({})) == (False, None), "winget was run where there is none"


def test_the_winget_command_is_upgrade_where_winget_manages_an_older_typst_else_install():
    with _patched(typst_check, winget=lambda: "winget"):
        agreed = ["--accept-package-agreements", "--accept-source-agreements", "--disable-interactivity"]
        assert typst_check.install_command("0.15.0") == ["winget", "install", "--id", "Typst.Typst", "-e", "--version", "0.15.0", *agreed]
        assert typst_check.install_command("0.15.0", True, "0.14.2") == ["winget", "upgrade", "--id", "Typst.Typst", "-e", "--version", "0.15.0", *agreed]
        assert typst_check.install_command("0.14.2", True, "0.15.0") == ["winget", "install", "--id", "Typst.Typst", "-e", "--version", "0.14.2", *agreed, "--force"], "going back to the pin needs --force"


def test_after_installing_the_typst_first_on_the_path_is_said():
    base = conftest.tmpdir("typst_path")
    old, new, links = base / "Program Files" / "typst", base / "WinGet" / "Packages", base / "WinGet" / "Links"
    for folder in (old, new, links):
        folder.mkdir(parents=True)
    name = "typst.exe" if sys.platform == "win32" else "typst"
    (old / name).write_bytes(b"")
    (links / name).write_bytes(b"")
    run = _Run({str(old): (0, "typst 0.14.2"), str(links): (0, "typst 0.15.0")})
    with _patched(typst_check, winget_links=lambda: links):
        shadowed = typst_check.after_install("0.15.0", path=os.pathsep.join([str(old), str(new)]), run=run)
        assert not shadowed["ok"] and shadowed["first"] == (str(old / name), "0.14.2") and shadowed["found"] == str(links / name), shadowed
        first = typst_check.after_install("0.15.0", path=os.pathsep.join([str(links), str(old)]), run=run)
        assert first["ok"] and first["first"][0] == str(links / name)
        nowhere = typst_check.after_install("0.16.0", path=str(old), run=run)
        assert not nowhere["ok"] and nowhere["found"] is None


# --- the window's side ----------------------------------------------------------------------------

def _qt():
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:
        raise conftest.Skip(f"PySide6 is not installed ({exc})")
    return QApplication.instance() or QApplication([])


def _window():
    from PySide6.QtWidgets import QVBoxLayout, QWidget

    class Window(QWidget):
        lang = "en"

        def __init__(self):
            super().__init__()
            self.rebuilt = 0
            self.box = QVBoxLayout(self)

        def rebuild(self):
            self.rebuilt += 1

    return Window()


def _asked(window, answer, seconds=10):
    """typst_gui.ask_github with GitHub answering `answer` -- a version, None, or an exception raised -- and the loop run until the answer is back from its thread. The thread waits for the check to listen before it answers, or it could answer first and be missed."""
    import threading
    import typst_gui
    from PySide6.QtCore import QEventLoop, QTimer
    listening = threading.Event()

    def fetch():
        listening.wait(seconds)
        if isinstance(answer, BaseException):
            raise answer
        return answer

    bridge = typst_gui.ask_github(window, fetch=fetch)
    loop = QEventLoop()
    answered = []
    bridge.found.connect(lambda value: (answered.append(value), QTimer.singleShot(0, loop.quit)))
    listening.set()
    QTimer.singleShot(seconds * 1000, loop.quit)
    loop.exec()
    return answered


def test_a_modal_only_where_typst_is_missing_or_another_version():
    _qt()
    import typst_gui
    window = _window()
    asked = []
    for state, modal in ((("ok", "0.14.2", "0.14.2"), False), (("unpinned", "0.14.2", None), False),
                         (("missing", None, "0.14.2"), True), (("other", "0.12.0", "0.14.2"), True)):
        asked.clear()
        with _env(WOODCORE_TYPST_CHECK=None), \
                _patched(typst_check, state=lambda state=state, **_k: state), \
                _patched(typst_gui, ask_install=lambda *args: asked.append(args), ask_github=lambda window, fetch=None: None):
            typst_gui.check_at_start(window)
        assert bool(asked) == modal, (state, asked)
        if modal:
            assert asked[0][1:] == state
    # and an installed Woodcore, or the suite, asks nothing at all
    for env, frozen in ((None, True), ("0", False)):
        called = []
        with _env(WOODCORE_TYPST_CHECK=env), _patched(sys, frozen=frozen), \
                _patched(typst_check, state=lambda **_k: called.append("state") or ("missing", None, "0.14.2")), \
                _patched(typst_gui, ask_github=lambda *a, **k: called.append("github")):
            assert typst_gui.check_at_start(window) is None
        assert not called, (env, frozen, called)


def test_the_modal_s_later_installs_nothing_and_its_install_runs_winget():
    _qt()
    from PySide6.QtWidgets import QMessageBox
    import typst_gui
    window = _window()
    ran = []
    for answer, expected in (("Later", []), ("Install", [("0.14.2", False)])):
        ran.clear()

        def click(box, answer=answer):
            texts = {button.text(): button for button in box.buttons()}
            assert "0.12.0" in box.text() and "0.14.2" in box.text(), box.text()
            texts[answer].click()
            return 0

        with _patched(QMessageBox, exec=click), _patched(typst_gui, run_install=lambda w, version, pin_after: ran.append((version, pin_after)) or True):
            typst_gui.ask_install(window, "other", "0.12.0", "0.14.2")
        assert ran == expected, (answer, ran)


def test_a_banner_only_where_github_offers_a_newer_typst_and_silence_where_it_does_not_answer():
    _qt()
    import typst_gui
    window = _window()
    assert typst_gui.add_banner(window, window.box) is None, "a banner with nothing newer"
    assert _asked(window, urllib.error.URLError("no network")) == [None] and window.rebuilt == 0 and not getattr(window, "typst_update", None), "a failed request said something"
    assert _asked(window, typst_check.pinned()) == [None] and window.rebuilt == 0, "the pinned version was offered as newer"
    assert _asked(window, "99.0.0") == ["99.0.0"] and window.rebuilt == 1 and window.typst_update == "99.0.0"
    row = typst_gui.add_banner(window, window.box)
    texts = [row.itemAt(i).widget().text() for i in range(row.count())]
    assert any("99.0.0" in text and typst_check.pinned() in text for text in texts) and "Install Typst 99.0.0" in texts, texts
    assert row.itemAt(0).widget().property("callout") == "info", "the banner is not the packages' quieter blue"


def test_installing_runs_winget_shows_its_output_pins_a_newer_version_and_says_the_path():
    _qt()
    from PySide6.QtWidgets import QMessageBox
    import typst_gui
    window = _window()
    window.typst_update = "99.0.0"
    said, pinned = [], []
    program = [sys.executable, "-c", "print('Successfully installed')"]

    def finish(dialog):
        dialog.process.waitForFinished(30000)
        return 0

    stubs = dict(winget=lambda: "winget", winget_list=lambda run=None: (False, None), install_command=lambda version, managed, current: program,
                 pin=lambda version, *a: pinned.append(version) or [], after_install=lambda version, **k: {"ok": False, "first": (r"C:\Program Files (x86)\typst\typst.exe", "0.14.2"), "found": r"C:\Links\typst.exe"})
    dialogs = []
    real_exec = typst_gui.InstallDialog.exec
    heard = lambda notice: said.append(notice.text if notice.severity == "info" else ("warning", notice.text))   # noqa: E731 -- a notice since v0.117, no box
    with _patched(typst_check, **stubs), _patched(typst_gui.InstallDialog, exec=lambda dialog: dialogs.append(dialog) or finish(dialog)), \
            conftest.notices_said(heard):
        assert typst_gui.run_install(window, "99.0.0", pin_after=True)
    assert typst_gui.InstallDialog.exec is real_exec
    output = dialogs[0].output.toPlainText()
    assert "Successfully installed" in output and output.startswith(">"), output
    assert pinned == ["99.0.0"] and window.typst_update is None and window.rebuilt == 1
    assert "requirements.txt" in said[0] and r"C:\Program Files (x86)\typst\typst.exe" in said[0] and "Start Woodcore again" in said[0], said
    # the pinned version installed from the modal: nothing pinned; and winget failing says so
    said.clear()
    pinned.clear()
    failing = [sys.executable, "-c", "import sys; print('0x8a150014'); sys.exit(3)"]
    with _patched(typst_check, **dict(stubs, install_command=lambda *a: failing)), _patched(typst_gui.InstallDialog, exec=finish), \
            conftest.notices_said(heard):
        assert not typst_gui.run_install(window, "0.14.2", pin_after=False)
    assert not pinned and said and said[0][0] == "warning" and "3" in said[0][1], said
    # no winget: said, with Typst's releases page, and nothing run
    shown = []
    with _patched(typst_check, winget=lambda: None, winget_list=lambda run=None: shown.append("list")), \
            conftest.notices_said(lambda notice: shown.append(notice)):
        assert not typst_gui.run_install(window, "0.14.2", pin_after=False)
    assert len(shown) == 1 and shown[0].severity == "warning" and typst_check.RELEASES_PAGE in shown[0].text + shown[0].technical, shown


def test_the_typst_window_speaks_three_languages():
    _qt()
    import typst_gui
    keys = set(typst_gui.STRINGS["fr"])
    for lang in ("de", "en"):
        assert set(typst_gui.STRINGS[lang]) == keys, lang
    assert not any("ß" in text for text in typst_gui.STRINGS["de"].values()), "Swiss German writes no ß"
    for key, text in typst_gui.STRINGS["fr"].items():
        assert not re.search(r"\S[:;?!](\s|$)", text.replace("://", "")), f"French puts a space before a colon: {key}"
