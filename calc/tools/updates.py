"""Whether a newer Woodcore has been published, and fetching it (docs/conventions/build-and-release.md §12, v0.89).

An installed Woodcore asks the project's website, once at each start, what the latest version is: `version.json`, written by the site's build (website/build.py) on the project's website (Cloudflare Pages), and names an installer published as a Release of a public GitHub repository, the installer being too large for a file of that site (v0.117). Where it names a newer version than this one -- and that version is neither installed already, nor set aside by the engineer, nor put off for today -- the window says so, and «Installer» downloads the installer, checks it against the SHA-256 the manifest states, and starts it (update_gui.py). Versions install side by side (packaging/woodcore.iss), so nothing is replaced: a project pinned to an older version still opens with it.

Qt-free, like dependencies.py beside it, so that tests/test_updates.py reads exactly what the window reads. Every function that touches the network says nothing when it fails -- no network, a proxy, a site not yet published: an answer nobody asked for must not be able to stop a window opening.

Three things are refused, each by name, rather than acted on: a manifest that does not have the shape below; an installer whose address is neither HTTPS on the manifest's own host nor HTTPS on the one place this program names for installers, INSTALLER_PREFIX -- github.com, the Releases of Woodcore's own repository, written whole and checked as a parsed address, never as the start of a string (a manifest pointing elsewhere is not one this program was built to trust; what a manifest on the site cannot do, is have this program fetch from a host the program was not built with); and a downloaded file whose size or SHA-256 is not the one stated. The file is written beside its final name and renamed only once it checks, so a download cut short never leaves an installer that looks whole.

Asked only by an installed Woodcore: a checkout is updated by git, and a test run asks nothing. `WOODCORE_UPDATE_CHECK=1` asks from the sources all the same, `0` never asks; `WOODCORE_UPDATE_URL` names another manifest (what the tests serve one with).
"""

import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import proc
import usersettings

# The manifest the site publishes (website/build.py writes it), on Cloudflare Pages: website/site.json's base_url, which tests/test_updates.py holds equal to this (the installed program has no website/ to read it from). It answers anyone, the repository itself being private.
FEED_URL = "https://woodcore.pages.dev/version.json"
# The one place besides the manifest's own host an installer may be fetched from: the Releases of the public repository packaging/publish.py uploads them to (website/site.json's releases_repo, held equal by tests/test_updates.py). The host and the start of the path are fixed; the SHA-256 and the size the manifest states are what make the file the right one. GitHub answers with a redirect to a signed address of its own, which is followed -- those hosts are not named here, GitHub having already renamed them once -- so long as it does not leave HTTPS.
INSTALLER_HOST = "github.com"
INSTALLER_PREFIX = "/When-I-hit-the-wall/woodcore-releases/releases/download/"
ENV_URL = "WOODCORE_UPDATE_URL"
ENV_CHECK = "WOODCORE_UPDATE_CHECK"

SCHEMA_VERSION = "1.0"
TIMEOUT = 5.0            # the manifest: short, it is a convenience
DOWNLOAD_TIMEOUT = 30.0  # each read of the installer: a slow connection is still a connection
SNOOZE_HOURS = 24        # «Plus tard»: one process per project (docs/decisions.md §13), so a day, not a start -- three projects opened in a morning are not three questions
CHUNK = 1 << 16

# Where every version is installed, one folder each (packaging/woodcore.iss) -- packaging/launcher.py's INSTALL_ROOT, held equal by tests/test_updates.py. A version whose folder holds Woodcore.exe is installed, and is not offered again.
INSTALL_ROOT = Path(os.environ.get("LOCALAPPDATA") or Path.home()) / "Programs" / "Woodcore"

VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
LANGUAGES = ("fr", "de", "en")


class UpdateError(Exception):
    """A download that did not give the installer the manifest names. `code` is what the window writes its own sentence for (update_gui.STRINGS); args[0] is the English, for a caller with no window."""

    def __init__(self, message, code, **detail):
        super().__init__(message)
        self.code = code
        self.detail = detail


def version_tuple(text):
    """0.89.0 -> (0, 89, 0); a piece that is not a number counts as 0, as the launcher reads it."""
    parts = []
    for piece in str(text).split("."):
        digits = "".join(ch for ch in piece if ch.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts)


def feed_url():
    return os.environ.get(ENV_URL) or FEED_URL


