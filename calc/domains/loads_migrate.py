"""A project's sections, scripts and sources taken to the names the snow and wind sheets give since v0.120 (spec 2026-10-21-restes-issue-69, CON-002, D-06, ARCH-RISK-801 to 805; docs/domain/loads.md §3.3bis, §3.3quater).

An `SL-*` or `WL-*` sheet is computed by Woodcore since v0.120, and its instance takes the names of the code that computes it: a flat roof's one load is `q_k1` where the sheet called it `q_k11`, the global wind force on b·h `qk_max_cf1` where it was `qk_max_bh` (domains/loads_names.py). A project's own files still name the old ones, and the engineer wrote them: they are rewritten once, when the project is opened, as the report commands are (commands_migrate) -- **planned first, then written at once**, every file saved into the project's archives before it changes.

What a name becomes depends on its instance -- its roof, its table of Annexe C --, which the export the project last wrote says (`data/calculations.json`, read before the new one replaces it). Three kinds of file name a value of a load:

* **a Typst section** (`.typ`): `var-of`, `value-of` and `show-input` name it third, after the domain and the instance; `val` first, its domain in `domain:`; `show-calc` names it as a key of `shown:`. A call is rewritten where its domain and instance are written as strings -- `var-of("snow-load", "SL", "q_k11")`. A `#var("q_k11", …)` of the document's own is no load and is never touched;
* **a script** (`.py`): `value("snow-load", "SL", "q_k11")`, the three strings literal;
* **a source of Woodcore** (`.json`): every link `{domain, instance, var}` -- a member check's, a connector's, a connection's, a load's `links`, a static model's magnitude, a figure's text's `vars` --, the file rewritten only where Woodcore wrote it (`engine.source_bytes`: read and written again, the same bytes).

**What cannot be rewritten safely is refused, never guessed**: a name with no equivalent (`loads_names`: «Grosse Höhensprünge: Nein», the forces of Tableaux 50 to 56), a call whose instance or name is not a string where a renamed name stands in the file, a source that is not Woodcore's bytes. It is left as it is, and the export stops on it, naming the file, the line or the field, and the name (`refusal`).
"""

import json
import re
from pathlib import Path

import engine
from domains import commands_migrate, loads_names
from domains.commands_migrate import Change, _read
from typst_calls import closing as _closing, literal as _literal, split as _split   # the one reader of a call's arguments (calc/typst_calls.py)

DOMAINS = (loads_names.SNOW, loads_names.WIND)
LABEL = "loads-migration"

# The Typst readers of a load's value, and where each names it: (position of the name among the positional strings, or "shown" for show-calc's keys)
_READERS = {"var-of": 2, "value-of": 2, "show-input": 2, "val": 0, "show-calc": "shown", "var": 0}   # `#var(name, domain: …)` the reader of the export since the spec 2026-10-21-commandes-typst-refonte (REQ-009)
_CALL = re.compile(r"(?<![A-Za-z0-9_-])(" + "|".join(re.escape(n) for n in sorted(_READERS, key=len, reverse=True)) + r")\(")
_PY_CALL = re.compile(r"(?<![A-Za-z0-9_.])value\(")


def renames(here):
    """{(domain, instance): {old: new or None}} of the instances of the export the project last wrote whose names changed -- {} where it wrote none, or wrote them in the new names already."""
    previous = engine.previous_json(Path(here.data_dir) / "calculations.json")
    out = {}
    for domain in DOMAINS:
        for iid, instance in ((previous.get("domains") or {}).get(domain, {}).get("instances") or {}).items():
            table = loads_names.renamed(domain, instance or {})
            if any(new != old for old, new in table.items()):
                out[(domain, iid)] = {old: new for old, new in table.items() if new != old}
    return out


def _old_names(table, domain=None):
    """Every old name of `table` (of `domain` alone where it is given)."""
    return {old for (d, _i), names in table.items() if domain in (None, d) for old in names}


def _line(text, index):
    return text.count("\n", 0, index) + 1


