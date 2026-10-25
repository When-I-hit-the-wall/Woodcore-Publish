"""The public commands of lib/ as the reference reads them -- each binding's signature, its /// block parsed into a description, its parameters and its examples, its category -- split out of calc/build_reference.py (issue #30), moved verbatim. build_reference.py imports every name back.
"""

import re
from pathlib import Path


DOC_LINE_RE = re.compile(r"^\s*///\s?(.*)$")


LET_FN_RE = re.compile(r"^#let\s+([a-zA-Z][\w-]*)\(")


# `..rest` is a parameter like any other and is documented like one, so the leading dots are part of the name: without them the line would be read as prose and the argument would lose its row.
BULLET_RE = re.compile(r"^-\s+(\.{0,2}[\w-]+)\s*\(([^)]*)\)\s*:\s*(.*)$")


# Two arguments documented on one line, `- norm (str, none), norm-ref (str): the citation` -- four commands of lib/formula.typ write them so. BULLET_RE matches no such line, so until v0.86 it was read as the continuation of the bullet above it: `norm` and `norm-ref` had no row in the commands tab or the workbook, and `level`'s meaning ended in their text. Each name now gets a row of its own, the meaning shared.
MULTI_BULLET_RE = re.compile(r"^-\s+((?:\.{0,2}[\w-]+\s*\([^)]*\)\s*,\s*)+\.{0,2}[\w-]+\s*\([^)]*\))\s*:\s*(.*)$")


BULLET_NAME_RE = re.compile(r"(\.{0,2}[\w-]+)\s*\(([^)]*)\)")


# Any top-level binding, function or not. LET_FN_RE above wants a `(` straight after the name, so `#let report-level = state("report-level", 1)` matched nothing and the four settings of the document were invisible to this parser until v0.64 (docs/typst/command-docs.md §10sexies).
LET_RE = re.compile(r"^#let\s+([a-zA-Z][\w-]*)\s*(\(|=)")


# A fenced block inside a /// comment: one worked example. One fence is one example -- several examples in one fence would share a page and an arrow.
#
# ```typ is compiled: Woodcore's command tab renders it and tests/test_commands.py holds it. ```typ-dry is shown and never compiled, for the one example that cannot run against this project's own data: show-check reads an instance's `checks[]`, and nothing exports one yet (docs/open-questions.md §14). Printing Typst's error for a situation the documentation already explains would say nothing; leaving the command without an example would say less.
FENCE_RE = re.compile(r"^```([A-Za-z0-9_-]*)\s*$")


RUNNABLE_FENCE = "typ"


# The three files commands.typ re-exports, in the order the tab lists them. i18n.typ is never named there: it arrives through calc-engine.typ, which imports it with a wildcard of its own (docs/typst/language.md §4bis).
LIB_FILES = ("calc-engine.typ", "number.typ", "subscript.typ", "calc-engine-core.typ", "calc-engine-drawings.typ", "calc-engine-display.typ", "calc-engine-records.typ", "calc-engine-connections.typ", "formula.typ", "i18n.typ")  # calc-engine.typ a façade over its five parts since v0.120 (spec 2026-10-19-base-saine-nettoyage, G9)


# distance.typ (v0.87) is the fourth file of the engine: formula.typ imports its one command, `distance`, so it reaches the sections through commands.typ like the rest, and its helpers stay out of their scope -- they are listed under Internes all the same, being top-level bindings of lib/.
LIB_FILES += ("distance.typ",)


# bibliography.typ (v0.99) is the sixth, likewise: formula.typ imports `show-bibliography` and `cite-norm` by name -- and `bib-note`, which the commands that take a `norm:` emit so that the document they cite is listed at the end of the report.
LIB_FILES += ("bibliography.typ",)


# document.typ (the three document modes, phase 3): what is left of the parametric objects of a project's documents once they were written in raw Typst (spec 2026-10-21-commandes-typst-refonte, REQ-019) -- the list of the norms a document cites, `show-norm-list`.
LIB_FILES += ("document.typ",)


