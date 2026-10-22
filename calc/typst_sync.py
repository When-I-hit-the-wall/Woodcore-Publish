"""The values Woodcore keeps in step inside a document: `#sync(id)[content]` (spec docs/requirements/completed/2026-10-21-commandes-typst-refonte.md, REQ-011, ARCH-009, ARCH-010).

The engineer, 20.10.2026: tables written in raw Typst, «des balises de commandes qui n'affichent rien, mais permettent de délimiter du contenu … De cette manière, les valeurs entre les balises peuvent être synchronisées. Si le user supprime une balise, alors cette valeur cesse d'être synchronisée», settled as one tag that surrounds what it keeps, `#sync` (T38). In Typst `#sync(id)[content]` prints its content and nothing else (lib/calc-engine-core.typ); here it is found, read and rewritten.

**Found by the lexer, never by a regex** (ARCH-RISK-108, ARCH-009): a `#sync` is a `#name` that `typst_paths`' lexer meets where Typst would run it -- in markup, a cell `[…]`, a list, a sentence --, its arguments closed by `typst_calls.closing` (code, where a `"` opens a string), its content block by the lexer in markup mode, where a `"` is a smart quote and a `]` inside a nested `[…]`, a raw block or a comment is no end. A `#sync` in a comment, a string or a raw block is no sync. Every byte outside a content rewritten is kept, line endings included.

**What a content is** (Q-007): a literal -- `#sync("live-load/A1/category")[A1]` -- or a reading of the export Typst makes at every compile -- `#sync("live-load/A1/q_k")[#var("q_k", domain: ("live-load", "A1"), display: "value-unit")]`. Woodcore keeps both in step, the call or the literal; the value a reading prints never ages, and a literal is **compared** with the export at each export: a gap is a warning naming the file, the line and the id, never an overwrite -- the refresh is an action of the engineer's (ARCH-010).

**The id** is `domain/instance/variable` -- `live-load/A1/q_k`, the address `dependency_graph` names a value by --, a `/` or a `\\` inside one of its parts written `\\/` and `\\\\`. One id once per file. Standard library and calc/units.py only; Qt-free.
"""

import json
import re
from dataclasses import dataclass

import typst_calls
import typst_paths
import units

NAME = "sync"


@dataclass(frozen=True)
class Sync:
    """One `#sync(id)[content]` of a file: its id, where the call starts (the `#`), where its content lies -- `content_start` after the `[`, `content_end` at the `]` --, the content as written, and its line (from 1)."""
    id: str
    start: int
    content_start: int
    content_end: int
    content: str
    line: int


class SyncError(ValueError):
    """A `#sync` that cannot be read or written as asked -- an id given twice, a call without its content -- said with its line."""


def _hashes(text):
    """[(offset of `#`, name)] of every `#name` the lexer meets where Typst would run it."""
    lexer = typst_paths._Lexer(text)
    found = []
    original = lexer._hash

    def hashed(j):
        ident = typst_paths._IDENT.match(text, j + 1)
        if ident is not None:
            found.append((j, ident.group()))
        original(j)
    lexer._hash = hashed
    while lexer.i < lexer.n:
        at = lexer.i
        frame = lexer.stack[-1]
        getattr(lexer, "_" + frame[0])(frame)
        if lexer.i == at and lexer.stack[-1] is frame:
            lexer.i += 1   # a lexer that does not move would loop: never seen, guarded
    return found


def _content_end(text, open_at):
    """The offset of the `]` that closes the content block opened by the `[` at `open_at`, read in markup mode; None where the file ends first."""
    lexer = typst_paths._Lexer(text)
    lexer.i = open_at + 1
    lexer.stack = [["markup", None, 0], ["markup", "]", 0]]
    while lexer.i < lexer.n and len(lexer.stack) > 1:
        at = lexer.i
        frame = lexer.stack[-1]
        getattr(lexer, "_" + frame[0])(frame)
        if lexer.i == at and lexer.stack[-1] is frame:
            lexer.i += 1
    return lexer.i - 1 if len(lexer.stack) == 1 else None


def _unescaped(literal):
    r"""A Typst string's value from its text as written: `\\` a backslash, `\\"` a quote -- so that an id's `\/` (`make_id`), written `\\/` in a valid Typst string, reaches `split_id` as itself."""
    if literal is None:
        return None
    return re.sub(r"\\(.)", lambda m: {"n": "\n", "t": "\t"}.get(m.group(1), m.group(1)), literal)


def syncs(text):
    """Every `#sync(id)[content]` of `text`, in order. Raises SyncError for a `#sync` without its id or its content, or an id given twice."""
    out, seen = [], {}
    for j, name in _hashes(text):
        if name != NAME:
            continue
        line = text.count("\n", 0, j) + 1
        paren = j + 1 + len(NAME)
        if paren >= len(text) or text[paren] != "(":
            continue   # `#sync` named and not called: nothing to keep
        close = typst_calls.closing(text, paren)
        if close is None:
            raise SyncError(f"line {line}: #sync( is never closed")
        positional, _named = typst_calls.arguments(text[paren + 1:close])
        ident = _unescaped(typst_calls.literal(positional[0])) if positional else None
        if ident is None:
            raise SyncError(f"line {line}: #sync takes its id first, a string -- #sync(\"live-load/A1/q_k\")[…]")
        if close + 1 >= len(text) or text[close + 1] != "[":
            raise SyncError(f"line {line}: #sync({ident!r}) has no content -- write what it keeps between brackets, #sync(\"{ident}\")[…]")
        end = _content_end(text, close + 1)
        if end is None:
            raise SyncError(f"line {line}: the content of #sync({ident!r}) is never closed")
        if ident in seen:
            raise SyncError(f"line {line}: the id {ident!r} is given to two #sync of this file (first at line {seen[ident]})")
        seen[ident] = line
        out.append(Sync(ident, j, close + 2, end, text[close + 2:end], line))
    return out


