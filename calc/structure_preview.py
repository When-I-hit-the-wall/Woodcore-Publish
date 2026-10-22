"""The page a selection of the «Structure du document» tab compiles to (the engineer's rework of 01.10.2026, work package R2-D1): **the preview of the selected node only**.

The centre of the tab shows what the engineer has chosen in the tree and nothing else -- a chapter, only that chapter's printed sections; a section, only it; an object, only that object; nothing chosen, or the document itself, the whole document (which is the tab's own full compile, and not a snippet). This module works out **the Typst source of that small document**; it reads the project's files and writes none, imports no Qt, and is held by tests/test_structure_preview.py without a window.

**A snippet is a document of its own, compiled from standard input** against the project's folder as the Typst root -- nothing is written into the engineer's project to render a preview -- which is why every path in it is written **from the root** (`include "/1_Convention d'utilisation/Sections/purpose.typ"`), the one spelling that does not depend on where the source lies. What it carries is the least that makes a section print as it does in the document:

* the project's own **config.typ** (`conf`), so the font, the margins and the line breaking are the printed page's -- with the page as **tall as it needs to be** (`height: auto`), so that one table is a page the height of a table and a paragraph one the height of a paragraph, **as wide as the document's text plus a margin of 0.8 cm** (`page_line`; the text's width is read from the config.typ -- 16 cm where it cannot be told), so that the lines break where the printed page breaks them and the page fills the pane it is fitted to instead of being a whole A4 whose text is set at two thirds of its size, and without a footer or a heading number, which a part of a document has no sense of;
* the engine (`/commands.typ`), the **document** it belongs to (`wc-document`, which `show-journal` reads: the journal printed is this document's) and the **language** its entry file sets the engine to;
* for a **section**, the very lines the document's entry file includes it with: `#{ set heading(offset: depth - 1); include "…" }` -- the offset the section has in the document, so that its headings are at their own levels -- and for a **chapter** its heading, `#heading(level: depth, "Title")`, and the sections it holds that are printed (a disabled section, and everything under a disabled chapter, is left out of a chapter's page, as it is left out of the document's);
* for an **object**, the file's **preamble** -- the `#import`, `#let`, `#set` and `#show` lines that stand before its first tag, which is what the object may rely on -- and the object's body as it is written in the file, under the heading offset of its section.

The report (rs) has no groups and no offset: its sections are the `#include` lines of its entry file, and a section is included as it is. A heading inside a file that carries no tags is not an object and cannot be previewed alone: it stands for its file.

A node the document does not print -- a section switched off -- is **shown all the same** when it is the node chosen: the engineer who has just chosen it is looking at what it would print.
"""

import hashlib
import os
import re
from dataclasses import dataclass
from pathlib import Path

import project
import structure
import validation
import templates
import typst_objects
import typst_paths

# The lines of a section's preamble: what the code of a file may state before its first tag, and an object relies on.
PREAMBLE = ("#import", "#let", "#set", "#show")
# The report's engine language where the entry file says none.
DEFAULT_LANGUAGE = "de"
# The level the preview is compiled at: the document's own default.
LEVEL = 2
# The page of a snippet: **as wide as the document's text plus a small margin** (`page_line`), as tall as it needs, no footer, no header, no number. Its width is not the paper's: a part of a document is shown fitted to the width of a pane about 600 px wide, and a whole A4 page there sets the text at two thirds of its size -- the line breaking is the printed document's, and the page fills the pane.
SIDE_CM = 0.8
UPDOWN_CM = 1.0
PAGE_REST = f"height: auto, margin: (x: {SIDE_CM}cm, y: {UPDOWN_CM}cm), header: none, footer: none, numbering: none"
# The measure of the report's text where the project's config.typ does not say it in a form this module reads: 16 cm, an A4 less the margins the neutral style sets.
DEFAULT_TEXT_WIDTH_CM = 16.0
# The papers Typst names, as (width, height) in centimetres -- the ones a config.typ is likely to set.
PAPERS_CM = {
    "a3": (29.7, 42.0), "a4": (21.0, 29.7), "a5": (14.8, 21.0), "a6": (10.5, 14.8),
    "b4": (25.0, 35.3), "b5": (17.6, 25.0), "us-letter": (21.59, 27.94), "us-legal": (21.59, 35.56),
}
_UNITS_CM = {"cm": 1.0, "mm": 0.1, "pt": 2.54 / 72, "in": 2.54}
_LENGTH = re.compile(r"^\s*(-?\d+(?:\.\d+)?|-?\.\d+)\s*(cm|mm|pt|in)\s*$")


