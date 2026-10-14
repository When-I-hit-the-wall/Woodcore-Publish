"""Woodcore-Launcher.exe: what a double-click on a `.woodcore` file starts, and the Start menu's «Woodcore» (packaging/woodcore.iss, v0.83).

Several versions of Woodcore may be installed side by side, one folder each under `%LOCALAPPDATA%\\Programs\\Woodcore\\<version>\\`, so that a project exported years ago can be opened again with the program that exported it. The file association cannot name one of them -- it would have to change with every installation and uninstallation -- so it names this launcher, which lives beside them in `launcher\\`, and which chooses:

- **the engineer's own sources**, where `%APPDATA%\\Woodcore\\settings.json` says so (`launcher.dev_checkout`, the window's *Fichier* menu from the sources): the developer's machine opens its projects with the code being worked on;
- else **the version the project asks for**, `woodcore_version` in its `.woodcore` (*Propriétés du projet*): the newest installed version whose number begins with it -- `0.83` takes 0.83.2 over 0.83.0;
- else **the newest version installed** -- unless the project was last exported by a newer one than any installed here, which would refuse to write into it (calc/project.py, engine_state `newer`): that is said here, rather than by a window that opens only to refuse.

Standard library only, and one file: it is built alone, as one executable (packaging/launcher.spec), so that an older installer cannot leave half of a newer launcher behind. `--dry-run` prints the command it would start and starts nothing -- what tests/test_packaging.py and the build check it with.
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

INSTALL_ROOT = Path(os.environ.get("LOCALAPPDATA") or Path.home()) / "Programs" / "Woodcore"
SETTINGS = Path(os.environ.get("WOODCORE_SETTINGS") or (Path(os.environ.get("APPDATA") or Path.home()) / "Woodcore" / "settings.json"))
# Where a project's engine copy is when its .woodcore states no layout -- calc/project.py's DEFAULT_LAYOUT["generated"], held equal by tests/test_packaging.py.
DEFAULT_GENERATED = "Statischer Bericht (typst)/_woodcore"
PIN_KEY = "woodcore_version"
# The window in a checkout of the sources, under calc/tools/: woodcore_gui.py since v0.96, catalog_gui.py in a checkout older than that -- which a checkout of v0.96 and after still carries as a shim, for the launchers installed before it. Held equal to the checkout's own files by tests/test_packaging.py.
GUI_SCRIPTS = ("woodcore_gui.py", "catalog_gui.py")

MESSAGES = {
    "fr": {
        "none": "Aucune version de Woodcore n'est installée dans {root}.",
        "pinned": "Ce projet demande Woodcore {pin}, qui n'est pas installé ici. Installées : {installed}.",
        "newer": "Ce projet a été exporté par Woodcore {version}, plus récent que toutes les versions installées ici ({installed}). Installez Woodcore {version} ou une version plus récente pour ouvrir ce projet.",
        "dev": "Les sources de Woodcore choisies pour ouvrir les projets ({path}) sont introuvables, ou pythonw n'est pas sur le PATH.",
    },
    "de": {
        "none": "In {root} ist keine Woodcore-Version installiert.",
        "pinned": "Dieses Projekt verlangt Woodcore {pin}, das hier nicht installiert ist. Installiert: {installed}.",
        "newer": "Dieses Projekt wurde von Woodcore {version} exportiert, neuer als jede hier installierte Version ({installed}). Installieren Sie Woodcore {version} oder eine neuere Version, um dieses Projekt zu öffnen.",
        "dev": "Die zum Öffnen der Projekte gewählten Woodcore-Quellen ({path}) sind nicht zu finden, oder pythonw steht nicht im PATH.",
    },
    "en": {
        "none": "No version of Woodcore is installed in {root}.",
        "pinned": "This project asks for Woodcore {pin}, which is not installed here. Installed: {installed}.",
        "newer": "This project was exported by Woodcore {version}, newer than every version installed here ({installed}). Install Woodcore {version} or a newer version to open this project.",
        "dev": "The Woodcore sources chosen to open projects with ({path}) cannot be found, or pythonw is not on the PATH.",
    },
}


def version_tuple(text):
    parts = []
    for piece in str(text).split("."):
        digits = "".join(ch for ch in piece if ch.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts)


def read_json(path):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def installed(root=None):
    """{version: Woodcore.exe} of every version installed under `root`, newest first."""
    root = Path(root or INSTALL_ROOT)
    found = {}
    if root.is_dir():
        for folder in root.iterdir():
            exe = folder / "Woodcore.exe"
            if folder.is_dir() and folder.name[:1].isdigit() and exe.is_file():
                found[folder.name] = exe
    return dict(sorted(found.items(), key=lambda item: version_tuple(item[0]), reverse=True))


def pinned(project_file):
    """The version prefix the project asks for, "" where it asks for none."""
    value = read_json(project_file).get(PIN_KEY, "")
    return value.strip() if isinstance(value, str) else ""


def written_by(project_file):
    """The version that last wrote the project's engine copy, "" where none did."""
    data = read_json(project_file)
    layout = data.get("layout") if isinstance(data.get("layout"), dict) else {}
    generated = layout.get("generated") or DEFAULT_GENERATED
    stamp = read_json(Path(project_file).parent / generated / "VERSION")
    return str(stamp.get("version", ""))


