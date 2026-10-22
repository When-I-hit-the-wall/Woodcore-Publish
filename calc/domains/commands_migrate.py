"""A project's sections taken to the report commands of the day (spec docs/requirements/active/2026-10-19-base-saine-nettoyage.md, REQ-002, D-13, ARCH-RISK-406).

Thirteen commands that each listed the ids of one kind became one, `ids(kind)`; eight readers of one field of a variable became `get(v, field)`; the two load summaries became `show-load-summary(unit:)`; two commands were taken away. A project's own sections still call the old names, and the engineer wrote them: they are rewritten once, when the project is opened, as `unfold_migrate` rewrites the unfolded checks -- **planned first, then written at once**, every file saved into the project's archives before it changes. What a call becomes is read from one table, `calc/renamed-commands.json`.

A call is found by its name standing alone (not part of a longer name) followed by its arguments, which are kept byte for byte: `position-ids()` → `ids("position")`, `get-value(q)` → `get(q, "value")`, `show-line-load-summary(title: "Linien")` → `show-load-summary(title: "Linien", unit: "kN/m")`; a name passed as a function without its parentheses (`.map(get-value)`) becomes a function, `(v => get(v, "value"))`. A command that was taken away has nothing it can be rewritten into: it is left as it is and said (`unresolved`), and the export refuses the section, naming what to write instead.

**Taken away, never rewritten** (spec 2026-10-21-commandes-typst-refonte, REQ-020, ARCH-006, CON-004). The commands and the arguments that spec retires are `removed` entries -- the engineer carries a project over to them by hand, «la migration n'est pas nécessaire, il suffit d'avoir un message d'alerte» --, and an argument taken away from a command that stays is the table's `arguments` section, `{command: {argument: what to write instead}}`: a call that still writes it is said like a removed command, with its file and its line. `removals(here)` lists them for the window, which tells them when the project is opened; the export refuses the first.
"""

import json
import re
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path

from typst_calls import closing as _closing   # the one reader of a call's brackets (calc/typst_calls.py)

TABLE = Path(__file__).resolve().parents[1] / "renamed-commands.json"
_OPEN = {"(": ")", "[": "]", "{": "}"}


@dataclass
class Change:
    """One file the migration rewrites: its path, its text before and after, and what was done to it, said in English for the log (`notes`)."""
    path: Path
    before: str
    after: str
    notes: list = field(default_factory=list)


def table():
    """{old name: rule} of calc/renamed-commands.json."""
    return json.loads(TABLE.read_text(encoding="utf-8"))["commands"]


def removed_arguments():
    """{command: {argument: what to write instead}} of calc/renamed-commands.json: the arguments a command that stays no longer takes (spec 2026-10-21-commandes-typst-refonte, REQ-020)."""
    return json.loads(TABLE.read_text(encoding="utf-8")).get("arguments", {})


def argument_calls(text, arguments=None):
    """Every call in `text` that writes an argument taken away, as (command, argument, what to write instead, offset) -- comments left out (`typst_calls.calls`)."""
    import typst_calls
    arguments = removed_arguments() if arguments is None else arguments
    found = []
    for name, start, args, _line in typst_calls.calls(text, list(arguments)):
        _positional, named = typst_calls.arguments(args)
        found += [(name, argument, hint, start) for argument, hint in arguments[name].items() if argument in named]
    return found


def _arguments(rule, inner):
    parts = list(rule.get("prepend", ()))
    if inner.strip():
        parts.append(inner.strip() if "\n" not in inner else inner)
    parts += rule.get("append", ())
    return ", ".join(parts)


_STRING = re.compile(r'"(?:[^"\\\n]|\\.)*"')
_IMPORT = re.compile(r'^([ \t]*#?import[ \t]+"[^"\n]*"[ \t]*:[ \t]*)([^\n]*)$', re.M)


def _imports(text, rules, notes, unresolved):
    """The names of an `#import "…": a, b, c` line: an old name becomes its command's new one, said once (`ids`, not thirteen times), a name taken away is dropped and said."""
    def one(found):
        names, out = [n.strip() for n in found.group(2).split(",")], []
        if not any(name in rules for name in names):
            return found.group(0)   # nothing to rename: the line as the engineer wrote it, spacing and all
        for name in names:
            rule = rules.get(name)
            if rule is None:
                new = name
            elif "removed" in rule:
                unresolved.append((name, rule["removed"]))
                notes.append(f"{name} dropped from an import")
                continue
            else:
                new = rule["to"]
                notes.append(f"{name} -> {new} (import)")
            if new and new not in out:
                out.append(new)
        return found.group(1) + ", ".join(out)
    return _IMPORT.sub(one, text)