def enabled(settings=None):
    """Whether this process asks at all: an installed Woodcore does, a checkout does not, unless WOODCORE_UPDATE_CHECK says otherwise; and never where the settings say `updates.enabled: false`."""
    forced = os.environ.get(ENV_CHECK)
    if forced == "0":
        return False
    prefs = (settings or {}).get("updates")
    if isinstance(prefs, dict) and prefs.get("enabled") is False:
        return False
    if forced == "1":
        return True
    return bool(getattr(sys, "frozen", False))


def installer_address_problem(url, feed=None):
    """Why `url` is not an address an installer may be fetched from, "" where it is: HTTPS, and either on the manifest's own host (`feed`, where one is given) or exactly at INSTALLER_HOST under INSTALLER_PREFIX -- no port, no user name, no query, no fragment, no `..` or encoded separator in the path."""
    if not isinstance(url, str) or not url.startswith("https://"):
        return f"installer url {url!r} is not HTTPS"
    if not feed:
        return ""
    parts = urllib.parse.urlsplit(url)
    if parts.netloc == urllib.parse.urlsplit(feed).netloc:
        return ""
    path = parts.path
    lowered = path.lower()
    released = (parts.netloc == INSTALLER_HOST and not parts.query and not parts.fragment and "?" not in url and "#" not in url
                and path.startswith(INSTALLER_PREFIX) and len(path) > len(INSTALLER_PREFIX)
                and "\\" not in url and "%2e" not in lowered and "%2f" not in lowered and "%5c" not in lowered
                and all(piece not in ("", ".", "..") for piece in path[len(INSTALLER_PREFIX):].split("/")))
    return "" if released else f"installer url {url!r} is neither on the manifest's own host nor in Woodcore's releases"


def validate(manifest, feed=None):
    """The reasons `manifest` cannot be acted on, [] where it can. It is read from the network, so nothing about its shape is assumed."""
    if not isinstance(manifest, dict):
        return ["not a JSON object"]
    problems = []
    if manifest.get("schema_version") != SCHEMA_VERSION:
        problems.append(f"schema_version is {manifest.get('schema_version')!r}, expected {SCHEMA_VERSION!r}")
    if not isinstance(manifest.get("version"), str) or not VERSION_RE.match(manifest["version"]):
        problems.append(f"version {manifest.get('version')!r} is not <major>.<minor>.<patch>")
    installer = manifest.get("installer")
    if not isinstance(installer, dict):
        problems.append("no installer")
    else:
        problem = installer_address_problem(installer.get("url"), feed)
        if problem:
            problems.append(problem)
        if not isinstance(installer.get("sha256"), str) or not SHA256_RE.match(installer["sha256"]):
            problems.append("installer sha256 is not 64 lowercase hexadecimal digits")
        if not isinstance(installer.get("size"), int) or installer["size"] <= 0:
            problems.append("installer size is not a positive whole number of bytes")
    notes = manifest.get("notes", {})
    if not isinstance(notes, dict) or any(not isinstance(v, str) for v in notes.values()):
        problems.append("notes is not {language: text}")
    return problems


def fetch(url=None, timeout=TIMEOUT):
    """The manifest the site publishes, or None -- no network, no site yet, a manifest that does not validate. Never raises."""
    url = url or feed_url()
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "Woodcore", "Cache-Control": "no-cache"})
        with urllib.request.urlopen(request, timeout=timeout) as response:
            manifest = json.loads(response.read(1 << 20).decode("utf-8"))
    except (urllib.error.URLError, OSError, ValueError):
        return None
    return manifest if not validate(manifest, url) else None


def installed(root=None):
    """The versions installed side by side on this machine, as the launcher finds them."""
    root = Path(root or INSTALL_ROOT)
    if not root.is_dir():
        return []
    return [f.name for f in root.iterdir() if f.is_dir() and f.name[:1].isdigit() and (f / "Woodcore.exe").is_file()]


def _prefs(settings):
    prefs = settings.get("updates")
    return prefs if isinstance(prefs, dict) else {}


def offer(manifest, current, settings, now=None, root=None):
    """Whether the window should announce `manifest`: a newer version than `current`, not installed here already, not set aside («Ignorer cette version»), not put off within the day («Plus tard»)."""
    if not manifest:
        return False
    version = manifest["version"]
    if version_tuple(version) <= version_tuple(current):
        return False
    if version in installed(root):
        return False   # already here: the launcher starts it; this window is an older one opened on purpose
    prefs = _prefs(settings)
    if prefs.get("skipped") == version:
        return False
    snoozed = prefs.get("snoozed")
    if isinstance(snoozed, dict) and snoozed.get("version") == version:
        until = snoozed.get("until")
        if isinstance(until, (int, float)) and (now if now is not None else time.time()) < until:
            return False
    return True


