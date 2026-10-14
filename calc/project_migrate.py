"""A project laid out as one report, moved into three documents: the migration of the three document modes (work package 1.3).

Until the three documents a project was laid out as one report: its report's folder, `Statischer Bericht (typst)/`, was the Typst root and held everything the report reads -- its `config.typ` and `commands.typ`, the project's `references.bib`, its `Images/`, and the export in `_woodcore/`. A project in three documents keeps what the three share at the top of the project, which becomes the Typst root, and gives each document a folder of its own: `1_Nutzungsvereinbarung/`, `2_Projektbasis/`, `3_Statischer Bericht/` in German (calc/documents.py). This module moves the one into the other. What it does is small, and how it does it is the whole of it, because it moves the engineer's real project on disk one day, and a project moved wrongly is a report nobody can compile any more.

**Nothing is deleted, and nothing is copied: things are renamed.** The export, the pictures and the three shared files go up to the top of the project by `os.rename`, and last of all the report's folder takes its new name; the two new documents are made from their templates (calc/doc_templates.py) into folders that did not exist. What a rename moves keeps every byte and every date it had, and a rename is undone by another.

**What is written is written where it has to be, and textually.** Every `.typ` of the report is rewritten by calc/typst_paths.py, which changes a path literal only where it would stop reaching its target and keeps every other byte, line endings included; the project's `.woodcore` gains its layout in full -- by the very bytes `project.update` writes where the file is in Woodcore's own form, and by a textual edit where it is not, since a file written by hand is never reserialised (json.dumps drops what it does not know). `.vscode/settings.json` gains `"tinymist.rootPath": "${workspaceFolder}"` -- the project's folder, which is now the Typst root, stated for Tinymist as a safety net -- inserted as a line of its own where the file does not state a root already, every other line kept, and made from the template's where the project has none; its `tinymist.outputPath` follows the report's folder where it points into it, which neither the template nor the engineer's project does.

**Everything is proved against a reference taken first**, as v0.82's step 4 was. Before the first move -- and after the backup, so that undoing the migration undoes the reference's own export and engine update too -- the report is compiled as it is written, its pages read as text, its outline and the variables its PDF carries kept, and -- unless `skip_data` -- the export run and kept. After the last write the project is read again, and it must say it is laid out in three documents, its engine must be intact, the export run again must write the same data, the report compiled from its new place must print the same pages, the same outline and the same variables (modulo the runs of white and the date the title page prints), and the two new documents must compile.

**A failure anywhere undoes everything.** A write-ahead log, `<archives>/migration-<timestamp>/moves.json`, is written before the first move and after every step, and `before.zip` beside it, written before anything else, holds the `.woodcore`, the `.vscode/settings.json` and the whole of the report's folder as they were found. On a failure the new documents are moved into `rolled-back/`, the renames are undone in reverse, and every file of the old tree is put back from the zip where it differs, what the migration added being moved into `rolled-back/` rather than deleted; `result.json` then says why. `rollback(workspace)` does the same on request once a migration has succeeded, and refuses where the engineer has changed something since (a moved folder not where the log put it, a rewritten file not the bytes the migration wrote).

The entry points: `plan()` says what would be done and reads nothing but files; `check()` adds what depends on the moment -- the lock, the engine, Typst and pypdf -- and gives the refusals, each an `engine.Note` with a code and an English sentence; `run()` does it, `rollback()` undoes it, and `command()` is `woodcore-cli migrate` (its arguments in its docstring). There is no Qt in this file, so the command line, the window's dialog and the tests all go through it.
"""

import argparse
import hashlib
import importlib.util
import inspect
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import time
import zipfile
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path, PurePosixPath

# calc/ and calc/tools on the path: this module is also run as a script, and the archive is a tool.
_CALC = Path(__file__).resolve().parent
for _path in (str(_CALC), str(_CALC / "tools")):
    if _path not in sys.path:
        sys.path.insert(0, _path)

import documents  # noqa: E402
import engine  # noqa: E402
import proc  # noqa: E402  -- a child process starts without a console window flashing open
import project  # noqa: E402
import project_lock  # noqa: E402
import typst_paths  # noqa: E402
import validation  # noqa: E402

FORMAT = "woodcore-migration"
LOG_VERSION = 1
# The migration's own folder, in the project's archives: its log, its backup, its reference, what a rollback set aside, and what became of it.
WORKSPACE_PREFIX = "migration-"
LOG_FILE = "moves.json"
BACKUP_FILE = "before.zip"
RESULT_FILE = "result.json"
REFERENCE_DIR = "ref"
ROLLED_BACK_DIR = "rolled-back"
# The files a report's folder keeps beside its entry and a project in three documents keeps at its top, shared by the three.
# The form's `Template/` folder (calc/forms.py), which a report alone written with a form carries beside its config.typ, goes up with them -- see `plan`, where it is moved like Images/ and RFEM-Export/.
# title.typ is moved up where a report alone carries one, and is no reason to refuse where it carries none: the migration writes the standard one at the top of the project then (`ensure_title`), for the two documents it makes, and leaves the report's own entry, and the title page written in it, as they are.
SHARED_FILES = (project.CONFIG_FILE, project.COMMANDS_FILE, project.REFERENCES_FILE, project.TITLE_FILE)
# What a build or a test leaves in a report's folder: moved with the folder, never read as the report's own.
DEBRIS = {"__pycache__", ".render-cache", ".preview", ".probe"}
# The variables the report's PDF carries (lib/calc-engine.typ, calc/variables.py ATTACHMENT): matched by its basename, Typst naming the attachment after the path of the file that attaches it.
ATTACHMENT = "woodcore-variables.json"
# How long one compile may take before the migration gives it up -- a report of a few hundred pages compiles in well under a minute.
COMPILE_TIMEOUT = 900
# A rename refused by a file another program holds for a moment -- NextCloud syncing, an antivirus reading a PDF just written -- is tried again, this often and this far apart.
RENAME_TRIES = 20
RENAME_PAUSE = 0.25

TINYMIST_REMINDER = (
    "Tinymist: the Typst root is now the project's own folder. Open that folder in VS Code (Woodcore's «Ouvrir dans "
    "VS Code» does), and pin as the main file the entry of the document you are writing -- {rs}, {cu} or {bp} -- with "
    "«Typst: Pin the main file»: one is pinned at a time, and a section compiled on its own exports a stray PDF."
)


# The Typst root stated for Tinymist in the project's `.vscode/settings.json` (the engineer's safety net, 30.09.2026): the folder VS Code was opened on, which the VS Code extension substitutes before Tinymist reads it -- Tinymist wants an absolute root and refuses a relative one, so "." would not do.
ROOT_PATH_KEY = "tinymist.rootPath"
ROOT_PATH_VALUE = "${workspaceFolder}"
ROOT_PATH_COMMENT = ("// The Typst root is this project's folder, the one VS Code was opened on (Woodcore's «Ouvrir dans VS Code» opens it): "
                     "every document imports \"/commands.typ\" and a picture \"/Images/…\" from it. Added by Woodcore's migration into three documents.")
# The settings a project that has none is given: the template's own, which states the root and says why.
TEMPLATE_SETTINGS = project.APP_ROOT / "templates" / "projet" / ".vscode" / "settings.json"


class MigrationError(project.ProjectError):
    """A migration refused, or one that failed and was undone. `code` says which (`refused`, `failed`, `rollback_refused`, `rollback_incomplete`), `refusals` lists the reasons a migration was refused (engine.Note, each with its own code), `diffs` what the verification found, and `workspace` the folder that holds the log, the backup and result.json -- None where nothing was begun."""

    def __init__(self, code, message, refusals=(), diffs=(), workspace=None):
        super().__init__(message)
        self.code = code
        self.refusals = list(refusals)
        self.diffs = list(diffs)
        self.workspace = workspace


def _note(code, text, **args):
    return engine.Note(code, text, **args)


# --- paths ----------------------------------------------------------------------------------------

def _key(path):
    """What two paths are compared by: case and separators as Windows counts them, without asking the disk -- a path may be where it was or already where it is going."""
    return os.path.normcase(os.path.abspath(os.fspath(path)))


def _is_under(path, folder):
    """Whether `path` is `folder` or lies inside it."""
    k, f = _key(path), _key(folder)
    return k == f or k.startswith(f.rstrip(os.sep) + os.sep)


def _where(path, pairs):
    """Where `path` lies once every (old, new) of `pairs` has moved: under its longest moved ancestor, or where it is."""
    best = None
    for old, new in pairs:
        if _is_under(path, old) and (best is None or len(_key(old)) > len(_key(best[0]))):
            best = (old, new)
    path = Path(os.path.abspath(os.fspath(path)))
    if best is None:
        return path
    old, new = best
    return Path(os.path.abspath(os.fspath(new))).joinpath(*path.parts[len(Path(os.path.abspath(os.fspath(old))).parts):])


