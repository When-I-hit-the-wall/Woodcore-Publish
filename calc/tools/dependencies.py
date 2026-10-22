"""What this project needs installed, and whether it is (docs/architecture/layout.md §11).

`requirements.txt` names the three packages outside the standard library and the versions this report was built against. That file is the statement; this module is what checks the machine against it, and what Woodcore's window shows when the two disagree.

Two questions, deliberately kept apart because they cost different things:

* **What is installed here?** Read out of the running interpreter's own metadata. Instant, offline, and the one that matters: a machine with another openpyxl reads the workbooks with another reader, and the report it builds is not the report this version was verified against.
* **Is there anything newer?** A request to PyPI. Slow, needs a network, and is never a reason to stop anything -- so it runs in a thread of its own, says nothing when it fails, and only ever *offers*.

Nothing here installs anything by itself. `install_command()` builds the line, the window asks, and pip is run only on a yes -- the rule every other action of the window follows.
"""

import json
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

import importlib.metadata as metadata

import proc  # a child process starts without a console window flashing open (calc/proc.py)

ROOT = Path(__file__).resolve().parent.parent.parent
REQUIREMENTS = ROOT / "requirements.txt"

# `name==version`, ignoring comments and blank lines. The file is written by hand and read by pip; this reads the one form pip is given here.
_PIN = re.compile(r"^\s*([A-Za-z0-9._-]+)\s*==\s*([A-Za-z0-9._-]+)\s*$")

# How long to wait on PyPI before giving up. Short: the answer is a convenience, and a window that takes ten seconds to open because a proxy is slow is worse than no answer at all.
PYPI_TIMEOUT = 4.0
PYPI_URL = "https://pypi.org/pypi/{name}/json"


def required():
    """{package: pinned version} as requirements.txt states it, {} where the file is missing."""
    if not REQUIREMENTS.exists():
        return {}
    out = {}
    for line in REQUIREMENTS.read_text(encoding="utf-8").splitlines():
        if line.lstrip().startswith("#"):
            continue
        m = _PIN.match(line)
        if m:
            out[m.group(1)] = m.group(2)
    return out


def installed(name):
    """The version of `name` in this interpreter, or None where it is not installed."""
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def check():
    """What is installed against what is required: [(package, wanted, found), ...] for every one that disagrees, `found` being None where the package is missing.

    Empty when the machine matches the file, which is the normal case and the one the window says nothing about.
    """
    return [
        (name, wanted, installed(name))
        for name, wanted in required().items()
        if installed(name) != wanted
    ]


def latest(name):
    """The newest version PyPI lists for `name`, or None -- no network, a proxy in the way, a name PyPI does not have. Never raises: an answer nobody asked for must not be able to stop a window opening."""
    try:
        with urllib.request.urlopen(PYPI_URL.format(name=name), timeout=PYPI_TIMEOUT) as response:
            return json.load(response)["info"]["version"]
    except (urllib.error.URLError, OSError, ValueError, KeyError):
        return None


def _parts(version):
    """A version as a tuple that sorts: 6.11.2 -> (6, 11, 2). A suffix that is not a number (3.1.5b1) stops the comparison there, which is what makes a pre-release never look newer than the release it precedes."""
    out = []
    for piece in str(version).split("."):
        if not piece.isdigit():
            break
        out.append(int(piece))
    return tuple(out)


def newer_than(candidate, current):
    """Whether `candidate` is a later version than `current`, both read as dotted numbers."""
    a, b = _parts(candidate), _parts(current)
    return bool(a) and bool(b) and a > b


def updates():
    """[(package, pinned, available), ...] for every package PyPI lists a newer version of.

    Reads `requirements.txt`, not what is installed: what a newer version would replace is the *pinned* version, and that is the number the engineer decides about. Calls PyPI once per package -- three requests -- so it belongs in a thread.
    """
    out = []
    for name, pinned in required().items():
        newest = latest(name)
        if newest and newer_than(newest, pinned):
            out.append((name, pinned, newest))
    return out


def install_command(packages=None):
    """The pip line that brings this machine to what requirements.txt states, or that installs `packages` as [(name, version), ...].

    Built rather than run: the window shows it, asks, and only then executes it -- and an engineer who would rather run it in their own terminal can copy it.
    """
    if packages is None:
        return [sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS)]
    return [sys.executable, "-m", "pip", "install"] + [f"{name}=={version}" for name, version in packages]


def install(packages=None, timeout=600):
    """Runs `install_command`. Returns (ok, output). Never raises."""
    try:
        out = proc.run(
            install_command(packages), capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=timeout,
        )
        return out.returncode == 0, (out.stdout or "") + (out.stderr or "")
    except (OSError, subprocess.SubprocessError) as exc:
        return False, str(exc)


def pin(packages):
    """Rewrites the versions in requirements.txt to `packages` as [(name, version), ...], leaving every comment and every blank line where it is.

    Installing a newer version without this would leave the file stating one version and the machine carrying another -- which is exactly the disagreement `check()` reports, arrived at from the other side.
    """
    if not REQUIREMENTS.exists():
        return
    wanted = dict(packages)
    lines = REQUIREMENTS.read_text(encoding="utf-8").splitlines(keepends=True)
    for i, line in enumerate(lines):
        m = _PIN.match(line.rstrip("\r\n"))
        if m and m.group(1) in wanted:
            ending = line[len(line.rstrip("\r\n")):]
            lines[i] = f"{m.group(1)}=={wanted[m.group(1)]}{ending}"
    REQUIREMENTS.write_text("".join(lines), encoding="utf-8", newline="\n")