def choose(versions, pin="", written=""):
    """(version, None) -- the version to start -- or (None, (message key, values)) where none will do."""
    listed = ", ".join(versions) or "-"
    if pin:
        matching = [v for v in versions if v == pin or v.startswith(pin + ".")]
        return (matching[0], None) if matching else (None, ("pinned", {"pin": pin, "installed": listed}))
    if not versions:
        return None, ("none", {"root": str(INSTALL_ROOT)})
    newest = versions[0]
    if written and version_tuple(written) > version_tuple(newest):
        return None, ("newer", {"version": written, "installed": listed})
    return newest, None


def dev_checkout(settings):
    """The engineer's own sources, where the settings choose them: the checkout's `calc/tools/woodcore_gui.py`, else its `catalog_gui.py` where the checkout is older than v0.96 (GUI_SCRIPTS), or None. Where neither is there, the first, which the caller finds missing."""
    launcher = settings.get("launcher") if isinstance(settings.get("launcher"), dict) else {}
    chosen = launcher.get("dev_checkout")
    if not chosen:
        return None
    tools = Path(chosen) / "calc" / "tools"
    return next((tools / name for name in GUI_SCRIPTS if (tools / name).is_file()), tools / GUI_SCRIPTS[0])


def command(project_file=None, root=None, settings=None):
    """The command to start, or (None, (message key, values))."""
    settings = read_json(SETTINGS) if settings is None else settings
    args = ["--project", str(project_file)] if project_file else ["--home"]
    gui = dev_checkout(settings)
    if gui is not None:
        pythonw = shutil.which("pythonw")
        if not gui.is_file() or pythonw is None:
            return None, ("dev", {"path": str(gui.parent.parent.parent)})
        return [pythonw, str(gui), *args], None
    versions = installed(root)
    version, problem = choose(list(versions), pinned(project_file) if project_file else "", written_by(project_file) if project_file else "")
    if problem:
        return None, problem
    return [str(versions[version]), *args], None


def say(problem, settings=None):
    key, values = problem
    settings = read_json(SETTINGS) if settings is None else settings
    lang = settings.get("lang") if settings.get("lang") in MESSAGES else "fr"
    text = MESSAGES[lang][key].format(**values)
    if sys.platform == "win32" and not sys.stdout:
        import ctypes
        ctypes.windll.user32.MessageBoxW(None, text, "Woodcore", 0x30)
    else:
        print(text, file=sys.stderr)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    dry = "--dry-run" in argv
    argv = [a for a in argv if a != "--dry-run"]
    project_file = next((a for a in argv if a.lower().endswith(".woodcore")), None)
    cmd, problem = command(project_file)
    if problem:
        say(problem)
        return 1
    if dry:
        print(json.dumps(cmd))
        return 0
    flags = 0x00000008 | 0x00000200 if sys.platform == "win32" else 0   # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
    subprocess.Popen(cmd, close_fds=True, creationflags=flags, cwd=str(Path(cmd[0]).parent))
    return 0


if __name__ == "__main__":
    sys.exit(main())