def _rewrite_call(name, args, table):
    """One reader's arguments rewritten: (new arguments, notes, problems) -- a problem being (name, why)."""
    spans = _split(args)
    parts = [args[a:b] for a, b in spans]
    named = {}
    positional = []
    for k, part in enumerate(parts):
        key = re.match(r"\s*([A-Za-z_][A-Za-z0-9_-]*)\s*:", part)
        if key and not part.strip().startswith('"'):
            named[key.group(1)] = k
        else:
            positional.append(k)
    # the domain and the instance: the first two positional strings, or val's and var's `domain: ("…", "…")`
    if name in ("val", "var"):
        held = parts[named["domain"]].split(":", 1)[1].strip() if "domain" in named else ""
        inner = held[1:-1] if held.startswith("(") and held.endswith(")") else ""
        pair = [_literal(p) for p in inner.split(",")] if inner.count(",") == 1 else [None, None]
        domain, instance = (pair + [None, None])[:2]
        if "domain" not in named:
            return args, [], []
    else:
        if len(positional) < 2:
            return args, [], []
        domain, instance = _literal(parts[positional[0]]), _literal(parts[positional[1]])
    if domain not in DOMAINS:
        return args, [], []
    olds = _old_names(table, domain)
    names = table.get((domain, instance))
    notes, problems = [], []

    def mentions(text):
        return [old for old in olds if re.search(r'(?<![A-Za-z0-9_])"?%s"?\s*[:,)]|"%s"' % (re.escape(old), re.escape(old)), text)]
    if instance is None:
        # an instance that is not written as a string: which roof or table it is cannot be known
        for old in mentions(args):
            problems.append((old, "the instance of %s is not written as a string" % domain))
        return args, notes, problems + [(None, domain)]
    if names is None:
        return args, notes, problems
    position = _READERS[name]
    if position == "shown":
        if "shown" not in named:
            return args, notes, problems
        k = named["shown"]
        part = parts[k]

        def key(found):
            old = found.group(1)
            if old not in names:
                return found.group(0)
            if names[old] is None:
                problems.append((old, "no equivalent in %s %s" % (domain, instance)))
                return found.group(0)
            notes.append("%s/%s: %s -> %s" % (domain, instance, old, names[old]))
            return names[old] + found.group(2)
        head, rest = part.split(":", 1)
        parts[k] = head + ":" + re.sub(r'(?<![A-Za-z0-9_"])([A-Za-z_][A-Za-z0-9_]*)(\s*:)', key, rest)
    else:
        if len(positional) <= position:
            return args, notes, problems
        k = positional[position]
        old = _literal(parts[k])
        if old is None:
            for found in mentions(args):
                problems.append((found, "the name read from %s %s is not written as a string" % (domain, instance)))
            problems.append((None, domain))
        elif old in names:
            if names[old] is None:
                problems.append((old, "no equivalent in %s %s" % (domain, instance)))
            else:
                parts[k] = parts[k].replace('"%s"' % old, '"%s"' % names[old], 1)
                notes.append("%s/%s: %s -> %s" % (domain, instance, old, names[old]))
    return ",".join(parts), notes, problems


def rewrite_typst(text, table):
    """`text` with every reader of a renamed load value rewritten, and (notes, unresolved) -- unresolved [(line, name, why)]. Every byte that is no such name is kept, line endings included."""
    notes, unresolved, out, at, dynamic = [], [], [], 0, set()
    for found in _CALL.finditer(text):
        open_at = found.end() - 1
        if found.start() < at:
            continue
        close = _closing(text, open_at)
        if close is None:
            continue
        args, said, problems = _rewrite_call(found.group(1), text[open_at + 1:close], table)
        notes += said
        unresolved += [(_line(text, found.start()), old, why) for old, why in problems if old is not None]
        # a value read by a name or an instance the call computes (`for n in (…) [#var-of("snow-load", "SL", n)]`): which names it reads cannot be known
        dynamic.update(why for old, why in problems if old is None)
        out.append(text[at:open_at + 1] + args)
        at = close
    out.append(text[at:])
    after = "".join(out)
    # where a load is read dynamically, an old name the file still writes as a string may be one it reads: refused, never guessed
    for domain in sorted(dynamic):
        for old in sorted(_old_names(table, domain)):
            for found in re.finditer(r'"%s"' % re.escape(old), after):
                unresolved.append((_line(after, found.start()), old, "%s is read here by a name or an instance the section computes" % domain))
    return after, notes, list(dict((u[:2], u) for u in unresolved).values())   # one line and one name, said once


def rewrite_python(text, table):
    """A script's `value("domain", "instance", "name")` rewritten, and (notes, unresolved): a call whose three arguments are not strings, where a renamed name stands in it, is unresolved."""
    notes, unresolved, out, at = [], [], [], 0
    for found in _PY_CALL.finditer(text):
        open_at = found.end() - 1
        close = _closing(text, open_at)
        if close is None or found.start() < at:
            continue
        args = text[open_at + 1:close]
        spans = _split(args)
        parts = [args[a:b] for a, b in spans]
        if len(parts) == 3:
            domain, instance, name = (_literal(p) for p in parts)
            if domain in DOMAINS:
                names = table.get((domain, instance), {}) if instance is not None else {}
                olds = _old_names(table, domain)
                if instance is None or name is None:
                    for old in olds:
                        if '"%s"' % old in args or "'%s'" % old in args:
                            unresolved.append((_line(text, found.start()), old, "the call's arguments are not written as strings"))
                elif name in names:
                    if names[name] is None:
                        unresolved.append((_line(text, found.start()), name, "no equivalent in %s %s" % (domain, instance)))
                    else:
                        parts[2] = parts[2].replace('"%s"' % name, '"%s"' % names[name], 1)
                        notes.append("%s/%s: %s -> %s" % (domain, instance, name, names[name]))
        out.append(text[at:open_at + 1] + ",".join(parts))
        at = close
    out.append(text[at:])
    return "".join(out), notes, unresolved