def skip(settings, version):
    """«Ignorer cette version»: never announced again -- a later one will be. Changes `settings` and returns it."""
    prefs = dict(_prefs(settings))
    prefs["skipped"] = version
    prefs.pop("snoozed", None)
    settings["updates"] = prefs
    return settings


def snooze(settings, version, now=None, hours=SNOOZE_HOURS):
    """«Plus tard»: not announced again for `hours`. Changes `settings` and returns it."""
    prefs = dict(_prefs(settings))
    prefs["snoozed"] = {"version": version, "until": (now if now is not None else time.time()) + hours * 3600}
    settings["updates"] = prefs
    return settings


def notes(manifest, lang):
    """What is new, in `lang` -- else English, else French, else nothing."""
    texts = manifest.get("notes") or {}
    for key in (lang, "en", "fr", "de"):
        if isinstance(texts.get(key), str) and texts[key].strip():
            return texts[key].strip()
    return ""


def page(manifest, lang):
    """The download page in `lang`, where the manifest names one."""
    pages = manifest.get("page") or {}
    return pages.get(lang) or pages.get("en") or ""


def changes(manifest, lang, feed=None):
    """The page saying what the version changes and what to do about it, in `lang` -- else English -- or "" (v0.89: `changes` in version.json, website/build.py). Only an HTTPS page on the manifest's own host: the window offers it as a link."""
    pages = manifest.get("changes")
    if not isinstance(pages, dict):
        return ""
    url = pages.get(lang) or pages.get("en") or ""
    if not isinstance(url, str) or not url.startswith("https://"):
        return ""
    if urllib.parse.urlsplit(url).netloc != urllib.parse.urlsplit(feed or feed_url()).netloc:
        return ""
    return url


def download_dir():
    return usersettings.cache_dir("updates")


def download(manifest, folder=None, progress=None, cancelled=None, timeout=DOWNLOAD_TIMEOUT):
    """The installer the manifest names, downloaded and checked: its path. `progress(done, total)` is told as it comes, `cancelled()` asked between chunks. Raises UpdateError where it is cancelled, fails, or is not the file stated."""
    installer = manifest["installer"]
    url, size, digest = installer["url"], installer["size"], installer["sha256"]
    folder = Path(folder or download_dir())
    name = Path(urllib.parse.urlsplit(url).path).name or f"Woodcore-{manifest['version']}-setup.exe"
    target = folder / name
    if target.is_file() and target.stat().st_size == size and _sha256(target) == digest:
        return target   # downloaded before and put off: no second download
    partial = target.with_name(target.name + ".part")
    try:
        folder.mkdir(parents=True, exist_ok=True)
        request = urllib.request.Request(url, headers={"User-Agent": "Woodcore"})
        hasher, done = hashlib.sha256(), 0
        with urllib.request.urlopen(request, timeout=timeout) as response, open(partial, "wb") as out:
            if url.startswith("https://") and not response.geturl().startswith("https://"):
                raise UpdateError(f"{url} was redirected out of HTTPS", "network", error="redirected out of HTTPS")
            while True:
                if cancelled is not None and cancelled():
                    raise UpdateError("download cancelled", "cancelled")
                chunk = response.read(CHUNK)
                if not chunk:
                    break
                out.write(chunk)
                hasher.update(chunk)
                done += len(chunk)
                if done > size:
                    raise UpdateError(f"{url} is longer than the {size} bytes stated", "size", expected=size, found=done)
                if progress is not None:
                    progress(done, size)
    except UpdateError:
        partial.unlink(missing_ok=True)
        raise
    except (urllib.error.URLError, OSError) as exc:
        partial.unlink(missing_ok=True)
        raise UpdateError(f"{url}: {exc}", "network", error=str(exc)) from exc
    if done != size:
        partial.unlink(missing_ok=True)
        raise UpdateError(f"{url} gave {done} bytes, {size} stated", "size", expected=size, found=done)
    if hasher.hexdigest() != digest:
        partial.unlink(missing_ok=True)
        raise UpdateError(f"{url} does not have the SHA-256 the manifest states", "sha256", expected=digest, found=hasher.hexdigest())
    os.replace(partial, target)
    return target


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(CHUNK), b""):
            h.update(chunk)
    return h.hexdigest()


def launch(installer):
    """Starts the installer the engineer asked for -- per user, no administrator (packaging/woodcore.iss): its own wizard, in its own language, which opens the new version at its end."""
    installer = str(installer)
    if sys.platform == "win32":
        os.startfile(installer)  # noqa: S606 -- the file just checked against the manifest's SHA-256
    else:
        proc.popen([installer], close_fds=True)