@dataclass(frozen=True)
class Snippet:
    """What a selection compiles to: its Typst `source`, a `key` that names it (the hash of the source and the document), the ids of the nodes it shows (`ids`, in document order, a node whose ancestor is chosen too left out), what it shows (`kind`: `group`, `file`, `object`, or `mixed`) and the files it reads (`files`), which a window watches."""
    source: str
    key: str
    ids: tuple
    kind: str
    files: tuple = ()


def _quote(text):
    return structure.typst_string(text)


# -- the width of the page -----------------------------------------------------------------------------------

def _strip_comments(text):
    """`text` with the `//` comments taken out -- a `//` inside a string is no comment."""
    out = []
    for line in text.splitlines():
        quoted, i = False, 0
        while i < len(line):
            ch = line[i]
            if quoted:
                i += 2 if ch == "\\" else 1
                quoted = quoted and not (ch == '"')
                continue
            if ch == '"':
                quoted = True
            elif line.startswith("//", i):
                line = line[:i]
                break
            i += 1
        out.append(line)
    return "\n".join(out)


def _balanced(text, open_at):
    """What lies between the parenthesis at `open_at` and the one that closes it -- None where it is never closed."""
    depth, i, quoted = 0, open_at, False
    while i < len(text):
        ch = text[i]
        if quoted:
            if ch == "\\":
                i += 1
            elif ch == '"':
                quoted = False
        elif ch == '"':
            quoted = True
        elif ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
            if depth == 0:
                return text[open_at + 1:i]
        i += 1
    return None


def _split_top(text):
    """`text` cut at the commas that are not inside a bracket or a string."""
    parts, current, depth, quoted, i = [], [], 0, False, 0
    while i < len(text):
        ch = text[i]
        if quoted:
            current.append(ch)
            if ch == "\\" and i + 1 < len(text):
                i += 1
                current.append(text[i])
            elif ch == '"':
                quoted = False
        elif ch == '"':
            quoted = True
            current.append(ch)
        elif ch in "([{":
            depth += 1
            current.append(ch)
        elif ch in ")]}":
            depth -= 1
            current.append(ch)
        elif ch == "," and depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(ch)
        i += 1
    parts.append("".join(current))
    return [part for part in parts if part.strip()]


def _named(arguments):
    """{name: the text of its value} of the named arguments of a call, at its top level."""
    found = {}
    for part in _split_top(arguments):
        name, colon, value = part.partition(":")
        if colon and re.fullmatch(r"\s*[A-Za-z][\w-]*\s*", name):
            found[name.strip()] = value.strip()
    return found


def _length_cm(text):
    """A Typst length in centimetres; ValueError where it is none this module reads (an `em`, a percentage, a computed one)."""
    found = _LENGTH.match(text or "")
    if found is None:
        raise ValueError(text)
    return float(found.group(1)) * _UNITS_CM[found.group(2)]


def text_width_cm(here):
    """The width of the text of the project's pages, in centimetres, as its form (`Template/template.typ`) and its config.typ set it -- the paper (or the `width`) less the left and right margins of its `set page(…)` rules, read in order, the later one winning for what it states. None where it cannot be told: no config.typ, a length in a unit this reads not (`em`, `%`), a margin that is computed. A margin left out is Typst's own: 2.5/21 of the shorter side."""
    try:
        text = _strip_comments(typst_paths.read_text(here.config_typ))
    except (OSError, UnicodeDecodeError):
        return None
    # The page is the **form's** (`Template/template.typ`, calc/forms.py), which config.typ calls and then writes its own adjustments over: the form's rules are read first, so that the later ones win as they do in the compile.
    form = Path(here.config_typ).parent / project.TEMPLATE_FOLDER / "template.typ"   # beside config.typ, wherever the project keeps it (000-Typst-Config/ laid out by folders, issue #64)
    if form.is_file():
        try:
            text = _strip_comments(typst_paths.read_text(form)) + chr(10) + text
        except (OSError, UnicodeDecodeError):
            pass
    size, margin, flipped = list(PAPERS_CM["a4"]), None, False
    try:
        for found in re.finditer(r"\bset\s+page\s*\(", text):
            arguments = _balanced(text, found.end() - 1)
            if arguments is None:
                continue
            named = _named(arguments)
            if "paper" in named:
                name = named["paper"].strip().strip('"')
                if name not in PAPERS_CM:
                    return None
                size = list(PAPERS_CM[name])
            if "width" in named:
                size[0] = _length_cm(named["width"])
            if "height" in named and named["height"] != "auto":
                size[1] = _length_cm(named["height"])
            if "flipped" in named:
                flipped = named["flipped"] == "true"
            if "margin" in named:
                value = named["margin"]
                if value == "auto":
                    margin = None
                elif value.startswith("("):
                    margin = {key: _length_cm(item) for key, item in _named(value[1:-1]).items()}
                else:
                    margin = {"rest": _length_cm(value)}
    except ValueError:
        return None
    if flipped:
        size.reverse()
    default = 2.5 / 21 * min(size)
    margin = margin if margin is not None else {}
    rest = margin.get("rest", default)
    left = margin.get("left", margin.get("inside", margin.get("x", rest)))
    right = margin.get("right", margin.get("outside", margin.get("x", rest)))
    width = size[0] - left - right
    return round(width, 3) if 5.0 <= width <= size[0] else None