def rewrite_json(data, table, path=""):
    """Every link `{domain, instance, var}` of a source's JSON taken to the new name, in place; returns (notes, unresolved) -- unresolved [(field, name, why)]."""
    notes, unresolved = [], []
    if isinstance(data, dict):
        domain, instance, var = data.get("domain"), data.get("instance"), data.get("var")
        if domain in DOMAINS and isinstance(instance, str) and isinstance(var, str):
            names = table.get((domain, instance), {})
            if var in names:
                if names[var] is None:
                    unresolved.append((path or "/", var, "no equivalent in %s %s" % (domain, instance)))
                else:
                    data["var"] = names[var]
                    notes.append("%s: %s/%s: %s -> %s" % (path or "/", domain, instance, var, names[var]))
        for key, value in data.items():
            n, u = rewrite_json(value, table, "%s/%s" % (path, key))
            notes += n
            unresolved += u
    elif isinstance(data, list):
        for i, value in enumerate(data):
            n, u = rewrite_json(value, table, "%s/%d" % (path, i))
            notes += n
            unresolved += u
    return notes, unresolved


def _json_files(here):
    """The project's own JSON sources: every `.json` under its folder but the export (`data/`), the engine's copy and the archives."""
    generated = Path(here.generated_dir)
    # the export, the archives, and the engine's copy beside the export (its lib/ and calc/, project.ENGINE_FILES)
    left_out = [Path(folder).resolve() for folder in (here.data_dir, here.archives_dir, generated / "lib", generated / "calc")]
    for path in sorted(Path(here.root).rglob("*.json")):
        resolved = path.resolve()
        if any(resolved.is_relative_to(folder) for folder in left_out) or "archives" in path.relative_to(here.root).parts:
            continue
        yield path


def _script_files(here):
    from domains import script
    return script.source_paths(here)


def plan(here, table=None):
    """(changes, unresolved): every file the migration would change, with what it would write and why, and every name it cannot take to the new one, (file, where, name, why) -- reading everything, writing nothing."""
    table = renames(here) if table is None else table
    changes, unresolved = [], []
    if not table:
        return changes, unresolved
    for path in commands_migrate._typst_files(here):
        try:
            before = _read(path)
        except (OSError, UnicodeDecodeError):
            continue
        after, notes, left = rewrite_typst(before, table)
        unresolved += [(path, "line %d" % line, name, why) for line, name, why in left]
        if after != before:
            changes.append(Change(path, before, after, notes))
    for path in _script_files(here):
        try:
            before = _read(path)
        except (OSError, UnicodeDecodeError):
            continue
        after, notes, left = rewrite_python(before, table)
        unresolved += [(path, "line %d" % line, name, why) for line, name, why in left]
        if after != before:
            changes.append(Change(path, before, after, notes))
    olds = _old_names(table)
    for path in _json_files(here):
        try:
            before = _read(path)
            data = json.loads(before)
        except (OSError, UnicodeDecodeError, ValueError):
            continue
        if not any('"%s"' % old in before for old in olds):
            continue
        notes, left = rewrite_json(data, table)
        unresolved += [(path, field, name, why) for field, name, why in left]
        if not notes:
            continue
        if engine.source_bytes(json.loads(before)).decode("utf-8") != before:
            # not the bytes Woodcore writes: rewriting it would change more than the names
            unresolved += [(path, "/", note.split(" -> ")[0].rsplit(": ", 1)[-1], "the file is not as Woodcore writes it -- save it once in Woodcore") for note in notes]
            continue
        changes.append(Change(path, before, engine.source_bytes(data).decode("utf-8"), notes))
    return changes, unresolved


def commit(here, changes):
    """`changes` written, every file saved first into the project's archives (commands_migrate.commit, the one way a migration writes)."""
    return commands_migrate.commit(here, changes, LABEL)


def migrate(here):
    """The migration done; returns the changes made -- none on a second run, none where the last export already named the values the new way."""
    changes, _unresolved = plan(here)
    return commit(here, changes)


def refusal(here):
    """None where nothing of the project names a load value by its old name, else the sentence the export stops on: the file, the line or the field, the name and what to do (CLAUDE.md: a defect stops the export, naming the file)."""
    changes, unresolved = plan(here)
    if unresolved:
        path, where, name, why = unresolved[0]
        return f"{here.rel(path)} ({where}): {name!r} is a value of a load renamed in v0.120 that cannot be rewritten -- {why}; name the value the instance now gives (docs/domain/loads.md §3.3bis)"
    if changes:
        first = changes[0]
        return f"{here.rel(first.path)}: names {first.notes[0].split(' -> ')[0].rsplit(': ', 1)[-1]}, a value of a load renamed in v0.120 -- open the project once in Woodcore, which rewrites its files (each saved into the archives first)"
    return None
