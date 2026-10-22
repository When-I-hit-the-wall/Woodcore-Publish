"""Woodcore's own preferences, per user and outside every project (docs/ui/window.md §10quater, v0.83).

`%APPDATA%\\Woodcore\\settings.json` holds the window's language and size, the projects opened lately and the launcher's choice of the version run from the sources; `%LOCALAPPDATA%\\Woodcore\\` the caches a render or a compilation fills and the window's stall log. Until v0.83 both were named after what the window was called then, the Typst-Katalog: `typst-katalog`; the settings are taken over once, the first time Woodcore starts without its own, and the render caches are moved rather than rendered again. The old folders are left where they were.

`WOODCORE_SETTINGS` points the settings elsewhere -- what the tests do, so that a run of the suite never writes the engineer's own preferences (v0.75, named TYPST_KATALOG_SETTINGS until v0.83).
"""

import json
import os
import shutil
from pathlib import Path

NAME = "Woodcore"
OLD_NAME = "typst-katalog"
ENV = "WOODCORE_SETTINGS"

# How many projects the start page and the «Récents» menu list.
RECENT_MAX = 12


def _appdata():
    return Path(os.environ.get("APPDATA") or Path.home())


def _localappdata():
    return Path(os.environ.get("LOCALAPPDATA") or Path.home())


def settings_file():
    named = os.environ.get(ENV)
    return Path(named) if named else _appdata() / NAME / "settings.json"


TEMPLATES_ENV = "WOODCORE_TEMPLATES"


def templates_dir():
    """The engineer's own project templates (calc/templates.py, v0.94): `%APPDATA%\\Woodcore\\templates\\`, one folder each, beside the settings; or `WOODCORE_TEMPLATES`'s folder; or, where only `WOODCORE_SETTINGS` is set -- a test run -- a folder beside the settings file it names, so that a test never writes the engineer's own."""
    named = os.environ.get(TEMPLATES_ENV)
    if named:
        return Path(named)
    settings = os.environ.get(ENV)
    if settings:
        return Path(settings).with_name(Path(settings).stem + "-templates")
    return _appdata() / NAME / "templates"


def cache_dir(*parts):
    """A folder of Woodcore's caches: `renders` for a plan's rendered pages, `examples` for the commands tab's, the stall log at the top. Outside the project, which NextCloud syncs; deleting it costs a render."""
    return _localappdata().joinpath(NAME, *parts)


def migrate():
    """Takes over, once, the settings of the Typst-Katalog, as the window was called until v0.83: copied where Woodcore has none yet. The render caches are moved where Woodcore's are still missing -- a rename on the same disk, where rendering them again would take seconds a page. Nothing at all while `WOODCORE_SETTINGS` points elsewhere, which is a test run: it must move nothing of the engineer's. Returns what was taken over."""
    moved = []
    if os.environ.get(ENV):
        return moved
    old = _appdata() / OLD_NAME / "settings.json"
    new = settings_file()
    if old.is_file() and not new.exists():
        try:
            new.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(old, new)
            moved.append(str(new))
        except OSError:
            pass
    for sub in ("renders", "examples"):
        old, new = _localappdata() / OLD_NAME / sub, cache_dir(sub)
        if old.is_dir() and not new.exists():
            try:
                new.parent.mkdir(parents=True, exist_ok=True)
                old.rename(new)
                moved.append(str(new))
            except OSError:
                pass
    return moved


def read():
    try:
        data = json.loads(settings_file().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def write(settings):
    path = settings_file()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(path.name + ".tmp")
        temporary.write_text(json.dumps(settings, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")
        os.replace(temporary, path)
    except OSError:
        pass  # a preference that cannot be saved is not worth interrupting anyone for


def _same(a, b):
    return os.path.normcase(os.path.abspath(a)) == os.path.normcase(os.path.abspath(b))


def recent_projects(settings):
    """The project files opened lately, the last first -- `last_project`, which v0.82 wrote, counting as one."""
    recent = [p for p in settings.get("recent_projects", []) if isinstance(p, str) and p]
    last = settings.get("last_project")
    if isinstance(last, str) and last and not any(_same(last, p) for p in recent):
        recent.insert(0, last)
    return recent[:RECENT_MAX]


def remember(settings, file):
    """`file` put at the head of the recent projects, once, the list cut to RECENT_MAX. Changes `settings` and returns it."""
    file = str(Path(file).resolve())
    recent = [p for p in recent_projects(settings) if not _same(p, file)]
    settings["recent_projects"] = [file, *recent][:RECENT_MAX]
    settings.pop("last_project", None)
    return settings


def forget(settings, file):
    """`file` taken off the recent projects. Changes `settings` and returns it."""
    settings["recent_projects"] = [p for p in recent_projects(settings) if not _same(p, file)]
    settings.pop("last_project", None)
    return settings