def page_line(here):
    """The `#set page(…)` a snippet carries: the width of the document's text and a margin of `SIDE_CM` each side -- 16 cm where the project's config.typ does not say -- as tall as the content, with no header, footer or number."""
    width = text_width_cm(here) or DEFAULT_TEXT_WIDTH_CM
    return f"#set page(width: {width + 2 * SIDE_CM:.2f}cm, {PAGE_REST})"


def from_root(here, path):
    """`path` as a path from the Typst root, written the way Typst reads one that starts at it: `/1_Convention d'utilisation/Sections/purpose.typ`."""
    root, path = Path(here.typst_root), Path(path)
    try:
        rel = path.relative_to(root)
    except ValueError:
        rel = Path(os.path.relpath(path, root))
    return "/" + rel.as_posix()


def language_of(here, mode):
    """The language the engine prints in for document `mode`: its entry file's `set-report-language` default, else the document's own (config.typ), else German."""
    document, report = templates.read_languages(here.document_typ(mode))
    for lang in (report, document):
        if lang in structure.LANGUAGES:
            return lang
    return DEFAULT_LANGUAGE


def header(here, mode, language=None):
    """The lines every snippet starts with: the project's `conf`, the page, the engine, the document and the language. No state is set that a part of a document has no use for -- no title page, no outline, no revision attachment."""
    language = language or language_of(here, mode)
    return [
        f'#import "{here.from_root(here.config_typ)}": conf',   # in 000-Typst-Config/ laid out by folders (issue #64)
        f'#import "{here.from_root(here.commands_typ)}": *',
        "#show: conf",
        page_line(here),
        "#set heading(numbering: none)",
        f'#wc-document.update("{mode}")',
        f'#set-report-language("{language}")',
        f"#report-level.update({LEVEL})",
        "#number-digits.update(3)",
    ]


def preamble(text):
    """The lines of a section's text that precede its first tag and are code of the kind an object relies on (`PREAMBLE`), as one string, each ended by a line break -- what an object's preview is given before its body. Comments, blank lines and anything that prints are not part of it."""
    out = []
    for line in re.findall(r"[^\r\n]*(?:\r\n|\r|\n)|[^\r\n]+", text):
        bare = line.strip()
        if bare.startswith("// woodcore:"):
            break
        if bare.startswith(PREAMBLE):
            out.append(bare + "\n")
    return "".join(out)


def _family(nodes):
    flat = structure.flatten(nodes)
    return flat, {node.id: node for node in flat}


def _depth(by_id, node):
    """How deep a node lies in a convention's or a base de projet's tree: 1 at the top -- the number of groups above it, plus one."""
    depth, parent = 1, by_id.get(node.parent)
    while parent is not None:
        if parent.kind == "group":
            depth += 1
        parent = by_id.get(parent.parent)
    return depth


def _file_of(by_id, node):
    """The file node a node of the tree stands in -- itself where it is one, the file of an object or a heading, None for a group."""
    while node is not None and node.kind != "file":
        if node.kind == "group":
            return None
        node = by_id.get(node.parent)
    return node


def _top_only(by_id, flat, ids):
    """The nodes of `ids` in document order, a node whose ancestor is chosen as well left out -- the ancestor shows it -- and every node of a file standing for its file."""
    chosen = []
    for node in flat:
        if node.id in ids:
            chosen.append(node)
    keep = {node.id for node in chosen}
    out = []
    for node in chosen:
        parent, hidden = by_id.get(node.parent), False
        while parent is not None:
            if parent.id in keep:
                hidden = True
                break
            parent = by_id.get(parent.parent)
        if not hidden:
            out.append(node)
    return out