def _imports_offsets(text, rules):
    """Where each name taken away stands in an import line -- the offsets `_imports` reports in its order."""
    out = []
    for found in _IMPORT.finditer(text):
        for name in [n.strip() for n in found.group(2).split(",")]:
            if "removed" in rules.get(name, {}):
                out.append(found.start())
    return out


def rewrite(text, rules=None, offsets=None):
    """`text` with every call of an old command rewritten, and (notes, unresolved): what was done, and the calls of a command taken away, each (name, what to write instead). Every byte that is no such call is kept, line endings included. `offsets`, a list, is given where in `text` each unresolved call stands, in their order -- the line the window and the export name."""
    rules = table() if rules is None else rules
    offsets = [] if offsets is None else offsets
    notes, unresolved = [], []
    offsets += _imports_offsets(text, rules)
    text = _imports(text, rules, notes, unresolved)
    spans = [(m.start(), m.end()) for m in _IMPORT.finditer(text)]
    # a call quoted in a Typst string -- a message that shows the call to write -- is rewritten too, its quotes escaped
    strings = [(m.start(), m.end()) for m in _STRING.finditer(text)]
    # a name said in a comment -- `/// … show-line-load-summary …` -- is prose: it takes the new name, never a function's form
    comments = [(m.start(), m.end()) for m in re.finditer(r"//[^\n]*", text) if not any(a < m.start() < b for a, b in strings)]
    names = sorted(rules, key=len, reverse=True)
    # a name standing alone: not the end of a longer name (`my-get-value`), but after a sign it may be (`-get-symbol(v)`, a unary minus)
    pattern = re.compile(r"(?<![A-Za-z0-9_])(?<![A-Za-z0-9_]-)(" + "|".join(re.escape(n) for n in names) + r")(?![A-Za-z0-9_-])")
    out, at = [], 0
    for found in pattern.finditer(text):
        if found.start() < at or any(a <= found.start() < b for a, b in spans):
            continue
        name = found.group(1)
        rule = rules[name]
        if "removed" in rule:
            # a command taken away is said where it is **called** -- its name followed by `(` or by a content block --, never a word of the prose, a comment or a message: «member», «schema» are words too (spec 2026-10-21-commandes-typst-refonte, REQ-020)
            after = text[found.end():found.end() + 1]
            if after not in ("(", "[") or any(a < found.start() < b for a, b in strings) or any(a < found.start() < b for a, b in comments):
                continue
            unresolved.append((name, rule["removed"]))
            offsets.append(found.start())   # the import lines rewritten above keep their line, so the line counted here is the file's
            continue
        end = found.end()
        quoted = any(a < found.start() < b for a, b in strings)
        if end < len(text) and text[end] == "(":
            close = _closing(text, end)
            if close is None:
                continue
            new = f"{rule['to']}({_arguments(rule, text[end + 1:close])})"
            out.append(text[at:found.start()] + (new.replace('"', '\\"') if quoted else new))
            at = close + 1
        elif quoted or any(a < found.start() < b for a, b in comments):
            out.append(text[at:found.start()] + rule["to"])   # a name said in a message or a comment: the new one
            at = end
        elif rule.get("append"):
            new = f"(v => {rule['to']}({_arguments(rule, 'v')}))"   # a reader of one field, passed as a function: `.map(get-value)`
            out.append(text[at:found.start()] + new)
            at = end
        elif rule.get("prepend"):
            new = f"(() => {rule['to']}({_arguments(rule, '')}))"   # a list of ids, passed as a function
            out.append(text[at:found.start()] + new)
            at = end
        else:
            out.append(text[at:found.start()] + rule["to"])
            at = end
        notes.append(f"{name} -> {rule['to']}")
    out.append(text[at:])
    return "".join(out), notes, unresolved


def _typst_files(here):
    """The project's own `.typ` files: every one under its Typst root but the engine's copy (`_woodcore/`) and anything under an `archives` folder."""
    root = here.typst_root
    left_out = [here.generated_dir.resolve(), Path(here.archives_dir).resolve()]
    for path in sorted(root.rglob("*.typ")):
        resolved = path.resolve()
        if any(resolved.is_relative_to(folder) for folder in left_out) or "archives" in path.relative_to(root).parts:
            continue
        yield path


def _read(path):
    with open(path, encoding="utf-8", newline="") as file:
        return file.read()


