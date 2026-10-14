"""Typst, checked at every start of Woodcore run from its sources (docs/conventions/testing.md §11ter, v0.94).

The engineer: «à chaque lancement du katalog, il faut vérifier si la dernière version de typst est installée et proposer de le faire si ce n'est pas le cas». Typst is a binary and not a Python package, so the version the report is verified with is written in one file of its own, `typst-version.txt` at the root (v0.117, issue #26): tests/bootstrap.py installs it, packaging/build.py ships it, .github/workflows/site.yml and tests.yml compile with it, and every one of them reads that file rather than a copy. Until v0.117 the number was written three times -- requirements.txt's comment, site.yml's `TYPST_VERSION`, build.py's -- and held equal by this module rewriting all three. Two questions, dependencies.py's own two, kept apart for the same reason:

* **Is the Typst found the one pinned?** `typst --version` of project.typst_executable(): offline, instant, and a Typst missing or another than the pin is worth a modal -- a report compiled with another Typst is not the report verified.
* **Is there a newer Typst?** GitHub's latest release, in a thread, silent on any failure, and only ever an offer: a banner.

Installing is winget's (`Typst.Typst`), and only on the engineer's yes (calc/tools/typst_gui.py). `winget list` says first whether the Typst there is winget's own -- the one this machine had was installed otherwise, in `C:\\Program Files (x86)\\typst`, and winget did not know it -- which decides between `winget upgrade` and `winget install`. Installing a newer version rewrites the pin, typst-version.txt (`pin`): installing without pinning is the very mismatch the first question reports, from the other side. The SHA-256 of the new version's archives are not known here: typst-sha256.json is brought along by `python tests/bootstrap.py --record-hashes`, and tests/test_bootstrap.py refuses a pin that has none. A Typst winget installs goes into winget's own Links folder, which the Typst installed otherwise may come before on the PATH, so `after_install` says which Typst a new process will find.

An installed Woodcore asks nothing: it carries the Typst it was built with (project.typst_executable), and `enabled()` says so; `WOODCORE_TYPST_CHECK=0` stops the check from the sources too, which the test suite does.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

import dependencies
import proc
import project

ROOT = project.APP_ROOT
VERSION_FILE = ROOT / "typst-version.txt"
ENV = "WOODCORE_TYPST_CHECK"
WINGET_ID = "Typst.Typst"
RELEASES_API = "https://api.github.com/repos/typst/typst/releases/latest"
RELEASES_PAGE = "https://github.com/typst/typst/releases"
# How long to wait on GitHub: the answer is a convenience, and a window that waits on a slow proxy is worse than no answer (dependencies.PYPI_TIMEOUT's reason).
TIMEOUT = 4.0
WINGET_TIMEOUT = 90

_VERSION = re.compile(r"\d+\.\d+(?:\.\d+)*")


class PinError(Exception):
    """A version that cannot be pinned: not of the shape `1.2.3`, or a typst-version.txt that cannot be written."""


def enabled():
    """Whether this process checks Typst at all: from the sources yes, unless `WOODCORE_TYPST_CHECK=0`; an installed Woodcore never, the Typst it compiles with being the one it ships."""
    return not getattr(sys, "frozen", False) and os.environ.get(ENV) != "0"


def _read(path):
    with open(path, encoding="utf-8", newline="") as f:
        return f.read()


def pinned(version_file=None):
    """The Typst typst-version.txt names -- `1.2.3` -- or None where the file is not there or holds no version alone."""
    try:
        text = _read(Path(version_file or VERSION_FILE)).strip()
    except OSError:
        return None
    return text if _VERSION.fullmatch(text) else None


def parse_version(output):
    """`typst 0.14.2 (b33de9de)` -> `0.14.2`; None where the text carries no version."""
    found = _VERSION.search(output or "")
    return found.group(0) if found else None


def installed(executable=None, run=proc.run):
    """The version of the Typst `executable` is -- project.typst_executable() by default -- or None where none answers."""
    try:
        out = run([str(executable or project.typst_executable()), "--version"], capture_output=True, text=True,
                  encoding="utf-8", errors="replace", timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    return parse_version(out.stdout) if out.returncode == 0 else None


def state(run=proc.run, version_file=None):
    """(what, found, wanted): "ok" where the Typst found is the one pinned, "missing" where none answers, "other" where it is another version -- and "unpinned" where typst-version.txt names none, which asks nothing."""
    wanted = pinned(version_file)
    found = installed(run=run)
    if wanted is None:
        return "unpinned", found, None
    if found is None:
        return "missing", None, wanted
    return ("ok" if found == wanted else "other"), found, wanted


def latest(url=None, timeout=TIMEOUT, opener=urllib.request.urlopen):
    """The newest release GitHub lists for Typst -- `0.14.2`, its tag without the `v` -- or None: no network, a proxy, a limit of GitHub's reached, an answer not of the shape expected. Never raises: an answer nobody asked for must not be able to stop a window opening."""
    request = urllib.request.Request(url or RELEASES_API, headers={"Accept": "application/vnd.github+json", "User-Agent": "Woodcore"})
    try:
        with opener(request, timeout=timeout) as response:
            tag = str(json.load(response)["tag_name"]).strip().lstrip("vV")
    except (urllib.error.URLError, OSError, ValueError, KeyError, TypeError, AttributeError):
        return None
    return tag if _VERSION.fullmatch(tag) else None