def _absolute(here, mode):
    """Whether document `mode` writes its headings at the level they print at (structure.is_absolute): its files are then included as they are, and a chapter is its own file."""
    if mode == "rs":
        return True
    try:
        return structure.is_absolute(structure.read(here.structure_file(mode)))
    except (validation.ValidationError, OSError):
        return False


def _offset(here, mode, by_id, file_node):
    return 0 if _absolute(here, mode) else _depth(by_id, file_node) - 1


def _group_heading(here, mode, by_id, node, files):
    """A chapter's heading as the document prints it: its own file included where the document gives it one (an absolute document), else `#heading(level: …)` with its title."""
    if mode != "rs" and _absolute(here, mode) and node.file:
        files.append(Path(here.document_dir(mode)) / node.file)
        return f"#include {_quote(from_root(here, Path(here.document_dir(mode)) / node.file))}"
    return f"#heading(level: {_depth(by_id, node)}, {_quote(structure.plain_title(node.title or '') or node.id)})"


def _include(here, mode, by_id, file_node):
    offset = _offset(here, mode, by_id, file_node)
    path = from_root(here, Path(here.document_dir(mode)) / file_node.file)
    if offset == 0:
        return f"#include {_quote(path)}"
    return f"#{{ set heading(offset: {offset}); include {_quote(path)} }}"


def _group_lines(here, mode, by_id, node, files):
    """A chapter's page: its heading, and every section under it that is printed -- a disabled section, and a disabled chapter with all it holds, left out."""
    lines = [_group_heading(here, mode, by_id, node, files)]

    def emit(children):
        for child in children:
            if not child.enabled:
                continue
            if child.kind == "group":
                lines.append(_group_heading(here, mode, by_id, child, files))
                emit(child.children)
            elif child.kind == "file":
                lines.append(_include(here, mode, by_id, child))
                files.append(Path(here.document_dir(mode)) / child.file)

    emit(node.children)
    return lines


def _object_lines(here, mode, by_id, node, files):
    """One object's page: the preamble of its file, the heading offset of its section, and its body as written. None where the object is not in the file any more -- the tree is older than the disk."""
    file_node = _file_of(by_id, node)
    if file_node is None or not file_node.file:
        return None
    path = Path(here.document_dir(mode)) / file_node.file
    try:
        text = typst_paths.read_text(path)
    except (OSError, UnicodeDecodeError):
        return None
    found = typst_objects.find(text, node.object_id)
    if found is None:
        return None
    files.append(path)
    body = found.body.replace("\r\n", "\n").replace("\r", "\n")
    return [f"#set heading(offset: {_offset(here, mode, by_id, file_node)})", preamble(text).rstrip("\n"), body]


def build(here, mode, nodes, ids, language=None):
    """The snippet of the nodes `ids` of the tree `nodes` (what `structure.tree` gives) in document `mode` of project `here`, or **None** where the whole document is meant: nothing chosen, or only what a snippet cannot isolate -- the headings an entry file carries itself.

    Several nodes are shown one after the other in document order, a node whose ancestor is chosen too being left out. A chapter shows its printed sections, a section its file, an object its body; a heading of a file that carries no tags shows its file. Raises what `structure.typst_string` and the readers raise: nothing the engineer typed reaches Typst unquoted.
    """
    ids = {i for i in (ids or ()) if i}
    if not ids:
        return None
    flat, by_id = _family(nodes)
    pieces, shown, files, kinds = [], [], [], set()
    for node in _top_only(by_id, flat, ids):
        if node.kind == "group":
            pieces.append("\n".join(_group_lines(here, mode, by_id, node, files)))
            kinds.add("group")
        elif node.kind == "object":
            lines = _object_lines(here, mode, by_id, node, files)
            if lines is None:
                continue
            pieces.append("\n".join(line for line in lines if line))
            kinds.add("object")
        else:
            file_node = _file_of(by_id, node)
            if file_node is None or not file_node.file:
                continue        # a heading of the entry file itself
            if any(file_node is by_id.get(shown_id) for shown_id in shown):
                continue
            pieces.append(_include(here, mode, by_id, file_node))
            files.append(Path(here.document_dir(mode)) / file_node.file)
            kinds.add("file")
            node = file_node
        shown.append(node.id)
    if not pieces:
        return None
    source = "\n".join(header(here, mode, language)) + "\n\n" + "\n\n".join(pieces) + "\n"
    key = hashlib.sha1((mode + "\n" + source).encode("utf-8")).hexdigest()[:12]
    kind = kinds.pop() if len(kinds) == 1 else "mixed"
    return Snippet(source, key, tuple(shown), kind, tuple(dict.fromkeys(files)))
