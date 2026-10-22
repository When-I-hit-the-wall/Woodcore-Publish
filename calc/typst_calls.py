"""The calls a Typst file makes, read without compiling it: where a call opens and closes, its arguments split at their top-level commas, a string argument read back, and the comments left out (spec docs/requirements/completed/2026-10-21-graphe-dependances.md, ARCH-RISK-1104).

Three readers of a project's `.typ` find calls by their name and look at their arguments -- the migration of the report commands (domains/commands_migrate.py), the migration of the load names (domains/loads_migrate.py), and the graph of dependencies (domains/dependency_graph.py) --, and they read them through this one module: a call written inside a `#for` loop has no `#` before it, which `typst_objects_parse.parse_call_at` (a parametric object, `#doc-table(…)`) does not take, and what they need is the text of each argument, a string where it is one and the code as it stands where it is not.

**Comments.** A call in a comment -- `// #show-calc("dead-load", s)`, a section's note to itself -- calls nothing: `mask_comments` blanks `//` to the end of the line and `/* … */` (nested), keeping every offset, so a position found in the masked text is the file's. A `//` right after a `:` is a link (`https://`), not a comment. Qt-free; it imports nothing of Woodcore.
"""

import re

OPEN = {"(": ")", "[": "]", "{": "}"}
_STRING = re.compile(r'"((?:[^"\\\n]|\\.)*)"')


def closing(text, start):
    """The index of the bracket that closes the one at `start`, strings and nested brackets skipped; None where the text ends first."""
    stack = [OPEN[text[start]]]
    i = start + 1
    while i < len(text):
        c = text[i]
        if c == '"':
            i += 1
            while i < len(text) and text[i] != '"':
                i += 2 if text[i] == "\\" else 1
        elif c in OPEN:
            stack.append(OPEN[c])
        elif c in ")]}":
            if c != stack[-1]:
                return None
            stack.pop()
            if not stack:
                return i
        i += 1
    return None


def split(args):
    """A call's arguments as [(start, end)] spans of `args`, split at the top-level commas."""
    spans, depth, start, i = [], 0, 0, 0
    while i < len(args):
        c = args[i]
        if c == '"':
            i += 1
            while i < len(args) and args[i] != '"':
                i += 2 if args[i] == "\\" else 1
        elif c in "([{":
            depth += 1
        elif c in ")]}":
            depth -= 1
        elif c == "," and depth == 0:
            spans.append((start, i))
            start = i + 1
        i += 1
    if args[start:].strip():
        spans.append((start, len(args)))
    return spans


def literal(text):
    """The string a Typst or Python argument writes literally, None where it is anything else."""
    found = _STRING.fullmatch(text.strip())
    return found.group(1) if found else None


_NAMED = re.compile(r"\s*([A-Za-z_][A-Za-z0-9_-]*)\s*:(?!:)")


def arguments(args):
    """(positional, named): the text of each positional argument in order, and {name: text} of the named ones -- each as written, stripped."""
    positional, named = [], {}
    for a, b in split(args):
        part = args[a:b]
        key = _NAMED.match(part)
        if key and not part.strip().startswith('"'):
            named[key.group(1)] = part[key.end():].strip()
        else:
            positional.append(part.strip())
    return positional, named


def pair(text):
    """The two strings of a tuple written `("a", "b")`, or None -- a calculation's (domain, instance) as `domain:` names it."""
    text = (text or "").strip()
    if not (text.startswith("(") and text.endswith(")")):
        return None
    parts = [text[1:-1][a:b] for a, b in split(text[1:-1])]
    if len(parts) != 2:
        return None
    first, second = literal(parts[0]), literal(parts[1])
    return (first, second) if first is not None and second is not None else None


def mask_comments(text):
    """`text` with its comments blanked to spaces (line endings kept), every offset unchanged: what a reader of calls looks in."""
    out = list(text)
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c == '"':
            i += 1
            while i < n and text[i] not in '"\n':
                i += 2 if text[i] == "\\" else 1
            i += 1
        elif text.startswith("//", i) and (i == 0 or text[i - 1] != ":"):
            end = text.find("\n", i)
            end = n if end < 0 else end
            out[i:end] = " " * (end - i)
            i = end
        elif text.startswith("/*", i):
            depth, j = 1, i + 2
            while j < n and depth:
                if text.startswith("/*", j):
                    depth, j = depth + 1, j + 2
                elif text.startswith("*/", j):
                    depth, j = depth - 1, j + 2
                else:
                    j += 1
            for k in range(i, j):
                if out[k] != "\n":
                    out[k] = " "
            i = j
        else:
            i += 1
    return "".join(out)


def calls(text, names, masked=None):
    """Every call of one of `names` in `text`, outside its comments, as (name, start, args, line): `start` where its name begins, `args` the text between its brackets, `line` its line (from 1). A name is one standing alone -- not the end of a longer name, `my-show-calc` -- with or without a `#` before it; calls nested in another's arguments are found too."""
    if not names:
        return
    masked = mask_comments(text) if masked is None else masked   # a caller that reads the file more than once masks it once
    pattern = re.compile(r"(?<![A-Za-z0-9_-])(" + "|".join(re.escape(n) for n in sorted(names, key=len, reverse=True)) + r")\(")
    for found in pattern.finditer(masked):
        open_at = found.end() - 1
        close = closing(masked, open_at)
        if close is None:
            continue
        yield found.group(1), found.start(), text[open_at + 1:close], text.count("\n", 0, found.start()) + 1