# sheet.typ (v0.114): the export sheets -- the page, internal, and the three images a sheet's raw `#place` holds besides the plans, `image-section`, `image-legend`, `image-titleblock` (spec 2026-10-21-commandes-typst-refonte, Q-013, Q-015).
LIB_FILES += ("sheet.typ",)


# positions.typ (v0.116): a position on its line, `#position` (spec 2026-10-21-commandes-typst-refonte, REQ-015).
LIB_FILES += ("positions.typ",)


# What an engineer calls, in the order Woodcore's command tab lists it, and everything else (docs/typst/command-docs.md §10sexies). Hand-written and not derived: "carries a ///" would let resolve-level, parse-unit, natural-unit, key-symbol and fmt-magnitude in, which are documented internals, and would leave out position-ids and the three settings, which are public. The order inside a category is the order it is read in, not the order of the file.
#
# ⚠️ This list is the tab's contents. tests/test_commands.py checks it both ways -- a name here that the engine no longer defines, and a binding the engine defines that is named neither here nor implicitly internal -- so a command added to lib/ and given no category fails a test instead of quietly not existing for the reader.
#
# ⚠️ **The order of the categories is defined here and nowhere else**: Woodcore's tree, the website's navigation and its reference pages all follow it, and a category's name and its one-line introduction are calc/i18n/reference.json's (command_docs.category_label). The categories go by task, what a report is written with first and the building blocks of a template last (the engineer's order, 24.10.2026): calculating in the report, printing a drawing or an object, reading the project's data, the document and its citations, writing a template.
CATEGORIES = (
    ("formula", (
        "var", "eq", "unit", "verify",
        # the fine display arguments' own commands (spec 2026-10-21-commandes-typst-refonte, REQ-006, REQ-008): the defaults of the lines that follow, and the calculation domain that replaced var-domain
        "calc-defaults", "domain",
        # what a domain's file prints from a level on, a figure of the norm at level 3 alone (spec 2026-10-23-onglet-vent-briques, D-29)
        "from-level",
        # the variables of one role listed from the registry, of a domain or of all (REQ-010): the summaries' successor (Q-009)
        "var-table",
        # computed in the report from a diameter the call gives, like the lines above, and read from calc/norms/ rather than from the export (v0.87)
        "distance",
    )),
    ("display", (
        # the six drawings as images for a native #figure, its caption and its label the document's own (spec 2026-10-21-commandes-typst-refonte, REQ-013, REQ-014, ARCH-012; image-polar-moment, spec 2026-10-22-image-polar-moment)
        "image-positions-plan", "image-fire-plan", "image-static-model", "image-schema", "image-extract", "image-polar-moment",
        # what an export sheet's raw #place holds besides the plans: its section, its legend, its title block (Q-013, Q-015)
        "image-section", "image-legend", "image-titleblock",
        # the annexes at the end of the report, whose excerpts image-extract shows (v0.115)
        "show-annexes",
        # one position on a line, its fields chosen (spec 2026-10-21-commandes-typst-refonte, REQ-015): what #member printed of a position
        "position",
    )),
    ("data", (
        "find",
        # a value Woodcore keeps in step inside a document written in raw Typst (spec 2026-10-21-commandes-typst-refonte, REQ-011)
        "sync",
        # the file of a domain Woodcore wrote, or of a document's journal, what a section includes it by (spec 2026-10-21-commandes-typst-refonte, ARCH-008)
        "domain-file",
        # the ids of every object of one kind -- positions, domains and their instances, connections, connectors, scripts, plans, fire plans, static models, schemas, annexes and excerpts, member and steel checks -- one command since v0.120
        "ids", "project-info", "plans-of", "journal-entries",
        # one field of a variable, one command since v0.120
        "get",
    )),
    ("document", (
        # the bibliography at the end of the report, and a citation in the prose (v0.99): a part of the document, like its language and its metadata, and not a calculation of the export
        "show-bibliography", "cite-norm",
        # the list of the norms a document cites, the one parametric object of the documents left (spec 2026-10-21-commandes-typst-refonte, REQ-019)
        "show-norm-list",
        "set-report-language", "report-language", "report-lang", "woodcore-document", "caption-rules", "doc-tables",
        "t", "tl", "t-str", "tl-str", "t-label", "t-pattern", "t-of", "tl-of",
        "report-level", "uniform-level",   # number-digits left them in v0.120: one display rule, lib/number.typ
        "show-masked",   # the preview of «Affichage» shows what the report hides (spec 2026-10-22-onglet-neige-type, UI-011)
    )),
    # the building blocks of a template of one's own, last: what a report is written with comes first (the engineer, 24.10.2026, issue #115 answer 3)
    ("format", (
        "fmt-number", "fmt-value", "fmt-decimals",
        "render-symbol", "render-formula", "render-prose",
    )),
)


