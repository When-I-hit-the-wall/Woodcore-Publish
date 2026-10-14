"""Prepares a machine to run the whole test suite, in one command (docs/conventions/testing.md §11ter, v0.117, issue #26).

    python tests/bootstrap.py                 everything below that is missing, then the versions checked
    python tests/bootstrap.py --check         says what is missing and installs nothing; exit 1 if anything is
    python tests/bootstrap.py --typst-only    Typst alone (the website's workflow, which needs nothing else)
    python tests/bootstrap.py --prefix DIR    where Typst goes (default ~/.local/bin, %LOCALAPPDATA%\\Woodcore\\bin on Windows)
    python tests/bootstrap.py --record-hashes 0.16.0
                                              downloads every official archive of that Typst and records its SHA-256 in typst-sha256.json

What it installs, each only where it is missing, so a second call installs nothing:

* **the Python packages requirements.txt pins**, by one `pip install -r requirements.txt`, where one of them is missing or at another version;
* **on Linux, the system libraries Qt needs to draw without a screen** (libEGL, libxkbcommon, libGL, fontconfig, D-Bus), by `apt-get`, where they cannot be found and apt-get can be run; the window's tests otherwise skip by the hundred;
* **Typst, the version typst-version.txt names**, from its official archive on GitHub, refused unless its SHA-256 is the one typst-sha256.json records -- a hash fetched beside the archive would verify nothing.

The standard library only, like tests/run_tests.py: it runs before anything is installed. The hook SessionStart of .claude/settings.json calls it in Claude Code's cloud sessions, and .github/workflows/tests.yml and site.yml call it, so this file is the only list of what a test machine needs.
"""

import argparse
import ctypes.util
import hashlib
import importlib.metadata as metadata
import io
import json
import os
import platform
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REQUIREMENTS = ROOT / "requirements.txt"
VERSION_FILE = ROOT / "typst-version.txt"
HASH_FILE = ROOT / "typst-sha256.json"
DOWNLOAD = "https://github.com/typst/typst/releases/download/v{version}/{asset}"
TIMEOUT = 120

# (platform.system(), platform.machine() lowered) -> the archive Typst publishes for it
ASSETS = {
    ("linux", "x86_64"): "typst-x86_64-unknown-linux-musl.tar.xz",
    ("linux", "amd64"): "typst-x86_64-unknown-linux-musl.tar.xz",
    ("linux", "aarch64"): "typst-aarch64-unknown-linux-musl.tar.xz",
    ("linux", "arm64"): "typst-aarch64-unknown-linux-musl.tar.xz",
    ("windows", "amd64"): "typst-x86_64-pc-windows-msvc.zip",
    ("windows", "x86_64"): "typst-x86_64-pc-windows-msvc.zip",
    ("windows", "arm64"): "typst-aarch64-pc-windows-msvc.zip",
    ("darwin", "x86_64"): "typst-x86_64-apple-darwin.tar.xz",
    ("darwin", "arm64"): "typst-aarch64-apple-darwin.tar.xz",
}

# The library Qt opens (as ctypes.util.find_library names it) -> the Debian/Ubuntu package that carries it
QT_LIBRARIES = {
    "EGL": "libegl1",
    "xkbcommon": "libxkbcommon0",
    "GL": "libgl1",
    "fontconfig": "libfontconfig1",
    "dbus-1": "libdbus-1-3",
}

_PIN_LINE = re.compile(r"^([A-Za-z0-9_.-]+)==([^\s#;]+)")
_VERSION = re.compile(r"\d+\.\d+(?:\.\d+)*")


class BootstrapError(Exception):
    """What stops the preparation: a hash that does not match, a version with no recorded hash, a platform Typst publishes nothing for."""


def say(text, quiet=False):
    if not quiet:
        print(f"bootstrap: {text}", flush=True)


# --- the Python packages ---------------------------------------------------------------------