def _rel(root, path):
    """`path` as a `/`-separated path from `root`, for the log and a message."""
    return Path(os.path.abspath(os.fspath(path))).relative_to(Path(os.path.abspath(os.fspath(root)))).as_posix()


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _sha_file(path):
    return _sha(Path(path).read_bytes())


def _retrying(action, *args):
    """`action(*args)`, tried again for a few seconds where Windows refuses it because another program holds the file for a moment -- NextCloud syncing a file just written or just moved, an antivirus reading a PDF just compiled. Found on the tests' own tree, which lies in NextCloud as the engineer's project does: `os.replace` onto the log was refused once, mid-migration."""
    for attempt in range(RENAME_TRIES):
        try:
            return action(*args)
        except PermissionError:
            if attempt == RENAME_TRIES - 1:
                raise
            time.sleep(RENAME_PAUSE)


def _write_bytes(path, data):
    """`data` written beside `path` and moved into place, so that a failure leaves the old file whole -- what typst_paths.write_text does, and what every write of the migration goes through, the log, the project file and the rewritten `.typ` alike."""
    path = Path(path)
    part = path.with_name(path.name + ".part")
    _retrying(part.write_bytes, data)
    _retrying(os.replace, part, path)


def _write_json(path, data):
    """`data` written beside `path` and moved into place: a log read after a crash is one or the other, never half of one. LF, two-space indent, the text as it is."""
    _write_bytes(path, (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


def _rename(source, target):
    """`os.rename`, tried again where another program holds a file under it for a moment (`_retrying`) -- and nothing else: a rename that would copy is not a rename."""
    _retrying(os.rename, source, target)


# --- what a migration will do ---------------------------------------------------------------------

@dataclass
class Move:
    """One rename: what, from where, to where."""
    source: Path
    target: Path
    what: str


@dataclass
class Rewrite:
    """One `.typ` of the report rewritten: where it lies before the moves and after, the SHA-256 of what it holds now, the text it will hold, and what changes in it (typst_paths.Change)."""
    file_old: Path
    file_new: Path
    sha_before: str
    text: str
    changes: list


@dataclass
class Create:
    """One of the two documents made: its mode, its folder, its entry file's name and the template it is made from."""
    mode: str
    folder: Path
    entry: str
    template: str


@dataclass
class VsCode:
    """`.vscode/settings.json` as the migration will write it: its path, the text, the `tinymist.outputPath` that follows the report's folder ((old, new), or None), whether `tinymist.rootPath` is added, and whether the file is made where the project had none."""
    path: Path
    text: str
    output_path: tuple = None
    root_path: bool = False
    created: bool = False


@dataclass
class Plan:
    """What a migration of `here` would do, read and never written: the moves in their order, the rewrites, the documents made, the new layout and the new `.woodcore` text -- and, where it cannot be done, `refusals`."""
    here: project.Project
    language: str = ""
    folders: dict = field(default_factory=dict)
    entries: dict = field(default_factory=dict)
    old_report_dir: Path = None
    new_report_dir: Path = None
    moves: list = field(default_factory=list)
    rewrites: list = field(default_factory=list)
    creates: list = field(default_factory=list)
    layout: dict = field(default_factory=dict)
    data: dict = field(default_factory=dict)
    woodcore_text: str = None
    woodcore_route: str = ""
    vscode: VsCode = None
    refusals: list = field(default_factory=list)
    notes: list = field(default_factory=list)

    @property
    def root(self):
        return self.here.root

    @property
    def moved(self):
        """{old: new} of every rename, what typst_paths.rewrite is given."""
        return {m.source: m.target for m in self.moves}

    @property
    def pairs(self):
        """(old, new) of every rename, for `_where`."""
        return [(m.source, m.target) for m in self.moves]


def _report_typs(old, generated):
    """Every `.typ` of the report's folder but the engine's own, which moves whole and whose paths stay true, and the debris a build or a test leaves."""
    out = []
    for path in sorted(old.rglob("*.typ")):
        if not path.is_file() or _is_under(path, generated):
            continue
        parts = path.relative_to(old).parts
        if any(part in DEBRIS or part.startswith((".project-", ".settings-")) for part in parts):
            continue
        out.append(path)
    return out


def _language(here, language, p):
    """The language the two new documents and the three folders are named in: `language` where given, else the document language config.typ states beside the report, else German's."""
    if language is not None:
        if language not in documents.LANGUAGES:
            p.refusals.append(_note("bad_language", f"the language {language!r} is none of {', '.join(documents.LANGUAGES)}", language=language))
            return None
        return language
    import templates
    stated = templates.read_languages(here.report_typ)[0]
    if stated in documents.LANGUAGES:
        return stated
    if stated:
        p.notes.append(f"config.typ states the language {stated!r}, none of {', '.join(documents.LANGUAGES)}: the folders are named in German")
    return documents.DEFAULT_LANGUAGE


def _members(text, start=0):
    """The members of the JSON object that opens at `start` (after white), as [(key, key_start, value_start, value_end)] -- the positions a textual edit needs, which json.loads throws away. Raises ValueError where the text is not an object there."""
    decoder = json.JSONDecoder()
    ws = re.compile(r"\s*")
    i = ws.match(text, start).end()
    if i >= len(text) or text[i] != "{":
        raise ValueError(f"no object at {i}")
    i = ws.match(text, i + 1).end()
    out = []
    if i < len(text) and text[i] == "}":
        return out, i + 1
    while True:
        key_start = i
        key, i = json.decoder.scanstring(text, i + 1)
        i = ws.match(text, i).end()
        if text[i] != ":":
            raise ValueError(f"no ':' after the key {key!r}")
        i = ws.match(text, i + 1).end()
        value_start = i
        _value, i = decoder.raw_decode(text, i)
        out.append((key, key_start, value_start, i))
        i = ws.match(text, i).end()
        if text[i] == ",":
            i = ws.match(text, i + 1).end()
            continue
        if text[i] == "}":
            return out, i + 1
        raise ValueError(f"unexpected {text[i]!r} at {i}")


def _indent_of(text, position):
    """The white a line begins with, for the line `position` lies on."""
    line_start = text.rfind("\n", 0, position) + 1
    return re.match(r"[ \t]*", text[line_start:]).group()


def woodcore_text(raw, layout):
    """The text of a project file with `layout` stated -- and the route taken: `(text, "canonical" | "textual")`. Until 0.117 it also made `gui.rfem_models` follow the files they named; the RFEM import was retired then (archive/rfem/), and a retired key is left as it is.

    **Canonical** where the file is Woodcore's own form -- `json.dumps(data, ensure_ascii=False, indent=2)` and a newline, as `project.write` and `project.update` write it -- and then it is written again in that form, which loses nothing, keeping its own line endings. **Textual** otherwise, a file written or edited by hand: the `layout` member's value is replaced where the file has one and appended where it has none, indented as the file indents; every other byte stays, since reserialising a hand-written file silently drops what the serialiser does not know. Raises ValueError where neither yields the data meant (the caller refuses the migration then, before anything is moved).
    """
    bom = "﻿" if raw.startswith("﻿") else ""
    body = raw[len(bom):]
    newline = "\r\n" if "\r\n" in body else "\n"
    lf = body.replace("\r\n", "\n")
    data = json.loads(lf)
    expected = dict(data)
    expected["layout"] = dict(layout)
    if lf == json.dumps(data, ensure_ascii=False, indent=2) + "\n" and "\r" not in lf:
        text = (json.dumps(expected, ensure_ascii=False, indent=2) + "\n").replace("\n", newline)
        return bom + text, "canonical"

    members, _end = _members(body)
    edits = []
    by_key = {m[0]: m for m in members}
    # The file's own indentation: that of its first member's line, which is also one level's -- two spaces, four, a tab -- and two spaces for a file written on one line.
    member_indent = _indent_of(body, members[0][1]) if members else ""
    dumped = json.dumps(dict(layout), ensure_ascii=False, indent=member_indent or "  ").replace("\n", newline + member_indent)
    if "layout" in by_key:
        _k, _ks, vs, ve = by_key["layout"]
        edits.append((vs, ve, dumped))
    elif members:
        last_end = members[-1][3]
        edits.append((last_end, last_end, "," + newline + member_indent + '"layout": ' + dumped))
    else:
        raise ValueError("the project file holds no member to put the layout after")
    for s, e, new in sorted(edits, key=lambda x: x[0], reverse=True):
        body = body[:s] + new + body[e:]
    if json.loads(body.replace("\r\n", "\n")) != expected:
        raise ValueError("the textual edit of the project file does not give the data meant")
    return bom + body, "textual"


_OUTPUT_PATH = re.compile(r'^(?P<head>[ \t]*"tinymist\.outputPath"[ \t]*:[ \t]*")(?P<value>(?:[^"\\\r\n]|\\.)*)(?P<tail>")', re.M)


def vscode_text(raw, old_rel, new_rel):
    """`.vscode/settings.json` with its `tinymist.outputPath` following the report's folder -- `(text, (old value, new value))` -- or None where it states none, or one that does not point into the old folder: then the file is not touched at all. A line commented out (`//`) is not a setting and is left alone, the pattern reading only a line that begins with the key."""
    found = _OUTPUT_PATH.search(raw)
    if found is None:
        return None
    value = found.group("value")
    pattern = re.compile(r"(^|(?<=[/\\]))" + re.escape(old_rel) + r"(?=$|[/\\])")
    if not pattern.search(value):
        return None
    new_value = pattern.sub(new_rel.replace("\\", "\\\\"), value)
    return raw[:found.start("value")] + new_value + raw[found.end("value"):], (value, new_value)


def _jsonc_skip(text, i):
    """The position after the white and the comments (`//` to the end of the line, `/* … */`) that start at `i` in a JSONC text -- VS Code's settings.json."""
    n = len(text)
    while i < n:
        if text[i] in " \t\r\n﻿":
            i += 1
        elif text.startswith("//", i):
            end = text.find("\n", i)
            i = n if end < 0 else end + 1
        elif text.startswith("/*", i):
            end = text.find("*/", i + 2)
            if end < 0:
                raise ValueError("a /* comment is never closed")
            i = end + 2
        else:
            return i
    return i


def jsonc_plain(text):
    """A JSONC text -- VS Code's settings.json, with its `//` and `/* */` comments and its trailing commas -- as plain JSON, for json.loads to read: the comments dropped and a comma before a closing bracket dropped, strings left exactly as they are."""
    out, i, n = [], 0, len(text)
    while i < n:
        c = text[i]
        if c == '"':
            j = i + 1
            while j < n and text[j] != '"':
                j += 2 if text[j] == "\\" else 1
            if j >= n:
                raise ValueError("a string is never closed")
            out.append(text[i:j + 1])
            i = j + 1
        elif text.startswith("//", i) or text.startswith("/*", i):
            i = _jsonc_skip(text, i)
            out.append(" ")
        elif c == ",":
            k = _jsonc_skip(text, i + 1)
            if k < n and text[k] in "}]":
                out.append(" ")
            else:
                out.append(c)
            i += 1
        else:
            out.append(c)
            i += 1
    return "".join(out)


def vscode_root_text(raw):
    """`.vscode/settings.json` stating Tinymist's root -- `"tinymist.rootPath": "${workspaceFolder}"`, the project's folder VS Code was opened on -- or None where it states a root already, whatever it is: the engineer's own setting is his.

    The member is inserted **as a line of its own**, with a comment saying why, right after the object's opening brace, at the indentation of what follows it and with the file's own line endings -- every other byte kept, the comments and a trailing comma included, since the file is JSONC and is never reserialised. Raises ValueError where the file does not read as one JSON object, or where the text inserted would not give that object with the member added (the caller then leaves the file as it is and says so)."""
    bom = "﻿" if raw.startswith("﻿") else ""
    body = raw[len(bom):]
    data = json.loads(jsonc_plain(body))
    if not isinstance(data, dict):
        raise ValueError("it is not a JSON object")
    if ROOT_PATH_KEY in data:
        return None
    brace = _jsonc_skip(body, 0)
    if brace >= len(body) or body[brace] != "{":
        raise ValueError("it does not open with {")
    following = _jsonc_skip(body, brace + 1)
    empty = following < len(body) and body[following] == "}"
    newline = "\r\n" if "\r\n" in body else "\n"
    first = brace + 1
    while first < len(body) and body[first] in " \t\r\n":
        first += 1
    if "\n" in body[brace:first] and first < len(body) and body[first] != "}":
        indent = _indent_of(body, first)
    else:
        indent = "  "
    member = f'"{ROOT_PATH_KEY}": "{ROOT_PATH_VALUE}"' + ("" if empty else ",")
    # a blank line after it where the file goes on on a line of its own, as the template parts its settings; the rest of a file written on one line put on the next
    parted = empty or body[brace + 1:].lstrip(" \t").startswith(("\r\n", "\n"))
    inserted = newline + indent + ROOT_PATH_COMMENT + newline + indent + member + (newline if parted else newline + indent)
    text = body[:brace + 1] + inserted + body[brace + 1:]
    if json.loads(jsonc_plain(text)) != {ROOT_PATH_KEY: ROOT_PATH_VALUE, **data}:
        raise ValueError("the line inserted does not give the settings meant")
    return bom + text


def _vscode_plan(settings, old_rel, new_rel, notes):
    """What becomes of the project's `.vscode/settings.json` (a VsCode), or None where it is left as it is: its `tinymist.outputPath` following the report's folder, `tinymist.rootPath` stated where the file states no root, and the template's settings where the project has none. A file that cannot be read as JSONC is left alone, and `notes` says so -- a safety net missing is no reason to refuse a migration."""
    if not settings.is_file():
        try:
            text = typst_paths.read_text(TEMPLATE_SETTINGS)
        except OSError:
            text = "{" + "\n  " + ROOT_PATH_COMMENT + "\n  " + f'"{ROOT_PATH_KEY}": "{ROOT_PATH_VALUE}"' + "\n}\n"
        return VsCode(settings, text, None, True, True)
    raw = typst_paths.read_text(settings)
    text, output = raw, None
    found = vscode_text(raw, old_rel, new_rel)
    if found is not None:
        text, output = found
    try:
        rooted = vscode_root_text(text)
    except ValueError as exc:
        notes.append(f".vscode/settings.json does not read as JSON ({exc}): its {ROOT_PATH_KEY} is not stated -- set it to {ROOT_PATH_VALUE} by hand")
        rooted = None
    if rooted is not None:
        text = rooted
    if text == raw:
        return None
    return VsCode(settings, text, output, rooted is not None, False)


def plan(here, language=None, names=None, *, strict=False):
    """What migrating `here` would do, and what stands in its way -- read and never written.

    `here` is a Project or the path of its `.woodcore`. `language` names the language of the folders and of the two new documents (de, fr, en), else config.typ's `doc-lang` beside the report, else German. `names` names the three folders -- {mode: folder}, or three in the order CU BP RS -- else the language's own (documents.MODE_FOLDERS). The report keeps its entry file's name; the two new documents are named after themselves in the language (documents.ENTRY_NAMES); the sources and the archives stay where the project keeps them.

    The static refusals are `refusals`: a project already in three documents, a report at the top of the project, the sources or the archives inside the report's folder, a folder name that is refused or taken, a place a move would put something where something already is, a path literal of the report that cannot be made to follow its target, a project file whose layout cannot be written. What depends on the moment -- the lock, the engine, Typst -- is `check`'s.

    ⚠️ A literal whose target is not there **inside the export's folder** -- the engine's own files, which a project whose engine was never copied in does not have yet -- is a note and not a refusal, since the migration's reference step writes them (the engine synced, the export run) before anything moves. `strict` refuses it like any other: it is what `run` plans again with once the reference is taken, and where such a literal still names nothing, nothing moves.
    """
    here = here if isinstance(here, project.Project) else project.Project.load(here)
    p = Plan(here=here)
    refuse = p.refusals.append
    name = here.file.name
    if here.has_modes:
        refuse(_note("already_modes", f"{name} is already laid out in three documents: there is nothing to migrate", project=name))
        return p
    top = here.root
    old = here.report_typ.parent
    p.old_report_dir = old
    if not here.report_typ.is_file():
        refuse(_note("no_report", f"{here.rel(here.report_typ)} is not there: a project is migrated with its report", report=here.rel(here.report_typ)))
        return p
    if _key(old) == _key(top):
        refuse(_note("report_at_top", f"{name}'s report lies at the top of the project: its folder is the project's, and there is no report folder to become the third document's", project=name))
        return p
    for key, path in (("sources", here.sources_dir), ("archives", here.archives_dir)):
        if _is_under(path, old):
            refuse(_note(f"{key}_inside", f"layout.{key} ({here.layout[key]}) lies inside the report's folder ({here.rel(old)}), which the migration renames -- move it out of the report's folder first", folder=here.layout[key]))
    generated = here.generated_dir
    if _key(generated) == _key(old):
        refuse(_note("generated_is_report", f"layout.generated is the report's folder itself ({here.rel(old)}): the export has no folder of its own to move up", folder=here.rel(old)))
    if p.refusals:
        return p

    lang = _language(here, language, p)
    if lang is None:
        return p
    p.language = lang
    if names is None:
        folders = documents.folders_for(lang)
    elif isinstance(names, dict):
        folders = {**documents.folders_for(lang), **names}
    else:
        folders = list(names)
    entries = {mode: documents.ENTRY_NAMES[lang][mode] for mode in ("cu", "bp")}
    try:
        layout = documents.modes_layout(folders, entries, rs_entry=here.report_typ.name)
    except project.ProjectError as exc:
        refuse(_note("bad_names", str(exc), names=str(folders)))
        return p
    layout["sources"] = here.layout["sources"]
    layout["archives"] = here.layout["archives"]
    layout = project.full_layout(layout)
    p.layout = layout
    p.folders = {mode: PurePosixPath(layout[project.ENTRY_KEYS[mode]]).parent.as_posix() for mode in project.MODES}
    p.entries = {mode: PurePosixPath(layout[project.ENTRY_KEYS[mode]]).name for mode in project.MODES}
    shared = {documents.GENERATED_FOLDER, project.IMAGES_FOLDER, project.TEMPLATE_FOLDER, project.FORMULAS_FOLDER, *SHARED_FILES, here.file.name,
              PurePosixPath(here.layout["sources"]).parts[0], PurePosixPath(here.layout["archives"]).parts[0]}
    shared = {s.casefold() for s in shared}
    for mode, folder in p.folders.items():
        if PurePosixPath(folder).parts[0].casefold() in shared:
            refuse(_note("bad_names", f"the folder of the {documents.MODE_NAMES['en'][mode].lower()} ({folder}) is the name of something the three documents share at the top of the project", folder=folder))
    if p.refusals:
        return p

    # The renames, in their order: what the three share first, the report's folder last.
    new = top / p.folders["rs"]
    p.new_report_dir = new
    moves = [Move(generated, top / documents.GENERATED_FOLDER, "the export and the engine")]
    for folder, what in ((project.IMAGES_FOLDER, "the pictures"), (project.TEMPLATE_FOLDER, "the form (Template/)"), (project.FORMULAS_FOLDER, "the calculation domains (Formules/)")):
        if (old / folder).is_dir():
            moves.append(Move(old / folder, top / folder, what))
    for file in SHARED_FILES:
        if (old / file).is_file():
            moves.append(Move(old / file, top / file, file))
    if _key(old) != _key(new) or old.name != new.name:
        moves.append(Move(old, new, "the report's folder"))
    p.moves = moves
    for move in moves:
        if _key(move.source) != _key(move.target) and move.target.exists():
            refuse(_note("collision", f"{here.rel(move.target)} is there already: {move.what} cannot be moved there -- rename or move it first", path=here.rel(move.target)))
    for mode in ("cu", "bp"):
        folder = top / p.folders[mode]
        if folder.exists():
            refuse(_note("collision", f"{here.rel(folder)} is there already: the {documents.MODE_NAMES['en'][mode].lower()} cannot be made in it", path=here.rel(folder)))

    # The report's paths, rewritten where they would stop reaching their targets -- read now, written after the moves.
    for file in _report_typs(old, generated):
        file_new = _where(file, p.pairs)
        text = typst_paths.read_text(file)
        new_text, changes, unresolved = typst_paths.rewrite(text, file, file_new, old, top, p.moved)
        for item in unresolved:
            literal = item.literal
            target = old / literal.value.lstrip("/") if (literal.root_relative or literal.value.startswith("/")) else file.parent / literal.value
            if not strict and _is_under(target, generated):
                p.notes.append(f"{here.rel(file)}: {literal.value!r} names nothing yet inside the export's folder -- the reference step writes it, and the migration plans again then")
                continue
            refuse(_note("unrewritable", f"{here.rel(file)}: {item.reason}", file=here.rel(file), literal=literal.value, reason=item.reason))
        if new_text != text:
            p.rewrites.append(Rewrite(file, file_new, _sha(text.encode("utf-8")), new_text, changes))

    # The project file.
    raw_bytes = here.file.read_bytes()
    try:
        raw = raw_bytes.decode("utf-8")
        data = json.loads(raw.lstrip("﻿"))
        text, route = woodcore_text(raw, layout)
        new_data = json.loads(text.lstrip("﻿"))
        validation.validate_structure(new_data, "woodcore-project")
        project.Project(here.file, new_data)
    except (ValueError, KeyError, IndexError, validation.ValidationError) as exc:
        refuse(_note("woodcore_unrewritable", f"{name}: its layout cannot be written ({exc})", project=name, reason=str(exc)))
    else:
        p.woodcore_text, p.woodcore_route, p.data = text, route, new_data

    # Tinymist's settings: its root stated, and its output following the report's folder where it named it.
    p.vscode = _vscode_plan(top / ".vscode" / "settings.json", _rel(top, old), p.folders["rs"], p.notes)

    # The two documents, made from their templates.
    import doc_templates
    for mode in ("cu", "bp"):
        try:
            template = doc_templates.find(doc_templates.default_ref(mode), mode)
        except doc_templates.DocTemplateError as exc:
            refuse(_note("no_template", f"no template for the {documents.MODE_NAMES['en'][mode].lower()}: {exc}", mode=mode))
            continue
        if lang not in template.languages:
            refuse(_note("no_template", f"{template.ref} exists in {', '.join(template.languages)} and not in {lang}", mode=mode))
            continue
        p.creates.append(Create(mode, top / p.folders[mode], p.entries[mode], template.ref))
    return p


def check(p, *, update_engine=False, lock_owner=None):
    """The refusals of plan `p`, and what depends on the moment: the project held by another window (`lock_owner` names the process that holds it and is migrating it -- Woodcore's window, which runs the migration as a child process), the engine newer than this program or not one to replace without being told (`update_engine`), and Typst or pypdf missing. Each an engine.Note; an empty list is a migration that may run."""
    refusals = list(p.refusals)
    here = p.here
    me = project_lock.whoami()
    if lock_owner is not None:
        me["pid"] = int(lock_owner)
    other = project_lock.holder(here, me)
    if other is not None:
        refusals.append(_note("locked", f"{here.file.name} is open in {other.get('user', '?')}'s window on {other.get('host', '?')} since {other.get('since', '?')} -- close it there first",
                              user=other.get("user", "?"), host=other.get("host", "?"), since=other.get("since", "?")))
    if not here.has_modes:
        state, detail = project.engine_state(here)
        if state == "own":
            refusals.append(_note("engine_own", f"{here.file.name}'s export is the program's own folder: a project laid out before v0.82 cannot be migrated", project=here.file.name))
        elif state == "newer" or (state in project.ASKED and not update_engine):
            refusals.append(_note("engine_" + ("newer" if state == "newer" else "asked"), project.engine_message(state, detail).replace("export with --update-engine", "migrate with --update-engine"), state=state, detail=detail))
    executable = project.typst_executable()
    if not (Path(executable).is_file() or shutil.which(executable)):
        refusals.append(_note("no_typst", "no Typst to compile the report with: the migration compares the report before and after, and cannot without it"))
    if importlib.util.find_spec("pypdf") is None:
        refusals.append(_note("no_pypdf", "pypdf is not installed: the migration reads the report's pages to compare them, and cannot without it"))
    return refusals


def describe(p, refusals=None):
    """The plan as lines of English, for a dry run and for the window's dialog."""
    here = p.here
    out = [f"Migration of {here.name} ({here.file.name}) into three documents" + (f", named in {p.language}:" if p.language else ":")]
    if p.moves:
        out.append("  moves -- renamed, nothing copied, nothing deleted:")
        out += [f"    {here.rel(m.source)} -> {_rel(here.root, m.target)}   ({m.what})" for m in p.moves]
    if p.creates:
        out.append("  creates:")
        out += [f"    {_rel(here.root, c.folder)}/{c.entry}   (from {c.template})" for c in p.creates]
    if p.rewrites:
        count = sum(len(r.changes) for r in p.rewrites)
        out.append(f"  rewrites -- {count} path literal(s) in {len(p.rewrites)} file(s):")
        for r in p.rewrites:
            out.append(f"    {_rel(here.root, r.file_new)}:")
            out += [f"      {c.literal.kind} {c.old!r} -> {c.new!r}" for c in r.changes]
    if p.layout:
        out.append(f"  {here.file.name} ({p.woodcore_route or 'not writable'}) -- the layout stated in full:")
        out += [f"    {key}: {value}" for key, value in p.layout.items()]
    if p.vscode and p.vscode.created:
        out.append(f"  .vscode/settings.json: made from the template's, stating {ROOT_PATH_KEY} {ROOT_PATH_VALUE}")
    elif p.vscode:
        if p.vscode.output_path:
            out.append(f"  .vscode/settings.json: tinymist.outputPath {p.vscode.output_path[0]!r} -> {p.vscode.output_path[1]!r}")
        if p.vscode.root_path:
            out.append(f"  .vscode/settings.json: {ROOT_PATH_KEY} {ROOT_PATH_VALUE} added, as a line of its own")
    else:
        out.append(f"  .vscode/settings.json: untouched (it states its {ROOT_PATH_KEY} already, and no tinymist.outputPath into the report's folder)")
    out += [f"  note: {n}" for n in p.notes]
    refusals = p.refusals if refusals is None else refusals
    if refusals:
        out.append("  REFUSED:")
        out += [f"    [{r.code}] {r}" for r in refusals]
    else:
        out.append("  nothing stands in the way")
    return out


# --- the reference and the comparison ------------------------------------------------------------

def _compile(args, here):
    """`typst` with `args`, started in project `here`'s Typst root as every compile is (calc/stamps.py _read_deps): None where it compiled, else what Typst said."""
    try:
        done = proc.run([project.typst_executable(), *args], capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=COMPILE_TIMEOUT, cwd=here.typst_root)
    except subprocess.TimeoutExpired:
        return f"typst did not finish in {COMPILE_TIMEOUT} s"
    except OSError as exc:
        return f"typst could not be started ({exc})"
    if done.returncode != 0:
        return (done.stderr or done.stdout).strip() or f"typst exited {done.returncode}"
    return None


def read_pdf(path):
    """What the comparison reads of a compiled PDF: {"pages": [text of each page], "outline": [{title, page, level}], "attachment": the variables it carries, or None}."""
    logging.getLogger("pypdf").setLevel(logging.ERROR)
    from pypdf import PdfReader
    reader = PdfReader(str(path))
    pages = [(page.extract_text() or "") for page in reader.pages]
    outline = []

    def walk(items, level):
        for item in items:
            if isinstance(item, list):
                walk(item, level + 1)
                continue
            try:
                page = reader.get_destination_page_number(item)
            except Exception:  # broad: pypdf raises a family of its own -- a bookmark that cannot be followed has no page
                page = None
            outline.append({"title": " ".join(str(getattr(item, "title", "")).split()), "page": page, "level": level})

    try:
        walk(reader.outline, 1)
    except Exception:  # broad: pypdf's family again -- an outline that cannot be read compares as none
        outline = []
    attachment = None
    try:
        attachments = reader.attachments
        named = [n for n in attachments if Path(str(n)).name == ATTACHMENT]
        if named:
            attachment = json.loads(bytes(attachments[named[0]][0]).decode("utf-8"))
    except Exception:  # broad: pypdf's family, or an attachment that is not JSON -- compared as none
        attachment = None
    return {"pages": pages, "outline": outline, "attachment": attachment}


def _normal(text, dates):
    """A page's text as the comparison reads it: the date the title page prints written the same whichever day it was compiled on, and every run of white one space."""
    for day in dates:
        text = text.replace(day, "<today>")
    return re.sub(r"\s+", " ", text).strip()


def _excerpt(a, b):
    k = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
    return f"reference «…{a[max(0, k - 50):k + 50]}…» / now «…{b[max(0, k - 50):k + 50]}…»"


def compare_pdf(reference, current, dates):
    """What differs between the report as it printed before the migration (`reference`, read_pdf's) and after (`current`), the dates of `dates` allowed to be today's: [] where nothing does, else a sentence per difference, the pages first."""
    diffs = []
    ref_pages, cur_pages = reference["pages"], current["pages"]
    if len(ref_pages) != len(cur_pages):
        diffs.append(f"the report has {len(cur_pages)} page(s), and had {len(ref_pages)}")
    for number, (a, b) in enumerate(zip(ref_pages, cur_pages), 1):
        na, nb = _normal(a, dates), _normal(b, dates)
        if na != nb:
            diffs.append(f"page {number} prints something else: {_excerpt(na, nb)}")
            if len(diffs) >= 6:
                break
    ref_outline = reference["outline"]
    if ref_outline != current["outline"]:
        diffs.append(f"the outline differs: {len(ref_outline)} heading(s) before, {len(current['outline'])} after"
                     + ("" if len(ref_outline) != len(current["outline"]) else
                        " -- first " + next(f"{x} / {y}" for x, y in zip(ref_outline, current["outline"]) if x != y)))
    a, b = reference.get("attachment"), current.get("attachment")
    if (a is None) != (b is None):
        diffs.append("the variables the PDF carries: " + ("none before, some after" if a is None else "some before, none after"))
    elif a is not None and a != b:
        diffs.append("the variables the PDF carries differ")
    return diffs


def compare_data(reference, current, allowed_new=()):
    """What differs between the export kept before the migration (`reference`, a folder) and the one written after (`current`), byte for byte: [] where nothing does. A file of `allowed_new` (a name relative to data/) may be written after and not before -- the journals of the two new documents."""
    reference, current = Path(reference), Path(current)
    ref = {p.relative_to(reference).as_posix(): p for p in reference.rglob("*") if p.is_file()}
    cur = {p.relative_to(current).as_posix(): p for p in current.rglob("*") if p.is_file()}
    diffs = []
    for rel in sorted(set(ref) | set(cur)):
        if rel not in cur:
            diffs.append(f"data/{rel} was exported before the migration and is not after it")
            continue
        if rel not in ref:
            if rel not in allowed_new:
                diffs.append(f"data/{rel} is exported after the migration and was not before it")
            continue
        if ref[rel].read_bytes() == cur[rel].read_bytes():
            continue
        diffs.append(f"data/{rel} differs from the export made before the migration")
    return diffs


# --- the log --------------------------------------------------------------------------------------

def _workspace(here):
    """A new folder for this migration in the project's archives, `migration-<yymmdd-HHhMM>`, `-2`, `-3` where one of that minute is there."""
    base = here.archives_dir
    base.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%y%m%d-%Hh%M")
    n = 1
    while True:
        ws = base / f"{WORKSPACE_PREFIX}{stamp}" if n == 1 else base / f"{WORKSPACE_PREFIX}{stamp}-{n}"
        try:
            ws.mkdir()
            return ws
        except FileExistsError:
            n += 1


class _Log:
    """moves.json, the write-ahead log: written whole after every step, so that a rollback -- this process's own, or one asked for after a crash -- knows what was begun and what was done."""

    def __init__(self, workspace, record):
        self.workspace = workspace
        self.record = record
        self.save()

    def save(self):
        _write_json(self.workspace / LOG_FILE, self.record)

    def state(self, state):
        self.record["state"] = state
        self.save()


def _backup(zip_path, root, files, folder):
    """before.zip: `files` and the whole of `folder`, its folders included, named from `root` -- what a rollback puts back where it differs."""
    with zipfile.ZipFile(zip_path, "x", compression=zipfile.ZIP_DEFLATED) as z:
        for file in files:
            if file.is_file():
                z.write(file, _rel(root, file))
        z.write(folder, _rel(root, folder))
        for path in sorted(folder.rglob("*")):
            z.write(path, _rel(root, path))


def _result(workspace, data):
    _write_json(Path(workspace) / RESULT_FILE, {**data, "finished": datetime.now().isoformat(timespec="seconds")})


# --- running it -----------------------------------------------------------------------------------

def _say(log, text):
    if log is not None:
        log(f"migrate: {text}")


def _stamps():
    """calc/stamps.py where it is there and records a compile (work package 1.2), else None: the migration writes a document's stamp when it can and never fails for want of one."""
    try:
        import stamps
    except ImportError:
        return None
    return stamps if callable(getattr(stamps, "record", None)) else None


def run(here, *, language=None, names=None, skip_data=False, update_engine=False, dry_run=False, lock_owner=None, log=print, archive=True):
    """Migrates `here` (a Project or its `.woodcore`) into three documents, proves it, and gives back what became of it -- result.json's content -- or, with `dry_run`, the Plan and nothing written.

    `language` and `names` are `plan`'s; `skip_data` compares no export (a project that has no Positionen.xlsx has none to run) and only brings the engine up to date; `update_engine` replaces an engine another version wrote or someone edited, before the reference is taken; `lock_owner` is the process that holds the project's lock and is migrating it (Woodcore's window); `log` receives a line per step; `archive` archives the report once migrated, where calc/tools/archive_export.py knows the three documents.

    Raises MigrationError: `refused`, before anything is written, with the refusals; `failed`, after everything was undone, with the reason and what the verification found; `rollback_incomplete` where undoing it did not go through, before.zip then holding what was.
    """
    here = here if isinstance(here, project.Project) else project.Project.load(here)
    p = plan(here, language=language, names=names)
    refusals = check(p, update_engine=update_engine, lock_owner=lock_owner)
    if dry_run:
        p.refusals = refusals
        for line in describe(p, refusals):
            if log is not None:
                log(line)
        return p
    if refusals:
        raise MigrationError("refused", f"{here.file.name} cannot be migrated: " + "; ".join(refusals), refusals=refusals)

    # The lock: the window's own where it is migrating (`lock_owner`), else this process's for the length of the migration -- and never one left behind by a process gone, which is not this migration's to take over or to remove.
    me = project_lock.whoami()
    if lock_owner is not None:
        me["pid"] = int(lock_owner)
    acquired = project_lock.read(here) is None
    if acquired:
        project_lock.acquire(here, me=me)
    try:
        return _run(here, p, skip_data=skip_data, update_engine=update_engine, log=log, archive=archive)
    finally:
        if acquired:
            project_lock.release(here, me=me)


def _run(here, p, *, skip_data, update_engine, log, archive):
    """The migration itself, once nothing stands in its way: the reference, the backup, the moves, the rewrites, the two documents and the proof -- and everything undone on the first failure."""
    ws = _workspace(here)
    _say(log, f"{here.name}: the migration's folder is {here.rel(ws)}")
    root = here.root
    rs_pdf_after = root / p.layout["pdf"]
    record = {
        "format": FORMAT, "log_version": LOG_VERSION, "state": "backup",
        "project": here.file.name, "archives": here.layout["archives"],
        "started": datetime.now().isoformat(timespec="seconds"),
        "language": p.language, "folders": p.folders,
        "old_report": _rel(root, p.old_report_dir), "new_report": _rel(root, p.new_report_dir),
        "generated": _rel(root, here.generated_dir),
        # the report's PDF in the old layout's place: an output the rollback may put back or set aside without asking
        "outputs": [_rel(root, _where(rs_pdf_after, [(m.target, m.source) for m in p.moves]))],
        "layout_before": here.data.get("layout"), "layout_after": p.layout,
        "moves": [{"from": _rel(root, m.source), "to": _rel(root, m.target), "what": m.what, "state": "planned"} for m in p.moves],
        "rewritten": [], "woodcore": None, "vscode": None,
        "created": [], "seeded": [], "produced": [],
        "backup": None, "skip_data": skip_data,
    }
    book = _Log(ws, record)
    dates = set()
    try:
        # 1. The backup, before anything is written -- the reference's own export and engine update included, so that a migration undone gives the project back exactly as it was found -- and the log written whole.
        settings = root / ".vscode" / "settings.json"
        _say(log, f"backing up the report's folder into {BACKUP_FILE}")
        _backup(ws / BACKUP_FILE, root, [here.file, settings], p.old_report_dir)
        record["backup"] = BACKUP_FILE
        record["woodcore"] = {"sha256_before": _sha_file(here.file), "route": p.woodcore_route}
        if p.vscode:
            record["vscode"] = {"sha256_before": None if p.vscode.created else _sha_file(settings),
                                "created": p.vscode.created, "folder_created": not settings.parent.exists()}
        book.state("reference")

        # 2. The reference: the report as it is written, after any engine update, and the export as it stands.
        ref = ws / REFERENCE_DIR
        ref.mkdir()
        with project.using(here):
            if skip_data:
                written = project.sync_engine(here, update=update_engine)
                if written:
                    _say(log, f"engine written: {', '.join(written)}")
            else:
                import export_all
                _say(log, "the export, as the project stands")
                export_all.run(update_engine=update_engine)
                shutil.copytree(here.data_dir, ref / "data")
        _say(log, "the report compiled as it is written, for the reference")
        dates.add(date.today().strftime("%d.%m.%Y"))
        error = _compile(documents.compile_args(here, "rs", target=ref / "reference.pdf"), here)
        dates.add(date.today().strftime("%d.%m.%Y"))
        if error:
            raise MigrationError("failed", f"the report does not compile as it is written -- the migration compares against it, so it needs one that does:\n{error}")
        reference = read_pdf(ref / "reference.pdf")
        _write_json(ref / "reference.json", reference)
        (ref / "reference.txt").write_text("\n\f\n".join(reference["pages"]), encoding="utf-8")

        # The plan made again, strictly, now that the engine and the export are there: a path the first plan let pass because the reference was to write its target must reach it now, and nothing may have moved since.
        again = plan(here, language=p.language, names=p.folders, strict=True)
        if again.refusals:
            raise MigrationError("failed", "once the reference is taken the migration is refused: " + "; ".join(again.refusals), refusals=again.refusals)
        if [(m.source, m.target) for m in again.moves] != [(m.source, m.target) for m in p.moves] or again.layout != p.layout:
            raise MigrationError("failed", "the report's folder changed while the reference was taken: the moves are not the ones planned")
        p = again
        for rewrite in p.rewrites:
            record["rewritten"].append({"file": _rel(root, rewrite.file_new), "from": _rel(root, rewrite.file_old),
                                        "sha256_before": rewrite.sha_before, "state": "planned",
                                        "changes": [[c.old, c.new] for c in rewrite.changes]})
        book.state("moving")

        # 3. The moves, by rename, in their order.
        for entry, move in zip(record["moves"], p.moves):
            if not move.source.exists() or (move.target.exists() and _key(move.source) != _key(move.target)):
                raise MigrationError("failed", f"{move.what} is not where the plan found it, or {here.rel(move.target)} is taken")
            entry["state"] = "moving"
            book.save()
            _rename(move.source, move.target)
            entry["state"] = "done"
            book.save()
            _say(log, f"moved {entry['from']} -> {entry['to']}")

        # 4. The rewrites: the report's paths, the project file, Tinymist's settings.
        book.state("rewriting")
        for entry, rewrite in zip(record["rewritten"], p.rewrites):
            current = typst_paths.read_text(rewrite.file_new)
            if _sha(current.encode("utf-8")) != rewrite.sha_before:
                raise MigrationError("failed", f"{entry['file']} changed while it was being migrated")
            again, _changes, unresolved = typst_paths.rewrite(current, rewrite.file_old, rewrite.file_new, p.old_report_dir, root, p.moved)
            if again != rewrite.text or unresolved:
                raise MigrationError("failed", f"{entry['file']}: its paths do not rewrite after the moves as they did before them")
            entry["state"] = "writing"
            book.save()
            _write_bytes(rewrite.file_new, rewrite.text.encode("utf-8"))
            entry["sha256_after"] = _sha_file(rewrite.file_new)
            entry["state"] = "done"
            book.save()
        _say(log, f"{len(p.rewrites)} file(s) of the report rewritten")
        if _sha_file(here.file) != record["woodcore"]["sha256_before"]:
            raise MigrationError("failed", f"{here.file.name} changed while it was being migrated")
        record["woodcore"]["state"] = "writing"
        book.save()
        _write_bytes(here.file, p.woodcore_text.encode("utf-8"))
        record["woodcore"]["sha256_after"] = _sha_file(here.file)
        record["woodcore"]["state"] = "done"
        book.save()
        _say(log, f"{here.file.name} states its layout ({p.woodcore_route})")
        if p.vscode:
            path, text = p.vscode.path, p.vscode.text
            if p.vscode.created and path.exists():
                raise MigrationError("failed", ".vscode/settings.json appeared while the project was being migrated")
            if not p.vscode.created and _sha_file(path) != record["vscode"]["sha256_before"]:
                raise MigrationError("failed", ".vscode/settings.json changed while the project was being migrated")
            record["vscode"]["state"] = "writing"
            book.save()
            path.parent.mkdir(parents=True, exist_ok=True)
            _write_bytes(path, text.encode("utf-8"))
            record["vscode"]["sha256_after"] = _sha_file(path)
            record["vscode"]["state"] = "done"
            book.save()

        # 5. The two documents, and the export files they read.
        book.state("creating")
        import doc_templates
        # The title page the two new documents set (`#import "/title.typ": title-page`), Standard's, where the project carries none -- recorded with what was made, so that undoing the migration sets it aside with the two documents. The report's own entry and the title page it writes are left as they are.
        title = root / project.TITLE_FILE
        if not title.exists():
            import project_template
            record["created"].append(_rel(root, title))
            book.save()
            _retrying(shutil.copyfile, project_template.standard_title(), title)
            _say(log, f"made {_rel(root, title)} from Standard")
        for create in p.creates:
            record["created"].append(_rel(root, create.folder))
            book.save()
            doc_templates.instantiate(create.mode, p.language, create.folder, entry_name=create.entry, template=create.template)
            _say(log, f"made {_rel(root, create.folder)}/{create.entry} from {create.template}")
        migrated = project.Project.load(here.file)
        import export_all
        seeded = export_all.seed(migrated)
        record["seeded"] = [_rel(root, migrated.data_dir / name) for name in seeded]
        book.state("verifying")

        # 6. The proof.
        diffs = _verify(migrated, p, ws, reference, dates, skip_data, log)
        if diffs:
            raise MigrationError("failed", f"the migrated project is not the project it was: {diffs[0]}", diffs=diffs)

        # 7. Done: what the migration added to the moved trees, named as the old layout will name it, for a rollback to set aside rather than keep.
        record["produced"] = _produced(ws, root, p)
        book.state("done")
        reminder = TINYMIST_REMINDER.format(**{mode: migrated.rel(migrated.document_typ(mode)) for mode in project.MODES})
        outcome = {
            "ok": True, "project": here.file.name, "workspace": here.rel(ws), "language": p.language,
            "layout": p.layout, "moves": record["moves"], "rewritten": len(p.rewrites), "created": record["created"],
            "seeded": record["seeded"], "skip_data": skip_data, "reminder": reminder,
        }
        _result(ws, outcome)
        if archive:
            _archive(migrated, log)
        _say(log, "the project is laid out in three documents, and prints what it printed")
        if log is not None:
            log(reminder)
        return outcome
    except BaseException as exc:
        reason = str(exc) or exc.__class__.__name__
        diffs = getattr(exc, "diffs", [])
        _say(log, f"FAILED -- {reason.splitlines()[0]}; undoing everything")
        try:
            problems = _undo(ws, book.record, log)
        except BaseException as undo_exc:   # broad: the undo's own failure is said, never hidden behind the first
            problems = [f"the rollback stopped: {undo_exc}"]
        _result(ws, {"ok": False, "project": here.file.name, "workspace": here.rel(ws), "reason": reason,
                     "diffs": diffs, "rolled_back": not problems, "rollback_problems": problems})
        if problems:
            raise MigrationError("rollback_incomplete", f"the migration failed ({reason.splitlines()[0]}) and undoing it did not go through: "
                                 + "; ".join(problems) + f" -- {BACKUP_FILE} in {here.rel(ws)} holds the project as it was",
                                 diffs=diffs, workspace=ws) from exc
        if isinstance(exc, KeyboardInterrupt):
            raise
        raise MigrationError("failed", f"the migration failed and was undone: {reason}", diffs=diffs, workspace=ws) from exc


def _produced(ws, root, p):
    """The files the migration added to the trees it moved -- the report's PDF where there was none, the seeded export files, a stamp -- as the old layout names them: what before.zip does not hold."""
    with zipfile.ZipFile(ws / BACKUP_FILE) as z:
        held = {name.rstrip("/") for name in z.namelist()}
    reverse = [(m.target, m.source) for m in p.moves]
    out = []
    for move in p.moves:
        target = move.target
        files = [target] if target.is_file() else sorted(f for f in target.rglob("*") if f.is_file())
        for file in files:
            old = _rel(root, _where(file, reverse))
            if old not in held:
                out.append(old)
    return out


def _verify(migrated, p, ws, reference, dates, skip_data, log):
    """The proof of a migration: the project read again, its engine, its export, its report and its two new documents -- the differences found, [] where there is none."""
    diffs = []
    if not migrated.has_modes or migrated.modes != project.MODES:
        return [f"{migrated.file.name} does not read as a project in three documents"]
    state, detail = project.engine_state(migrated)
    if state not in ("current", "stale"):
        return [f"the engine moved with the export and is not intact: {state} {detail}".strip()]
    if not skip_data:
        import export_all
        _say(log, "the export again, from the new layout")
        with project.using(migrated):
            export_all.run()
        allowed = {documents.JOURNAL_FILES[mode] for mode in ("cu", "bp")}
        diffs += compare_data(ws / REFERENCE_DIR / "data", migrated.data_dir, allowed)
    _say(log, "the report compiled from its new folder")
    stamps = _stamps()
    deps = migrated.stamps_dir / "rs.deps.json" if stamps else None
    if deps is not None:
        deps.parent.mkdir(parents=True, exist_ok=True)
    dates.add(date.today().strftime("%d.%m.%Y"))
    error = _compile(documents.compile_args(migrated, "rs", deps=deps), migrated)
    dates.add(date.today().strftime("%d.%m.%Y"))
    if error:
        return diffs + [f"the report does not compile from its new folder:\n{error}"]
    if stamps is not None:
        try:
            stamps.record(migrated, "rs", [], deps, migrated.document_pdf("rs"))
        except Exception as exc:  # broad: a convenience -- said in the migration's log, the comparison goes on
            _say(log, f"the report's stamp was not written ({exc})")
    diffs += compare_pdf(reference, read_pdf(migrated.document_pdf("rs")), sorted(dates))
    if diffs:
        return diffs
    for mode in ("cu", "bp"):
        _say(log, f"the {documents.MODE_NAMES['en'][mode].lower()} compiled")
        error = _compile(documents.compile_args(migrated, mode), migrated)
        if error:
            diffs.append(f"the {documents.MODE_NAMES['en'][mode].lower()} does not compile:\n{error}")
    return diffs


def _archive(migrated, log):
    """The migrated report archived, where calc/tools/archive_export.py knows the three documents (its `mode`); said and skipped where it does not yet, since it would then archive the whole project folder as one report's."""
    try:
        from tools import archive_export
    except ImportError:
        import archive_export
    if "mode" not in inspect.signature(archive_export.run).parameters:
        _say(log, "not archived: calc/tools/archive_export.py does not know the three documents yet")
        return
    try:
        with project.using(migrated):
            archive_export.run("woodcore-cli", "migration", mode="rs")
    except Exception as exc:   # broad: a convenience, never a failed migration -- said in its log
        _say(log, f"archive skipped ({exc})")


# --- undoing it -----------------------------------------------------------------------------------

def _root_of(workspace, record):
    """The project's folder, from the workspace and the archives folder the log names: the workspace lies at `<root>/<archives>/migration-…`, so a project moved to another path, or opened on the other machine, is still found."""
    root = Path(workspace).resolve().parent
    for _part in PurePosixPath(record["archives"]).parts:
        root = root.parent
    return root


def _set_aside(workspace, root, path, sub=""):
    """`path` moved into the workspace's rolled-back/ -- never deleted -- under its path from the project's folder."""
    target = Path(workspace) / ROLLED_BACK_DIR / sub / _rel(root, path)
    n = 2
    while target.exists():
        target = target.with_name(f"{target.name}-{n}")
        n += 1
    target.parent.mkdir(parents=True, exist_ok=True)
    _rename(path, target)
    return target


def _backup_entries(workspace, record):
    """(files, folders) before.zip holds, the files as {name: ZipInfo} -- or None where the migration failed before it was written, and nothing but the reference was done."""
    if not record.get("backup"):
        return None
    with zipfile.ZipFile(Path(workspace) / record["backup"]) as z:
        infos = z.infolist()
    files = {i.filename: i for i in infos if not i.is_dir()}
    folders = {i.filename.rstrip("/") for i in infos if i.is_dir()}
    return files, folders


def _restore(workspace, root, record, problems, keep=frozenset()):
    """Every file before.zip holds, put back where it differs from what the zip says it was, read-only where it was; every file of the old report's folder the zip does not hold -- what the migration added -- moved into rolled-back/added/, save the files of `keep` (what the engineer added since, which stays where it is); the folders the migration added and left empty, removed."""
    entries = _backup_entries(workspace, record)
    if entries is None:
        return
    files, folders = entries
    folders = folders | {record["old_report"]}
    with zipfile.ZipFile(Path(workspace) / record["backup"]) as z:
        for name, info in files.items():
            target = root / name
            data = z.read(info)
            try:
                if target.is_file() and target.read_bytes() == data:
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                if target.exists():
                    os.chmod(target, 0o666)
                _retrying(target.write_bytes, data)
                mode = (info.external_attr >> 16) & 0o777
                if mode and not mode & 0o200:
                    os.chmod(target, 0o444)
            except OSError as exc:
                problems.append(f"{name} could not be put back ({exc})")
    for name in folders:
        (root / name).mkdir(parents=True, exist_ok=True)
    old = root / record["old_report"]
    if not old.is_dir():
        return
    for path in sorted((x for x in old.rglob("*") if x.is_file()), key=lambda x: len(x.parts), reverse=True):
        rel = _rel(root, path)
        if rel not in files and rel not in keep:
            try:
                _set_aside(workspace, root, path, "added")
            except OSError as exc:
                problems.append(f"{rel} could not be set aside ({exc})")
    for path in sorted((x for x in old.rglob("*") if x.is_dir()), key=lambda x: len(x.parts), reverse=True):
        if _rel(root, path) not in folders:
            try:
                path.rmdir()
            except OSError:
                pass   # not empty: the engineer's own, kept


def _undo(workspace, record, log, keep=frozenset()):
    """What a migration did, undone as far as the log says it went: the new documents set aside, the renames undone in reverse, and the old tree put back from before.zip (`_restore`, `keep` passed on). Returns the problems met, [] where it all went back."""
    root = _root_of(workspace, record)
    problems = []
    for name in reversed(record.get("created", [])):
        path = root / name
        if path.exists():
            try:
                _set_aside(workspace, root, path)
                _say(log, f"set aside {name} in {ROLLED_BACK_DIR}/")
            except OSError as exc:
                problems.append(f"{name} could not be set aside ({exc})")
    for entry in reversed(record.get("moves", [])):
        if entry.get("state") not in ("moving", "done"):
            continue
        source, target = root / entry["from"], root / entry["to"]
        if _key(source) == _key(target) and source.name == target.name:
            continue
        if target.exists() and not source.exists():
            try:
                _rename(target, source)
                _say(log, f"moved back {entry['to']} -> {entry['from']}")
            except OSError as exc:
                problems.append(f"{entry['to']} could not be moved back to {entry['from']} ({exc})")
        elif not source.exists():
            problems.append(f"neither {entry['from']} nor {entry['to']} is there")
    vscode = record.get("vscode") or {}
    if vscode.get("created") and vscode.get("state") in ("writing", "done"):
        settings = root / ".vscode" / "settings.json"
        for path in (settings, settings.with_name(settings.name + ".part")):
            if path.exists():
                try:
                    _set_aside(workspace, root, path)
                except OSError as exc:
                    problems.append(f".vscode/{path.name} could not be set aside ({exc})")
        if vscode.get("folder_created"):
            try:
                settings.parent.rmdir()
            except OSError:
                pass   # not empty: the engineer's own, kept
    _restore(workspace, root, record, problems, keep)
    record["state"] = "rolled-back" if not problems else "rollback-incomplete"
    record["rolled_back"] = datetime.now().isoformat(timespec="seconds")
    _write_json(Path(workspace) / LOG_FILE, record)
    return problems


def _audit(workspace, root, record):
    """What stands in the way of undoing a migration that went through, and what the engineer added since -- `(refusals, keep)`.

    Refused: a folder the migration moved that is not where the log put it; a file it rewrote, the project file or Tinymist's settings no longer the bytes it wrote; and a file of the moved trees the engineer changed or deleted since -- putting the old one back would lose that work without a word. What the export and a compile write -- the export's own folder, the report's PDF -- is regenerated and never stands in the way. A file the engineer added since is kept, where the rollback puts its folder.
    """
    refusals, keep = [], set()
    done = [m for m in record.get("moves", []) if m.get("state") == "done"]
    for entry in done:
        source, target = root / entry["from"], root / entry["to"]
        if not target.exists():
            refusals.append(_note("moved_since", f"{entry['to']} is not where the migration put it", path=entry["to"]))
        elif source.exists() and _key(source) != _key(target):
            refusals.append(_note("moved_since", f"{entry['from']} is there again, where {entry['to']} was moved from", path=entry["from"]))
    for entry in record.get("rewritten", []):
        path = root / entry["file"]
        if entry.get("state") == "done" and (not path.is_file() or _sha_file(path) != entry.get("sha256_after")):
            refusals.append(_note("edited_since", f"{entry['file']} was edited since the migration", file=entry["file"]))
    for key, name in (("woodcore", record["project"]), ("vscode", ".vscode/settings.json")):
        entry = record.get(key)
        path = root / name
        if entry and entry.get("state") == "done" and (not path.is_file() or _sha_file(path) != entry.get("sha256_after")):
            refusals.append(_note("edited_since", f"{name} was edited since the migration", file=name))
    if refusals:
        return refusals, keep
    entries = _backup_entries(workspace, record)
    if entries is None:
        return refusals, keep
    files, _folders = entries
    reverse = [(root / m["to"], root / m["from"]) for m in done]
    rewritten = {e["from"] for e in record.get("rewritten", [])}
    produced = set(record.get("produced", []))
    outputs = set(record.get("outputs", []))

    def regenerated(old):
        return _is_under(root / old, root / record["generated"]) or old in outputs

    seen = set()
    with zipfile.ZipFile(Path(workspace) / record["backup"]) as z:
        for entry in done:
            target = root / entry["to"]
            current = [target] if target.is_file() else sorted(f for f in target.rglob("*") if f.is_file())
            for file in current:
                old = _rel(root, _where(file, reverse))
                seen.add(old)
                if old in files:
                    if old in rewritten or regenerated(old):
                        continue
                    if file.read_bytes() != z.read(files[old]):
                        refusals.append(_note("edited_since", f"{_rel(root, file)} was changed since the migration", file=_rel(root, file)))
                elif not (old in produced or regenerated(old)):
                    keep.add(old)
    prefix = record["old_report"].rstrip("/") + "/"
    for old in files:
        if old.startswith(prefix) and old not in seen and not regenerated(old):
            refusals.append(_note("deleted_since", f"{old} was deleted, or moved, since the migration", file=old))
    return refusals, keep


def rollback(workspace, *, log=print, lock_owner=None):
    """Undoes a migration that went through, from its folder in the project's archives (`_Archiv/migration-<timestamp>`), and gives back what it did.

    It refuses -- MigrationError `rollback_refused`, nothing done -- where the log is not a migration's, where it was undone already, where the project is open in another window (`lock_owner` names the one that asked for the rollback and holds the lock, as `run`'s does), and where the engineer has worked in the migrated project since (`_audit`): a folder not where the log put it, a file the migration rewrote no longer the bytes it wrote, a file of the moved trees changed or deleted. Otherwise the two new documents go into `rolled-back/` -- kept whole, whatever was written in them since -- the renames are undone, the old report's folder, the project file and Tinymist's settings are put back from before.zip, what the migration added is set aside beside the documents, and a file the engineer added since stays where its folder now is.
    """
    workspace = Path(workspace)
    try:
        record = json.loads((workspace / LOG_FILE).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise MigrationError("rollback_refused", f"{workspace}: no migration's log can be read there ({exc})") from None
    if record.get("format") != FORMAT:
        raise MigrationError("rollback_refused", f"{workspace / LOG_FILE} is not a migration's log")
    if record.get("state") in ("rolled-back", "rollback-incomplete"):
        raise MigrationError("rollback_refused", f"the migration of {workspace.name} was undone already", workspace=workspace)
    root = _root_of(workspace, record)
    me = project_lock.whoami()
    if lock_owner is not None:
        me["pid"] = int(lock_owner)
    holder = project_lock.holder(root / record["project"], me)
    if holder is not None:
        raise MigrationError("rollback_refused", f"{record['project']} is open in {holder.get('user', '?')}'s window on {holder.get('host', '?')} -- close it there first", workspace=workspace)
    refusals, keep = _audit(workspace, root, record)
    if refusals:
        raise MigrationError("rollback_refused", "the migration cannot be undone: " + "; ".join(refusals), refusals=refusals, workspace=workspace)
    problems = _undo(workspace, record, log, keep)
    outcome = {"ok": not problems, "rolled_back": True, "project": record["project"], "kept": sorted(keep), "problems": problems}
    try:
        previous = json.loads((workspace / RESULT_FILE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        previous = {}
    _result(workspace, {**previous, "rolled_back": True, "rollback": outcome})
    if problems:
        raise MigrationError("rollback_incomplete", "undoing the migration did not go through: " + "; ".join(problems)
                             + f" -- {BACKUP_FILE} in {workspace} holds the project as it was", workspace=workspace)
    _say(log, f"{record['project']} is laid out as it was before the migration")
    return outcome


# --- the command ----------------------------------------------------------------------------------

def command(argv=None):
    """`woodcore-cli migrate`, and `python calc/project_migrate.py`:

        migrate [--project F] [--language de|fr|en] [--names CU BP RS] [--dry-run] [--skip-data] [--update-engine] [--lock-owner PID]
        migrate --rollback <archives>/migration-<timestamp> [--lock-owner PID]

    `--project` names the project's `.woodcore`, else WOODCORE_PROJECT's, else the one beside the checkout (calc/project.py). `--names` the three folders in the order CU BP RS. `--dry-run` prints what would be done and what stands in the way, and writes nothing. `--skip-data` compares no export -- a project without Positionen.xlsx has none to run. `--update-engine` replaces an engine another version wrote or someone edited, before the reference is taken. `--lock-owner` names the process that holds the project's lock and asked for the migration (Woodcore's window runs this command as its child, `--lock-owner <its pid>`). `--rollback` undoes a migration that went through. Returns 0 where it went through (a dry run: where nothing stands in the way), 1 where it was refused or failed and was undone, 2 for arguments it cannot read.
    """
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    parser = argparse.ArgumentParser(prog="woodcore-cli migrate", description="A project laid out as one report, moved into three documents.")
    parser.add_argument("--project", help="the project's .woodcore file; else WOODCORE_PROJECT's, else the one beside the checkout")
    parser.add_argument("--language", choices=documents.LANGUAGES, help="the language of the folders and of the two new documents; config.typ's doc-lang if left out")
    parser.add_argument("--names", nargs=3, metavar=("CU", "BP", "RS"), help="the three folders, in the order CU BP RS; the language's own if left out")
    parser.add_argument("--dry-run", action="store_true", help="say what would be done, and write nothing")
    parser.add_argument("--skip-data", action="store_true", help="compare no export: only the engine is brought up to date before the reference")
    parser.add_argument("--update-engine", action="store_true", help="replace an engine another version wrote, or one edited by hand")
    parser.add_argument("--lock-owner", type=int, metavar="PID", help="the process that holds the project's lock and asked for the migration")
    parser.add_argument("--rollback", metavar="WORKSPACE", help="undo the migration whose folder this is: <archives>/migration-<timestamp>")
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return int(exc.code or 0)
    try:
        if args.rollback:
            rollback(args.rollback, lock_owner=args.lock_owner)
            return 0
        here = project.Project.load(args.project) if args.project else project.current()
        outcome = run(here, language=args.language, names=args.names, skip_data=args.skip_data,
                      update_engine=args.update_engine, dry_run=args.dry_run, lock_owner=args.lock_owner)
    except MigrationError as exc:
        print(f"migrate: {exc}", file=sys.stderr)
        for diff in exc.diffs:
            print(f"  {diff}", file=sys.stderr)
        return 1
    except (project.ProjectError, validation.ValidationError, engine.EngineError) as exc:
        print(f"migrate: {exc}", file=sys.stderr)
        return 1
    if args.dry_run:
        return 1 if outcome.refusals else 0
    return 0


if __name__ == "__main__":
    sys.exit(command())