# The commands of CATEGORIES that take no `level:`, and why (spec 2026-10-20-indices-et-niveaux, UI-003, ARCH-003, D-03, D-08). Every command that prints a figure, a table or a list takes one (Q-007 of the base saine: `show-*`, `verify-*`, `distance`, `doc-*`, `sheet-*`); these do not, each for the reason given -- an accessor prints nothing, and a field, a table of a document or a sheet's text prints what the engineer wrote, complete or wrong (Q-003, D-08). tests/test_command_levels.py checks it both ways: a public command takes `level:` or is named here, never both, and a name here is a public command.
_ACCESSOR = "an accessor: it gives a value and prints nothing (Q-007 of the base saine)"
_DOCUMENT = "sets up the document or its language: it prints no figure, table or list"
NO_LEVEL = {
    "unit": "a unit written in a formula, read and not printed by itself",
    "calc-defaults": "a setting of the lines that follow, which prints nothing of its own (spec 2026-10-21-commandes-typst-refonte, REQ-006)",
    "domain-file": "an accessor: it gives the path of a file, which `#include` prints (ARCH-008)",
    "sync": "a value kept in step, printed as it is written: its content says what it shows (REQ-011)",
    "position": "one position on a line, the same at every level: the fields its call names (REQ-015)",
    "from-level": "its level is its first argument: what it holds is printed from that level on, never at a level of its own (spec 2026-10-23-onglet-vent-briques, D-29)",
    **{name: "a drawing for a native #figure: what it shows is its `detail-figure` and `detail-legend`, the same at every level (REQ-013, D-13)" for name in ("image-positions-plan", "image-fire-plan", "image-static-model", "image-schema", "image-extract", "image-polar-moment")},
    **{name: "a part of an export sheet, held by a #place: a sheet prints at level 2 (Q-015)" for name in ("image-section", "image-legend", "image-titleblock")},
    "var-table": "a table of the variables its call chooses -- their role, their domain, their unit and its columns --, which the lines it lists each print at their own level (REQ-010)",
    **{name: _ACCESSOR for name in ("find", "ids", "project-info", "plans-of", "journal-entries", "get",
                                    "fmt-number", "fmt-value", "fmt-decimals", "render-symbol", "render-formula", "render-prose",
                                    "t", "tl", "t-str", "tl-str", "t-label", "t-pattern", "t-of", "tl-of")},
    "cite-norm": "a citation in a sentence: the norm follows what is cited, not a level (docs/decisions.md, «the norm follows the record»)",
    **{name: _DOCUMENT for name in ("set-report-language", "report-language", "report-lang", "woodcore-document", "caption-rules", "doc-tables", "report-level", "uniform-level", "show-masked")},
}