def plan(here):
    """(changes, unresolved): every file the migration would change, with what it would write and why, and every call of a command or an argument taken away as (file, what is written -- `#val`, `#var(own:)` --, what to write instead, its line) -- reading everything, writing nothing."""
    changes, unresolved = [], []
    rules, arguments = table(), removed_arguments()
    for path in _typst_files(here):
        try:
            before = _read(path)
        except (OSError, UnicodeDecodeError):
            continue
        offsets = []
        after, notes, left = rewrite(before, rules, offsets)
        unresolved += [(path, "#" + name, hint, _line(before, at)) for (name, hint), at in zip(left, offsets)]
        unresolved += [(path, f"#{name}({argument}:)", hint, _line(before, at)) for name, argument, hint, at in argument_calls(before, arguments)]
        if after != before:
            changes.append(Change(path, before, after, notes))
    return changes, unresolved


def _line(text, offset):
    return text.count("\n", 0, offset) + 1


def commit(here, changes, label):
    """The changes written: every file saved first into `<archives>/<label>-<stamp>/` (its path under the Typst root kept), then all written together or none (`sharing._commit`), and a `notes.txt` beside the copies. The one way a migration of the project's Typst writes -- `unfold_migrate` writes through it too."""
    import sharing
    if not changes:
        return []
    backup = Path(here.archives_dir) / f"{label}-{time.strftime('%y%m%d-%H%M%S')}"
    n = 1
    while backup.exists():
        n += 1
        backup = backup.with_name(backup.name.split("~")[0] + f"~{n}")
    for change in changes:
        target = backup / _relative(here, change.path)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(change.path, target)
    sharing._commit([(c.path, c.after.encode("utf-8"), c.before.encode("utf-8")) for c in changes])
    (backup / "notes.txt").write_text("\n".join(f"{_relative(here, c.path).as_posix()}: {note}" for c in changes for note in c.notes) + "\n", encoding="utf-8", newline="\n")
    return changes


def _relative(here, path):
    """Where a file is kept in an archive: its path under the Typst root, else under the project's folder (a source of Woodcore, a script: spec 2026-10-21-restes-issue-69, ARCH-RISK-805), else its name."""
    path = Path(path)
    for root in (here.typst_root, here.root):
        try:
            return path.resolve().relative_to(Path(root).resolve())
        except ValueError:
            continue
    return Path(path.name)


def migrate(here):
    """The migration done; returns the changes made -- none on a second run."""
    changes, _unresolved = plan(here)
    return commit(here, changes, "commands-migration")


def refusal(here):
    """None where no section calls an old command, else the sentence the export stops on: the first file, the command and its replacement (CLAUDE.md: a defect stops the export, naming the file)."""
    changes, unresolved = plan(here)
    if unresolved:
        path, name, hint, line = unresolved[0]
        return f"{here.rel(path)}:{line}: {name} is no longer {'an argument of its command' if name.endswith(':)') else 'a command'} -- {hint}"
    if changes:
        first = changes[0]
        return f"{here.rel(first.path)}: calls {first.notes[0].split(' -> ')[0]}, a command renamed in v0.120 -- open the project once in Woodcore, which rewrites its sections (each file saved into the archives first)"
    return None


def removals(here):
    """[(file, line, what is written, what to write instead)] of every call of a command or an argument taken away in the project's own sections -- what the window tells when the project is opened (spec 2026-10-21-commandes-typst-refonte, REQ-020), nothing written."""
    _changes, unresolved = plan(here)
    return [(path, line, name, hint) for path, name, hint, line in unresolved]


def unscoped_units(text):
    """The offsets in `text` of every `#unit(...)` that writes no `scope:` -- comments left out (`typst_calls.calls`).

    Until the spec 2026-10-21-commandes-typst-refonte (REQ-005, CON-007) `#unit` reached the rest of the document; it now reaches the next answer of its dimension unless `scope:` says otherwise, and a call written before cannot be told from one written since: each is said, never rewritten."""
    import typst_calls
    return [start for _name, start, args, _line in typst_calls.calls(text, ["unit"]) if "scope" not in typst_calls.arguments(args)[1]]


def unit_scope_notes(here):
    """[(file, line)] of every `#unit` without `scope:` in the project's own sections -- what the window tells when the project is opened (CON-007)."""
    found = []
    for path in _typst_files(here):
        try:
            text = _read(path)
        except (OSError, UnicodeDecodeError):
            continue
        found += [(path, _line(text, at)) for at in unscoped_units(text)]
    return found
