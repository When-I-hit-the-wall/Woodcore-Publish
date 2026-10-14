"""The `///` doc comments of the Typst command layer — the surface an engineer types against.

Tinymist reads these blocks and shows them as a tooltip while `Sections/*.typ` is being written, which is the whole reason docs/typst/api-conventions.md §10bis asks for them. A block can be wrong in four ways, and none of them breaks a build, so nothing but a check will catch them:

* **a parameter with no bullet** — the argument exists and the tooltip does not mention it;
* **a sink signature** — `#let eq(..args)`, which an editor shows as `eq(args: arguments) -> any`. Every named argument is then invisible, which is how this file came to exist: the engineer sent a screenshot of `#eq`'s tooltip asking where `unit:` had gone (v0.63.1). Only the *positional* tail may be variadic, because Typst has no optional positionals;
* **a detached block** — a plain `//` line between the `///` block and the `#let`, which silently detaches the whole thing. `render-symbol` had carried one since v0.49 and showed no tooltip at all;
* **no return line** — `-> any` in the tooltip, which says nothing about whether the thing can be put in a grid cell.

⚠️ This parses the `.typ` files itself rather than importing `calc/tools/build_reference.py`, which has a parser of its own. Two reasons, and the second is the honest one: a guard should not fail because the tool it guards is mid-refactor, and the two parsers disagreeing is itself a signal worth having. The same argument `test_constants.py` makes for its copies.
"""

import re

from conftest import ROOT

LIB = ROOT / "lib"

# A binding that is documented for the engineer: `#let name(` or `#let name = state(...)`.
BINDING = re.compile(r"^#let ([a-zA-Z][a-zA-Z0-9\-]*)\s*[(=]")


def _params(src, start):
    """The parameter names declared in the list that opens at src[start], `..rest` included."""
    depth, j, inner = 0, start, ""
    while j < len(src):
        if src[j] == "(":
            depth += 1
            if depth == 1:
                j += 1
                continue
        elif src[j] == ")":
            depth -= 1
            if depth == 0:
                break
        if depth >= 1:
            inner += src[j]
        j += 1
    names, depth, cur = [], 0, ""
    for ch in inner + ",":
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        if ch == "," and depth == 0:
            if cur.strip():
                names.append(cur.split(":")[0].strip())
            cur = ""
        else:
            cur += ch
    return names


def documented():
    """Every documented binding of lib/: (file, line, name, declared params, doc lines)."""
    out = []
    for path in sorted(LIB.glob("*.typ")):
        lines = path.read_text(encoding="utf-8").split("\n")
        for n, line in enumerate(lines):
            m = BINDING.match(line)
            if not m or not (n and lines[n - 1].startswith("///")):
                continue
            k = n - 1
            while k >= 0 and lines[k].startswith("///"):
                k -= 1
            params = _params(line, 0) if "(" in line.split("=")[0] else []
            out.append((path.name, n + 1, m.group(1), params, lines[k + 1:n]))
    return out


def bullets(doc):
    """Every parameter name a doc block documents, including two named on one line."""
    names = set()
    for line in doc:
        b = re.match(r"/// - (\.{0,2}[a-zA-Z][a-zA-Z0-9\-]*)", line)
        if b:
            names.add(b.group(1))
            for extra in re.finditer(r"(\.{0,2}[a-zA-Z][a-zA-Z0-9\-]*) \(", line):
                names.add(extra.group(1))
    return names


def test_the_library_is_documented_at_all():
    """A guard on the guard: if the parser stops matching, every test below passes vacuously."""
    found = documented()
    assert len(found) >= 55, f"only {len(found)} documented bindings found — has the parser drifted?"
    names = {r[2] for r in found}
    for expected in ("show-calc", "var", "eq", "verify", "unit", "var-unit", "t-str", "calc-block"):
        assert expected in names, f"{expected} is not documented, or the parser missed it"


def test_every_declared_parameter_carries_a_bullet():
    """An argument the tooltip does not mention is an argument the engineer cannot find."""
    bad = []
    for file, line, name, params, doc in documented():
        missing = [p for p in params if p.lstrip(".") and p not in bullets(doc)]
        if missing:
            bad.append(f"{file}:{line} {name}() — undocumented: {', '.join(missing)}")
    assert not bad, "parameters with no `/// - name (type):` bullet:\n  " + "\n  ".join(bad)


def test_no_public_command_hides_its_arguments_behind_a_sink():
    """`#let eq(..args)` shows as `eq(args: arguments)` — every named argument invisible (v0.63.1).

    A variadic tail is fine and sometimes necessary (an optional positional symbol, a template's holes); a signature that is *nothing but* a variadic tail is not.
    """
    bad = []
    for file, line, name, params, doc in documented():
        if params and all(p.startswith("..") for p in params):
            bad.append(f"{file}:{line} {name}({', '.join(params)})")
    assert not bad, (
        "these declare nothing but a variadic sink, so an editor shows none of their arguments:\n  "
        + "\n  ".join(bad)
        + "\n  Declare the named arguments one by one and keep `..rest` for the positional tail only."
    )


def test_every_doc_block_ends_in_a_return_line():
    """`-> content` is what says a command's result can go in a grid cell; `-> any` says nothing."""
    bad = []
    for file, line, name, params, doc in documented():
        arrows = [d for d in doc if re.match(r"///\s*->", d)]
        if len(arrows) != 1:
            bad.append(f"{file}:{line} {name} — {len(arrows)} `-> ` lines, expected exactly 1")
        elif arrows[0] != doc[-1]:
            bad.append(f"{file}:{line} {name} — the `-> ` line is not the last of the block")
    assert not bad, "return types:\n  " + "\n  ".join(bad)


def test_a_union_of_types_is_written_with_a_pipe():
    """One spelling, so the catalogue and the tooltip read alike: `int | none`, never `int, none`."""
    bad = []
    for file, line, name, params, doc in documented():
        for d in doc:
            if re.match(r"///\s*->", d) and "," in d:
                bad.append(f"{file}:{line} {name} — {d.strip()}")
    assert not bad, "write a union of return types with `|`:\n  " + "\n  ".join(bad)


def test_no_doc_block_is_detached_from_its_binding():
    """A `//` line between a `///` block and its `#let` silently detaches it: no tooltip at all.

    `render-symbol` had one from v0.49 to v0.63.1 and nobody could see its documentation.
    """
    bad = []
    for path in sorted(LIB.glob("*.typ")):
        lines = path.read_text(encoding="utf-8").split("\n")
        for n, line in enumerate(lines):
            if not line.startswith("///"):
                continue
            if n + 1 < len(lines) and (lines[n + 1].startswith("///") or BINDING.match(lines[n + 1])):
                continue
            bad.append(f"{path.name}:{n + 1} — {line.strip()[:60]}")
    assert not bad, (
        "these `///` lines are followed by neither more `///` nor a `#let`, so nothing carries them:\n  "
        + "\n  ".join(bad)
    )