def rewrite(text, contents):
    """`text` with the content of each `#sync` whose id `contents` names replaced by its value, every other byte kept. An id `contents` names and the file does not hold is refused, nothing changed."""
    found = {s.id: s for s in syncs(text)}
    missing = sorted(set(contents) - set(found))
    if missing:
        raise SyncError(f"no #sync {', '.join(repr(m) for m in missing)} in this file")
    out, at = [], 0
    for s in sorted(found.values(), key=lambda s: s.content_start):
        if s.id not in contents:
            continue
        out.append(text[at:s.content_start])
        out.append(contents[s.id])
        at = s.content_end
    out.append(text[at:])
    return "".join(out)


def blanked(text):
    """`text` with every `#sync` content emptied -- what the sharing of a block between documents compares (calc/sync.py, ARCH-RISK-303): a value Woodcore keeps in step is no edit of the engineer's, and a refreshed number must not make two copies of a shared block look different. A file a `#sync` of which cannot be read is returned as it is."""
    try:
        found = syncs(text)
    except SyncError:
        return text
    out, at = [], 0
    for s in found:
        out.append(text[at:s.content_start])
        at = s.content_end
    out.append(text[at:])
    return "".join(out)


# --- the ids, and what the export holds for one ---------------------------------------------------

def split_id(ident):
    """`domain/instance/variable` read into its three parts, `\\/` and `\\\\` unescaped; None for an id of another shape."""
    parts, current, i = [], "", 0
    while i < len(ident):
        c = ident[i]
        if c == "\\" and i + 1 < len(ident):
            current += ident[i + 1]
            i += 2
            continue
        if c == "/":
            parts.append(current)
            current = ""
        else:
            current += c
        i += 1
    parts.append(current)
    return tuple(parts) if len(parts) == 3 and all(parts) else None


def make_id(domain, instance, variable):
    """The id of one value of the export, its parts escaped."""
    esc = lambda part: part.replace("\\", "\\\\").replace("/", "\\/")
    return "/".join(esc(p) for p in (domain, instance, variable))


def held(calculations, ident, lists=None):
    """The var the export holds under `ident` -- {value, unit, …} -- from `data/calculations.json`'s domains, or from the lists Woodcore writes once (`lists`, domains/list_files.py `sync_records`: the journals, the positions, the quantities); None where neither holds it."""
    parts = split_id(ident)
    if parts is None:
        return None
    domain, instance, variable = parts
    if lists and domain in lists:
        return lists[domain].get(instance, {}).get(variable)
    record = (calculations.get("domains", {}).get(domain, {}).get("instances", {}).get(instance, {}))
    return record.get("vars", {}).get(variable)


def written(value, unit=""):
    """A value as Woodcore writes it into a `#sync` it keeps: the number as the report prints one -- `units.fmt_decimals`, the twin of `fmt-number` held equal by tests/test_typst_sync.py, a minus sign typographic -- and its unit after a space; a word as it is."""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        text = units.signed(units.fmt_decimals(value))
    else:
        text = str(value)
    return text + (" " + unit if unit else "")


_NUMBER = re.compile(r"[-−]?\d+(?:[.,]\d+)?")


def stale(content, var):
    """Whether a literal content says another value than the export's var: the first number it writes against the var's, at the precision written (a value written to fewer decimals agrees where the export rounds to it -- literal-stale's rule in lib/formula.typ); a word against the word. A content that reads the export itself (`#var(`, `#get(`) never ages, and is never stale."""
    if "#var(" in content or "#get(" in content or "get(" in content:
        return False
    value = var.get("value")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        found = _NUMBER.search(content)
        if found is None:
            return True
        text = found.group().replace("−", "-").replace(",", ".")
        decimals = len(text.split(".")[1]) if "." in text else 0
        return abs(float(text) - value) > max(0.5 * 10 ** -decimals, 1e-9 * max(1.0, abs(value)))
    # a word of the engine the list prints in the document's language («Träger», «Poutre», «Beam») is the export's word
    from i18n import strings
    shown = content.strip().replace("\\", "")
    return shown not in {str(value)} | {strings.translate(str(value), lang) for lang in ("de", "fr", "en")}


def check(here, calculations=None):
    """[(file, line, id, content, the export's value written)] of every literal `#sync` of the project's own sections that says another value than the export -- what the export warns of (ARCH-010), nothing written. `calculations` is the export being made (`data/calculations.json`'s shape), else the last one written. A `#sync` whose id names nothing the export holds is left to the reader: an id of the engineer's own."""
    from domains import commands_migrate
    if calculations is None:
        try:
            calculations = json.loads((here.data_dir / "calculations.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return []
    from domains import list_files
    lists = list_files.sync_records(here)
    found = []
    for file in commands_migrate._typst_files(here):
        try:
            text = commands_migrate._read(file)
            entries = syncs(text)
        except (OSError, UnicodeDecodeError, SyncError):
            continue
        for s in entries:
            var = held(calculations, s.id, lists)
            if var is not None and stale(s.content, var):
                found.append((file, s.line, s.id, s.content, written(var.get("value"), var.get("unit") or "")))
    return found