# The commands whose levels print the same thing, which ones, and why (UI-003, D-07): a figure or a table that has no source and no citation to add prints at 3 what it prints at 2; a command that accepts `level:` for the sections written before and has nothing to leave out prints the same at all three. Every other command taking `level:` prints something different at each. tests/test_command_levels.py compiles each at 1, 2 and 3 and holds it to this.
LEVELS_CONFOUNDED = {
    "show-annexes": ((2, 3), "an annex's cover names its source and its pages from level 2 already"),
    "show-norm-list": ((2, 3), "a list of norms is its own citation: level 2 already gives each one whole"),
    "show-bibliography": ((2, 3), "a bibliography is its own citation: level 2 already gives each entry whole"),
    "distance": ((2, 3), "its citation, the norm's table, is printed from level 2 already"),
}


INTERNAL = "internal"  # everything the wildcard also exports: listed apart, folded, with no example and no call to copy


def category_of(name):
    """The category one binding belongs to, INTERNAL for everything not named above."""
    for key, names in CATEGORIES:
        if name in names:
            return key
    return INTERNAL


def read_signature(lines, i):
    """The parameter list of the `#let` at line `i`, joined across lines.

    A signature long enough to wrap -- show-typst-calc's -- used to match nothing, so the function silently vanished from this catalog. Reads to the closing parenthesis instead of to the end of the line.

    Returns (name, params, last_line_index), or None if line `i` does not start a `#let` function.
    """
    m = LET_FN_RE.match(lines[i])
    if not m:
        return None
    name = m.group(1)
    chunk = lines[i][m.end() - 1:]  # from the opening parenthesis
    params, depth, j = "", 0, i
    while True:
        for ch in chunk:
            if ch == "(":
                depth += 1
                if depth == 1:
                    continue  # the parameter list's own opening paren
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    # a wrapped signature usually ends on a trailing comma
                    return name, " ".join(params.split()).rstrip(","), j
            params += ch
        params += " "
        j += 1
        if j >= len(lines):
            return None  # unbalanced -- not a signature we can read
        chunk = lines[j]


def value_signature(name, line):
    """How a binding that is not a function is written down: `number-digits = state("number-digits", 3)`.

    Only the first line is read. One that opens a bracket and carries on -- a table of unit prefixes -- is closed with an ellipsis rather than reproduced: what a reader wants of such a binding is that it exists and where, not its 40 rows.
    """
    rhs = line.split("=", 1)[1].strip() if "=" in line else ""
    if rhs.endswith(("(", "[", "{")) or not rhs:
        rhs = (rhs[:-1].strip() + "(…)") if rhs[:-1].strip() else "(…)"
    elif len(rhs) > 80:
        rhs = rhs[:79] + "…"
    return f"{name} = {rhs}"


def read_binding(lines, i):
    """The top-level `#let` at line `i`: its name, its parameter list where it is a function, and the last line it spans.

    Returns (name, params, last_line_index, kind) with kind "function" or "value", or None where line `i` starts no top-level binding. A value binding has params None, so a state is catalogued beside the commands that read it instead of vanishing (docs/typst/command-docs.md §10sexies).
    """
    m = LET_RE.match(lines[i])
    if not m:
        return None
    if m.group(2) == "(":
        signature = read_signature(lines, i)
        if signature is None:
            return None
        name, params, last = signature
        return name, params, last, "function"
    return m.group(1), None, i, "value"


def parse_bindings(typ_path):
    """Every top-level `#let` of one .typ file, documented or not, in file order.

    A binding with no /// block carries an empty `doc_lines`. That is what lets Woodcore list the helpers `commands.typ`'s wildcard also exports, apart and folded (docs/typst/command-docs.md §10sexies), and what lets tests/test_commands.py see a command added to the engine and given no category.
    """
    path = Path(typ_path)
    lines = path.read_text(encoding="utf-8").splitlines()
    records, buffer = [], []
    i = 0
    while i < len(lines):
        m_doc = DOC_LINE_RE.match(lines[i])
        if m_doc:
            buffer.append(m_doc.group(1))
            i += 1
            continue
        binding = read_binding(lines, i)
        if binding is not None:
            name, params, last, kind = binding
            records.append({
                "name": name,
                "file": path.name,
                "line": i + 1,
                "kind": kind,
                "params": params,
                "signature": f"{name}({params})" if kind == "function" else value_signature(name, lines[i]),
                "doc_lines": buffer,
            })
            i = last + 1
        else:
            i += 1
        buffer = []
    return records