def pins(requirements=REQUIREMENTS):
    """[(name, version), ...] requirements.txt pins with `==`."""
    out = []
    for line in Path(requirements).read_text(encoding="utf-8").splitlines():
        m = _PIN_LINE.match(line.strip())
        if m:
            out.append((m.group(1), m.group(2)))
    return out


def package_mismatches(requirements=REQUIREMENTS, version_of=None):
    """[(name, pinned, installed or None), ...] for each package not installed at its pinned version."""
    def installed(name):
        try:
            return metadata.version(name)
        except metadata.PackageNotFoundError:
            return None
    version_of = version_of or installed
    return [(name, wanted, found) for name, wanted in pins(requirements) for found in [version_of(name)] if found != wanted]


def install_packages(requirements=REQUIREMENTS, run=subprocess.run):
    out = run([sys.executable, "-m", "pip", "install", "--disable-pip-version-check", "-q", "-r", str(requirements)])
    if out.returncode != 0:
        raise BootstrapError(f"pip install -r {requirements} failed with code {out.returncode}")


# --- the system libraries of Qt (Linux) -------------------------------------------------------

def missing_qt_packages(find=ctypes.util.find_library, system=None):
    """The apt packages carrying the libraries Qt needs and this Linux lacks; [] elsewhere."""
    if (system or platform.system()).lower() != "linux":
        return []
    return [package for library, package in QT_LIBRARIES.items() if not find(library)]


def install_qt_packages(packages, run=subprocess.run):
    if not packages:
        return
    apt = shutil.which("apt-get")
    if apt is None:
        raise BootstrapError("the libraries Qt needs are missing (" + ", ".join(packages) + ") and there is no apt-get to install them: install them with the system's package manager")
    prefix = [] if hasattr(os, "geteuid") and os.geteuid() == 0 else (["sudo", "-n"] if shutil.which("sudo") else [])
    env = dict(os.environ, DEBIAN_FRONTEND="noninteractive")
    if run([*prefix, apt, "install", "-y", "-q", *packages], env=env).returncode != 0:
        # the lists may be stale or absent on a fresh image: read them once, then try again
        run([*prefix, apt, "update", "-q"], env=env)
        if run([*prefix, apt, "install", "-y", "-q", *packages], env=env).returncode != 0:
            raise BootstrapError("apt-get could not install " + " ".join(packages))


# --- Typst ------------------------------------------------------------------------------------

def pinned(version_file=VERSION_FILE):
    text = Path(version_file).read_text(encoding="utf-8").strip()
    if not _VERSION.fullmatch(text):
        raise BootstrapError(f"{version_file}: holds {text!r}, not a Typst version")
    return text


def asset_name(system=None, machine=None):
    key = ((system or platform.system()).lower(), (machine or platform.machine()).lower())
    try:
        return ASSETS[key]
    except KeyError:
        raise BootstrapError(f"Typst publishes no archive for {key[0]} on {key[1]}") from None


def recorded_hash(version, asset, hash_file=HASH_FILE):
    hashes = json.loads(Path(hash_file).read_text(encoding="utf-8")).get("versions", {})
    found = hashes.get(version, {}).get(asset)
    if not found:
        raise BootstrapError(f"{Path(hash_file).name} records no SHA-256 for {asset} of Typst {version}: run `python tests/bootstrap.py --record-hashes {version}`")
    return found


def verify(data, expected, asset):
    found = hashlib.sha256(data).hexdigest()
    if found != expected.lower():
        raise BootstrapError(f"{asset}: SHA-256 {found}, typst-sha256.json records {expected} -- the archive is refused")


def default_prefix():
    if platform.system().lower() == "windows":
        return Path(os.environ.get("LOCALAPPDATA") or Path.home()) / "Woodcore" / "bin"
    return Path.home() / ".local" / "bin"


def executable_name():
    return "typst.exe" if platform.system().lower() == "windows" else "typst"