def newer(candidate, current):
    """Whether `candidate` is a later version than `current` (dependencies.newer_than: a suffix stops the comparison, so a pre-release never looks newer)."""
    return dependencies.newer_than(candidate, current)


def update(version_file=None, fetch=None):
    """The version of Typst newer than the one pinned that GitHub offers, or None -- nothing newer, nothing pinned, or no answer. `fetch` replaces the network (tests)."""
    wanted = pinned(version_file)
    available = (fetch or latest)()
    return available if wanted and available and newer(available, wanted) else None


# --- winget --------------------------------------------------------------------------------

def winget():
    """winget's path, or None where this machine has none -- a Windows Server, a Windows without App Installer."""
    return shutil.which("winget")


def parse_winget_list(output):
    """(managed, version) from what `winget list --id Typst.Typst -e` prints: its table carries a row naming the id, the version after it -- `Typst  Typst.Typst  0.14.2  winget` -- or it says «No installed package found matching input criteria.», winget then not managing the Typst there is."""
    for line in re.split(r"[\r\n]+", output or ""):
        tokens = line.split()
        lowered = [token.lower() for token in tokens]
        if WINGET_ID.lower() in lowered:
            at = lowered.index(WINGET_ID.lower())
            version = tokens[at + 1] if at + 1 < len(tokens) else None
            return True, (version if version and _VERSION.fullmatch(version) else None)
    return False, None


def winget_list(run=proc.run):
    """(managed, version): whether winget manages a Typst here, and which -- asked of `winget list`, a read that installs nothing. (False, None) without winget or without an answer."""
    exe = winget()
    if exe is None:
        return False, None
    try:
        out = run([exe, "list", "--id", WINGET_ID, "-e"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=WINGET_TIMEOUT)
    except (OSError, subprocess.SubprocessError):
        return False, None
    return parse_winget_list((out.stdout or "") + (out.stderr or ""))


def install_command(version, managed=False, current=None):
    """The winget line that brings this machine to Typst `version`: `upgrade` where winget manages an older Typst, else `install` -- `--force` where winget manages one already, a newer one to go back from. Built rather than run: the window shows it and runs it on a yes. The agreements are accepted on the command line, the engineer's yes being given in the window before it runs, and winget would otherwise wait on a question nobody sees."""
    base = ["--id", WINGET_ID, "-e", "--version", version, "--accept-package-agreements", "--accept-source-agreements", "--disable-interactivity"]
    exe = winget() or "winget"
    if managed and current and newer(version, current):
        return [exe, "upgrade", *base]
    return [exe, "install", *base, *(["--force"] if managed else [])]


def winget_links():
    """Where winget puts the command of a portable package, Typst's among them: `%LOCALAPPDATA%\\Microsoft\\WinGet\\Links`."""
    return Path(os.environ.get("LOCALAPPDATA") or Path.home()) / "Microsoft" / "WinGet" / "Links"


def fresh_path():
    """The PATH a process started now would have -- the machine's, then the user's, as Windows keeps them -- rather than this one's, which winget cannot change. This process's where the registry cannot be read."""
    if sys.platform == "win32":
        try:
            import winreg
            parts = []
            for root, key in ((winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"), (winreg.HKEY_CURRENT_USER, "Environment")):
                try:
                    with winreg.OpenKey(root, key) as handle:
                        parts.append(os.path.expandvars(winreg.QueryValueEx(handle, "Path")[0]))
                except OSError:
                    pass
            if parts:
                return os.pathsep.join(parts)
        except ImportError:
            pass
    return os.environ.get("PATH", "")


def on_path(path=None, extra=(), run=proc.run):
    """[(typst, version), ...] for every Typst on `path` (fresh_path's by default), in the order a process finds them, then in the folders of `extra`: the first is the one a new process compiles with."""
    name = "typst.exe" if sys.platform == "win32" else "typst"
    folders = [f for f in (path if path is not None else fresh_path()).split(os.pathsep) if f.strip()] + [str(f) for f in extra]
    seen, out = set(), []
    for folder in folders:
        candidate = Path(folder.strip().strip('"')) / name
        key = os.path.normcase(str(candidate))
        if key in seen or not candidate.is_file():
            continue
        seen.add(key)
        out.append((str(candidate), installed(candidate, run=run)))
    return out


def after_install(version, path=None, run=proc.run):
    """What installing Typst `version` came to: {"ok": whether the first Typst of the PATH is it, "first": (its path, its version) or None, "found": the path of a Typst of `version` found further down or in winget's Links, or None}. A Typst installed otherwise that stays first on the PATH hides the one winget installed, which the window then says by name."""
    found = on_path(path, extra=[winget_links()], run=run)
    first = found[0] if found else None
    where = next((p for p, v in found if v == version), None)
    return {"ok": bool(first and first[1] == version), "first": first, "found": where}


# --- the pin ---------------------------------------------------------------------------------

def pin(version, version_file=None):
    """Rewrites the Typst pinned to `version`: typst-version.txt, the one file every reader of the pin reads (v0.117). Returns the files rewritten -- [] where it already names `version`. Raises PinError for a version not of the shape `1.2.3`, or a file that cannot be written."""
    if not _VERSION.fullmatch(str(version or "")):
        raise PinError(f"{version!r}: not a Typst version")
    path = Path(version_file or VERSION_FILE)
    try:
        before = _read(path)
    except OSError:
        before = None
    text = version + "\n"
    if before == text:
        return []
    try:
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(text)
    except OSError as exc:
        raise PinError(f"{path}: {exc}") from None
    return [path]
