"""The public commands of lib/ as the reference reads them -- each binding's signature, its /// block parsed into a description, its parameters and its examples, its category -- split out of calc/tools/build_reference.py (issue #30), moved verbatim. build_reference.py imports every name back.
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
LIB_FILES = ("calc-engine.typ", "formula.typ", "i18n.typ")


# distance.typ (v0.87) is the fourth file of the engine: formula.typ imports its one command, `distance`, so it reaches the sections through commands.typ like the rest, and its helpers stay out of their scope -- they are listed under Internes all the same, being top-level bindings of lib/.
LIB_FILES += ("distance.typ",)


# timber.typ (v0.88) is the fifth, on distance.typ's arrangement: formula.typ imports its public commands by name, and its helpers are Internes.
LIB_FILES += ("timber.typ",)


# bibliography.typ (v0.99) is the sixth, likewise: formula.typ imports `show-bibliography` and `cite-norm` by name -- and `bib-note`, which the commands that take a `norm:` emit so that the document they cite is listed at the end of the report.
LIB_FILES += ("bibliography.typ",)


# summary.typ (v0.99) is the seventh: formula.typ imports its three commands by name -- and `summary-mark`, which `var` and `eq` call inside the registry update they already have when a call says `summary: true`.
LIB_FILES += ("summary.typ",)


# document.typ (the three document modes, phase 3) is the eighth -- rfem.typ, which was, was retired with the RFEM import in 0.117 (archive/rfem/): the parametric objects of a project's documents -- the convention d'utilisation, the base de projet and the statical report. formula.typ imports its eleven commands by name.
LIB_FILES += ("document.typ",)


# sheet.typ (v0.114) is the ninth: the export sheets -- a plan sheet A0 to A6 on which plans are set at a scale, beside a legend, a schematic section, texts and a title block. formula.typ imports its six commands by name.
LIB_FILES += ("sheet.typ",)


# positions.typ (v0.116) is the tenth: the list of the positions -- formula.typ imports `show-position-list` by name, and sheet.typ the table its `sheet-position-list` prints.
LIB_FILES += ("positions.typ",)


# steel.typ (issues #50-#52) is the eleventh: formula.typ imports its two commands by name -- the steel checks of Woodcore's «Acier» tabs, printed as the export computed them.
LIB_FILES += ("steel.typ",)


# What an engineer calls, in the order Woodcore's command tab lists it, and everything else (docs/typst/command-docs.md §10sexies). Hand-written and not derived: "carries a ///" would let resolve-level, parse-unit, natural-unit, key-symbol and fmt-magnitude in, which are documented internals, and would leave out position-ids and the three settings, which are public. The order inside a category is the order it is read in, not the order of the file.
#
# ⚠️ This list is the tab's contents. tests/test_commands.py checks it both ways -- a name here that the engine no longer defines, and a binding the engine defines that is named neither here nor implicitly internal -- so a command added to lib/ and given no category fails a test instead of quietly not existing for the reader.
#
# ⚠️ **The order of the categories is defined here and nowhere else**: Woodcore's tree, the website's navigation and its reference pages all follow it, and a category's name and its one-line introduction are calc/i18n/reference.json's (command_docs.category_label). What a report is written with comes first -- the engineer's order: calculating in the report, then showing what the export calculated.
CATEGORIES = (
    ("formula", (
        "var", "var-line", "var-unit", "eq", "unit", "var-domain", "val", "verify",
        # computed in the report from a diameter the call gives, like the lines above, and read from calc/norms/ rather than from the export (v0.87)
        "distance",
    )),
    ("display", (
        "calc-block", "show-connector", "show-calc", "show-input", "show-check",
        "show-live-load", "show-polar-moment", "show-connector-resistance",
        "show-plan", "show-plan-legend", "show-fire-plan", "show-static-model", "show-schema",
        # the report's revision journal, written by hand in Woodcore's «Journal» tab (v0.99)
        "show-journal",
        # the summary tables (v0.99): the loads and the main results of the whole report, gathered from the export and from what the report itself computed. Here rather than under "document" -- beside show-bibliography, which stands at the other end of the report and gathers what it cited -- because an engineer looking for how to summarise his loads looks where the loads are.
        "show-load-summary", "show-line-load-summary", "show-result-summary",
        # an excerpt of an annex -- a diagram of a FEM program's print report, framed in Woodcore's «Annexes» tab -- and the annexes it comes from, at the end of the report (v0.115)
        "show-extract", "show-annexes",
        # the list of the positions, STE Compact 02's «liste des positions» with this project's columns (v0.116)
        "show-position-list",
        # the quantities of the position plans, by material and section (issue #9)
        "show-plan-quantities",
    )),
    # the member checks of SIA 265 4.2 (v0.88): a member written down once, then each kind of action checked on it
    ("timber", (
        "member", "verify-tension", "verify-compression", "verify-compression-perp",
        "verify-bending", "verify-bending-normal",
        "verify-shear", "verify-shear-off", "verify-shear-perp",
        # a member check saved in Woodcore, resolved by the export and computed here with #member and the verify-* of its kind (calc/domains/member_check.py)
        "show-check-member", "check-member-ids",
    )),
    # the steel checks of SIA 263 saved in Woodcore's «Acier» tabs (issues #50-#52): computed by the export, printed here
    ("steel", (
        "show-check-steel", "check-steel-ids",
    )),
    # the parametric objects of a project's documents (the three document modes, phase 3): what Woodcore writes between the tags of a section of the convention d'utilisation, the base de projet or the report -- a table, the live loads and the non-structural self-weight, a field, a list to tick, a choice, a picture, a plan's extract, the signatures, the norms a section names
    ("objects", (
        "doc-table", "live-load-table", "dead-load-table",
        "doc-field", "doc-checklist", "doc-choice",
        "doc-image", "doc-plan", "doc-fire-plan", "doc-extract", "doc-annexes", "doc-signatures", "show-norm-list",
        "doc-value",
    )),
    # the export sheets (v0.114): a plan sheet of its own, Plans/<id>.typ, on which the position plans are placed at a scale beside a legend, a schematic section, texts and a title block -- each command one object of the sheet editor
    ("sheets", (
        "sheet", "sheet-text", "sheet-viewport", "sheet-fire-viewport", "sheet-section", "sheet-legend", "sheet-fire-legend", "sheet-titleblock",
        # the list of the positions on a sheet (v0.116)
        "sheet-position-list",
        # the quantities on a sheet (issue #9)
        "sheet-quantities",
    )),
    ("data", (
        "find",
        "position-ids", "domain-ids", "instance-ids", "connection-ids", "connector-ids", "project-info",
        "plan-ids", "plans-of", "fire-plan-ids", "static-model-ids", "schema-ids", "journal-entries",
        # the scripts of the project, one instance each of the `script` domain (v0.100)
        "script-ids",
        # the annexes' sources and excerpts (v0.115)
        "annex-ids", "extract-ids",
        "var-of", "value-of", "moisture-class-of",
        "get-value", "get-unit", "get-symbol", "get-label",
        "get-norm", "get-norm-ref", "get-description", "get-choices",
    )),
    ("format", (
        "fmt-number", "fmt-value", "fmt-decimals",
        "render-symbol", "render-formula", "render-prose",
    )),
    ("document", (
        # the bibliography at the end of the report, and a citation in the prose (v0.99): a part of the document, like its language and its metadata, and not a calculation of the export
        "show-bibliography", "cite-norm",
        "set-report-language", "report-language", "report-lang", "woodcore-document", "caption-rules",
        "t", "tl", "t-str", "tl-str", "t-label", "t-pattern", "t-of", "tl-of",
        "report-level", "uniform-level", "number-digits",
    )),
)


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


def parse_doc_comments(typ_path):
    """Pairs each /// block with the #let binding right after it -- the documented bindings of one file."""
    return [r for r in parse_bindings(typ_path) if r["doc_lines"]]


def lib_bindings(root):
    """Every top-level binding of the three files commands.typ re-exports, in file order.

    Each carries the category it belongs to, so the workbook and Woodcore's tab cannot place the same command differently.

    Until v0.64 this parser read lib/calc-engine.typ alone, so var, eq, verify, val, unit, var-domain, var-unit and the ten commands of lib/i18n.typ -- the whole of v0.60 and v0.61 -- were in no catalog at all (docs/typst/reference-workbook.md §10ter).
    """
    records = [r for name in LIB_FILES for r in parse_bindings(root / "lib" / name)]
    for record in records:
        record["category"] = category_of(record["name"])
    return records


def lib_records(root):
    """The documented ones of those, which is what the workbook's Functions and Parameters sheets list."""
    return [r for r in lib_bindings(root) if r["doc_lines"]]


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


def parse_param_docs(doc_lines):
    """(summary, [(param, type, meaning), ...]) -- the two function sheets' own reading of a doc block."""
    block = parse_doc_block(doc_lines)
    return block["summary"], block["bullets"]


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