def typst_version(executable):
    """The version `executable --version` prints, or None where nothing answers."""
    try:
        out = subprocess.run([str(executable), "--version"], capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    m = _VERSION.search(out.stdout or "")
    return m.group(0) if out.returncode == 0 and m else None


def found_typst(prefix):
    """The Typst a process would run -- the PATH's, else the one in `prefix` -- and its version: (path or None, version or None)."""
    candidates = [shutil.which("typst"), str(Path(prefix) / executable_name())]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return candidate, typst_version(candidate)
    return None, None


def fetch(url, timeout=TIMEOUT):
    request = urllib.request.Request(url, headers={"User-Agent": "Woodcore-bootstrap"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def extract(data, asset):
    """The bytes of the Typst executable inside the archive `asset`."""
    name = "typst.exe" if asset.endswith(".zip") else "typst"
    if asset.endswith(".zip"):
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            for member in archive.namelist():
                if member.rsplit("/", 1)[-1] == name:
                    return archive.read(member)
    else:
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:xz") as archive:
            for member in archive.getmembers():
                if member.isfile() and member.name.rsplit("/", 1)[-1] == name:
                    return archive.extractfile(member).read()
    raise BootstrapError(f"{asset}: holds no {name}")


def install_typst(version, prefix, asset=None, hash_file=HASH_FILE, download=fetch):
    """Downloads the archive of Typst `version`, refuses it unless its SHA-256 is the recorded one, and writes the executable into `prefix`. Returns its path."""
    asset = asset or asset_name()
    expected = recorded_hash(version, asset, hash_file)  # before the download: no hash, nothing fetched
    data = download(DOWNLOAD.format(version=version, asset=asset))
    verify(data, expected, asset)
    binary = extract(data, asset)
    prefix = Path(prefix)
    prefix.mkdir(parents=True, exist_ok=True)
    target = prefix / ("typst.exe" if asset.endswith(".zip") else "typst")
    with tempfile.NamedTemporaryFile(dir=prefix, delete=False) as tmp:
        tmp.write(binary)
    os.replace(tmp.name, target)
    target.chmod(target.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return target


def record_hashes(version, hash_file=HASH_FILE, download=fetch):
    """Downloads every archive of ASSETS for Typst `version` and writes their SHA-256 into typst-sha256.json. Returns {asset: hash}."""
    hashes = {}
    for asset in sorted(set(ASSETS.values())):
        hashes[asset] = hashlib.sha256(download(DOWNLOAD.format(version=version, asset=asset))).hexdigest()
    path = Path(hash_file)
    data = json.loads(path.read_text(encoding="utf-8"))
    data.setdefault("versions", {})[version] = hashes
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return hashes


def on_path(folder):
    folder = os.path.normcase(str(Path(folder).resolve()))
    return any(os.path.normcase(str(Path(p).resolve())) == folder for p in os.environ.get("PATH", "").split(os.pathsep) if p.strip())


# --- the command ------------------------------------------------------------------------------

def examples_engine_stale(root=ROOT):
    """Whether the engine's copy beside the frozen examples is missing or not today's `lib/` (`examples/lib/` is generated and not versioned, docs/typst/command-docs.md §10sexies): a clone has none, and tests/test_commands.py compiles the examples against it."""
    copy = root / "examples" / "lib"
    if not (copy / "calc-engine.typ").is_file() or not (root / "examples" / "commands.typ").is_file():
        return True
    return any(path.is_file() and (root / "lib" / path.relative_to(copy)).is_file() and path.read_bytes() != (root / "lib" / path.relative_to(copy)).read_bytes()
               for path in copy.rglob("*"))


def refresh_examples_engine(root=ROOT, run=subprocess.run):
    """The copy written by `build_examples.refresh_engine`, the one function that writes it (packaging/build.py calls it too) -- in a child, the packages being installed by then."""
    done = run([sys.executable, "-c", "import sys; sys.path[:0] = [sys.argv[1]]; import build_examples; build_examples.refresh_engine()", str(root / "calc" / "tools")],
               capture_output=True, text=True)
    if done.returncode != 0:
        raise BootstrapError(f"the engine's copy beside the examples could not be written: {(done.stderr or done.stdout).strip()[-400:]}")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Prepares a machine to run Woodcore's test suite: requirements.txt, Qt's system libraries, the pinned Typst.")
    ap.add_argument("--check", action="store_true", help="say what is missing, install nothing; exit 1 if anything is")
    ap.add_argument("--typst-only", action="store_true", help="Typst alone")
    ap.add_argument("--prefix", help="the folder Typst is installed into")
    ap.add_argument("--quiet", action="store_true", help="say only what is installed or wrong")
    ap.add_argument("--record-hashes", metavar="VERSION", help="record the SHA-256 of every official archive of that Typst in typst-sha256.json, and do nothing else")
    args = ap.parse_args(argv)

    if args.record_hashes:
        for asset, digest in record_hashes(args.record_hashes).items():
            say(f"{asset} {digest}")
        return 0

    prefix = Path(args.prefix) if args.prefix else default_prefix()
    missing = []
    try:
        if not args.typst_only:
            wrong = package_mismatches()
            if wrong:
                missing.append("packages: " + ", ".join(f"{n} {f or 'missing'} (pinned {w})" for n, w, f in wrong))
                if not args.check:
                    say("installing requirements.txt: " + ", ".join(n for n, _w, _f in wrong))
                    install_packages()
                    still = package_mismatches()
                    if still:
                        raise BootstrapError("after pip, still not as pinned: " + ", ".join(f"{n} {f or 'missing'} (pinned {w})" for n, w, f in still))
            else:
                say("the packages of requirements.txt are installed at their pinned versions", args.quiet)
            libraries = missing_qt_packages()
            if libraries:
                missing.append("Qt's system libraries: " + " ".join(libraries))
                if not args.check:
                    say("installing Qt's system libraries: " + " ".join(libraries))
                    install_qt_packages(libraries)
            elif platform.system().lower() == "linux":
                say("Qt's system libraries are there", args.quiet)

        version = pinned()
        where, found = found_typst(prefix)
        if found == version:
            say(f"Typst {version} is there ({where})", args.quiet)
            if os.environ.get("GITHUB_PATH") and not on_path(Path(where).parent):  # a Typst restored by a CI cache into --prefix: the later steps find it too
                with open(os.environ["GITHUB_PATH"], "a", encoding="utf-8") as f:
                    f.write(str(Path(where).parent) + "\n")
        else:
            missing.append(f"Typst {version} (found {found or 'none'})")
            if not args.check:
                say(f"installing Typst {version} into {prefix}" + (f" (the PATH gives {found} at {where})" if found else ""))
                target = install_typst(version, prefix)
                if typst_version(target) != version:
                    raise BootstrapError(f"{target} does not answer {version} to --version")
                if os.environ.get("GITHUB_PATH"):
                    with open(os.environ["GITHUB_PATH"], "a", encoding="utf-8") as f:
                        f.write(str(prefix) + "\n")
                elif not on_path(prefix):
                    say(f"{prefix} is not on the PATH: add it, or Woodcore and the tests will not find Typst")
                if shutil.which("typst") and typst_version(shutil.which("typst")) not in (version, None) and on_path(prefix):
                    say(f"another Typst comes before {prefix} on the PATH: {shutil.which('typst')}")
        if not args.typst_only:
            if examples_engine_stale():
                missing.append("the engine's copy beside the frozen examples (examples/lib/)")
                if not args.check:
                    say("writing the engine's copy beside the frozen examples (examples/lib/)")
                    refresh_examples_engine()
            else:
                say("the engine's copy beside the frozen examples is today's", args.quiet)
    except BootstrapError as exc:
        print(f"bootstrap: {exc}", file=sys.stderr, flush=True)
        return 1
    except OSError as exc:  # the network or the disk, named as they failed
        print(f"bootstrap: {exc}", file=sys.stderr, flush=True)
        return 1

    if args.check:
        for line in missing:
            print(f"bootstrap: missing -- {line}", flush=True)
        return 1 if missing else 0
    if not missing:
        say("already up to date: nothing installed", args.quiet)
    return 0


if __name__ == "__main__":
    sys.exit(main())