def lib_bindings(root):
    """Every top-level binding of the three files commands.typ re-exports, in file order.

    Each carries the category it belongs to, so the workbook and Woodcore's tab cannot place the same command differently.

    Until v0.64 this parser read lib/calc-engine.typ alone, so var, eq, verify, val, unit, var-domain, var-unit and the ten commands of lib/i18n.typ -- the whole of v0.60 and v0.61 -- were in no catalog at all (docs/typst/reference-workbook.md §10ter).
    """
    records = [r for name in LIB_FILES for r in parse_bindings(root / "lib" / name)]
    for record in records:
        record["category"] = category_of(record["name"])
    return records


def parse_doc_block(doc_lines):
    """One /// block, split into what each reader needs: its summary, its further paragraphs, its ```typ examples and its `- name (type):` argument lines.

    A `-> type: ...` return-value line, and any line continuing it, is dropped entirely -- it documents the return value, not a param, and there's no return-value column in the reference sheet to put it in.

    ⚠️ A fenced example is kept out of the prose. Nothing depended on that while only lib/calc-engine.typ was read, which carries no fence; the moment lib/formula.typ is read as well, six summaries would otherwise swallow the code of their own example.
    """
    paragraphs, bullets, examples, returns = [], [], [], []
    prose, fence, tag, current = [], None, None, None
    in_return = False
    for raw in doc_lines:
        line = raw.strip()
        m_fence = FENCE_RE.match(line)
        if m_fence is not None:
            if fence is None:
                fence, tag = [], m_fence.group(1)
            else:
                examples.append({"code": "\n".join(fence).strip("\n"), "render": tag == RUNNABLE_FENCE})
                fence, tag = None, None
            continue
        if fence is not None:
            fence.append(raw)  # not stripped: a fence is code, and its indentation is part of it
            continue
        m = BULLET_RE.match(line)
        m_multi = None if m else MULTI_BULLET_RE.match(line)
        if m:
            current = [[m.group(1), m.group(2), m.group(3)]]
            bullets.extend(current)
            in_return = False
        elif m_multi:
            current = [[name, kind, m_multi.group(2)] for name, kind in BULLET_NAME_RE.findall(m_multi.group(1))]
            bullets.extend(current)
            in_return = False
        elif line.startswith("->"):
            current = None
            in_return = True
            returns.append(line[2:].strip())
        elif in_return:
            if line:
                returns.append(line)
            continue
        elif current is not None:
            if line:
                for bullet in current:
                    bullet[2] += " " + line
        elif line:
            prose.append(line)
        elif prose:
            paragraphs.append(" ".join(prose))
            prose = []
    if prose:
        paragraphs.append(" ".join(prose))
    if fence is not None:  # an unclosed fence: keep what it held rather than lose it silently
        examples.append({"code": "\n".join(fence).strip("\n"), "render": tag == RUNNABLE_FENCE})
    return {
        "summary": " ".join(paragraphs),
        "paragraphs": paragraphs,
        "bullets": [tuple(b) for b in bullets],
        "examples": examples,
        "returns": " ".join(returns),
    }


VARIADIC = ".."


def split_params(params):
    """A parameter list as (name, default) pairs, the default None for a positional one.

    Splits on the commas at depth zero, so a default carrying brackets of its own -- `(:)`, `("a", "b")` -- stays whole.
    """
    parts, depth, current = [], 0, ""
    for ch in params:
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append(current)
            current = ""
        else:
            current += ch
    parts.append(current)
    pairs = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if ":" in part and not part.startswith(VARIADIC):
            pname, default = part.split(":", 1)
            pairs.append((pname.strip(), default.strip()))
        else:
            pairs.append((part, None))
    return pairs
