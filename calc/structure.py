"""The structure of a document: which sections a Convention d'utilisation or a Base de projet holds, in which order and how deep, and the block of its entry file that says so (the three document modes, CU, BP and RS).

A **CU** or **BP** document is an entry `.typ` and a folder of section files, one file per lowest-level section, each named by a stable English id -- `Sections/live-loads.typ`, no number prefix. What is *not* in the file names is the order, the nesting and whether a section is printed: those live in one **`structure.json`** beside the entry file, and the entry file's own `#include` lines are **generated from it** (`sync_entry`). A section switched off keeps its file and is simply not included. The report (RS) has no `structure.json`: its order and its enabled state stay in its own `#include` lines (calc/templates.py, `sync_includes`).

This module owns three things and no more.

**The file** -- `read`, `write`, `check_source`: `structure.json` read, checked and written back, always whole and always in one shape (fixed key order, two-space indent, written beside itself and moved into place, so NextCloud never syncs half a file and a failed write leaves the old one). The contract is schemas/structure.schema.json for what a schema walker can say, and `check_source` for the rest: an id that is not `^[a-z][a-z0-9]*(-[a-z0-9]+)*$`, two sections of one id, a tree more than four levels deep, a leaf whose file is not named after its id.

**The block** -- `sync_entry` rewrites what lies between `// woodcore:structure …` and `// woodcore:/structure` in the entry file, and **nothing else**: the title page, the language, the level, everything the engineer wrote outside the two lines is left exactly as it was, line endings included. A group at depth `d` prints its title as a heading of level `d`; a leaf at depth `d` is included with `set heading(offset: d - 1)`, so that its file writes its own heading as a plain `=` and **is independent of where it is included** -- a section moved under another group, or shared into a document that nests it differently, is not edited. A disabled section is a comment, `// disabled: <id> (<file>)`, which keeps it findable in the entry.

**Headings at the level they print at** (the engineer's request of 06.10.2026: «dans le document type, il doit y avoir deux égales … et le titre Grundlagen und Dokumente doit apparaître dans un fichier .typ dans lequel je puisse le modifier à la main ou dans Woodcore»). A structure that says `"headings": "absolute"` is laid out so: **every file writes its headings at the level they are printed at** -- a section under a chapter is `== Nutzlasten` -- and is included by a plain `#include`, no offset; and **every chapter is a file of its own too**, `Sections/<chapter id>.typ`, holding its heading (`= Grundlagen und Dokumente`, a heading object `title`) where the engineer edits it by hand or in Woodcore -- the title structure.json keeps for it in three languages is what a new chapter is written with and what stands where its file cannot be read. What depends on the depth now lies in the files, so **moving** a section or a chapter rewrites the `=` of the headings of every file it takes with it (`shift_headings`), outside the blocks a file shares with another document; a shared section keeps its title heading **outside** its shared block (`title_out_of_shared`), the two documents placing a section they share at different depths -- the live loads lie under a chapter in the convention and two deep in the base de projet. A structure that does not say so is laid out as it was, with offsets, and reads and writes as before; `make_absolute` converts one -- the window offers it, and writes nothing without the engineer's yes. The builtin templates are laid out so since v0.113.

**Tags** -- the same `// woodcore:<kind> …` comment lines mark the two other things Woodcore must find in a `.typ` to regenerate them: a parametric object (`woodcore:object <type> <id>`) and a block shared between documents (`woodcore:shared <shared-id>`), each closed by `// woodcore:/<kind> <id>`. `scan_tags`, `pair_tags` and `check_tags` read them and say what is wrong -- an unclosed tag, a closing tag that does not match, a block inside one it may not stand in, an id used twice -- so the editors that come later have one reader of the tags and this module's block is found by the very same one. A file with a tag problem is one Woodcore's editors refuse to rewrite (text-only editing); nothing here rewrites anything in it.

**The tree** -- what the «Structure document» tab shows for any of the three documents, CU, BP and RS, and the four things it does with it. **A file that carries object tags has its objects for children** -- every heading and every paragraph among them, a table, a list to tick, a choice: `Node.kind == "object"`, flat, in file order, with a short label (calc/typst_objects.py's `object_title`); `tag_section` is what puts the tags into a file that has none. `tree(here, mode)` is the document as a list of nodes in document order: for a CU or a BP from its `structure.json` and the headings of each section file, for the report from the `#include` lines of its entry file -- enabled ones and commented-out ones -- and the headings of each file they include. A node is a group, a section file or a heading, carries the absolute level it is printed at (the offsets the structure block applies are applied) and says whether it is printed, whether it opens a `.typ` file of its own and which other documents share it. `set_enabled` switches a section on or off where the document keeps that (`structure.json` and the entry's block for a CU or a BP, the `#include` line for the report, which is commented out and uncommented and nothing else); `set_title` rewrites the title where it lives (the first heading of the file, or a group's title in `structure.json`); `align` maps the nodes to the bookmarks of the compiled PDF so that a click in the tree can scroll the page, and `bookmarks_from_pdf` reads those bookmarks. **Headings are found by the lexer of calc/typst_paths.py** -- the one scanner of Typst this project has -- so a `=` in a comment, a raw block, a string or a formula is no heading and one after an `#import` line, in a content block or after a line break is.

**The catalogue's operations** -- what the sections tab does to a document's list of sections: `add_section`, `add_group`, `remove_section`, `move_node`, `rename_section` (and `suggest_id`, which proposes an id). Each validates everything before it writes anything, writes structure.json, the section files and the entry file together -- each beside itself and moved into place, and **put back if a later one fails** -- keeps the line endings of the files it rewrites, and returns an `Edit` saying what changed. A section removed is **never deleted**: its file is moved into `<document>/Sections/archives/<yymmdd-hhmmss>-<id>.typ`. Every refusal is a `StructureError` with a `code` (CODES) and an English sentence. A CU or a BP is worked on through structure.json and the entry's block; **the report (RS) is worked on through its `#include` lines** -- sections added, moved, removed (its line commented, its file archived) and renamed, but not nested and not grouped, which it has no way to say.

There is no Qt in this file.
"""

import bisect
import datetime
import io
import json
import os
import re
import time
from collections import namedtuple
from dataclasses import dataclass, field
from pathlib import Path

import typst_paths
import validation
from structure_tags import (  # split out of this module (issue #30): every name it had is still importable from it
    ALLOWED_INSIDE,
    Block,
    Bookmark,
    CALL,
    Heading,
    ID_PATTERN,
    KINDS,
    OBJECT_TYPES,
    Problem,
    Tag,
    _COMMENT,
    _EMPHASIS,
    _HeadingLexer,
    _LABEL,
    _NAMED,
    _NUMBERING,
    _TAG_LINE,
    _TYPOGRAPHY,
    _a,
    _arguments,
    _block_end,
    _bookmark,
    _call_end,
    _skip_content,
    _skip_string,
    _split,
    _strip,
    align,
    bookmarks_from_pdf,
    check_tags,
    flatten,
    normalize_title,
    pair_tags,
    plain_title,
    scan_headings,
    scan_tags,
    walk,
)
from structure_source import (  # split out of this module (issue #30): every name it had is still importable from it
    ABSOLUTE,
    FILE,
    FORMAT,
    LANGUAGES,
    MAX_DEPTH,
    MODES,
    NODE_KEYS,
    SCHEMA_VERSION,
    SECTIONS_DIR,
    SHARE_MODES,
    StructureError,
    TOP_KEYS,
    _fail,
    blank,
    check_source,
    dumps,
    find,
    group_file,
    is_absolute,
    leaves,
    named_files,
    ordered,
    read,
    section_file,
    title_of,
)
from structure_nodes import (  # split out of this module (issue #30): every name it had is still importable from it
    Include,
    Node,
    _file_node,
    _fill_shared,
    _group_title,
    _include_lines,
    _nest,
    _object_nodes,
    _read_section,
    _shared_index,
    _tree_report,
    _tree_structured,
    document_language,
    find_node,
    tree,
)


# The id of the heading object a chapter's file holds, and a section's first heading in the templates.
TITLE_ID = "title"


def _refuse(code, message, **values):
    """A StructureError that states its code: what the operations on the catalogue raise, so that a window can say it in its own words."""
    raise StructureError(message, code, **values)


def _replace(source, target):
    """`os.replace`, tried again a few times on the PermissionError the sync client of NextCloud gives while it holds a file it has just seen written."""
    for attempt in range(6):
        try:
            return os.replace(source, target)
        except PermissionError:
            if attempt == 5:
                raise
            time.sleep(0.1 * (attempt + 1))


# --- the file ------------------------------------------------------------------------------


def write(path, source):
    """The structure written back, checked first -- the one writer of structure.json. Always whole, always ordered, and written beside itself and moved into place: a failed write leaves the old file as it was. LF, whatever the platform, so a structure is the same bytes on every machine that syncs the project."""
    path = Path(path)
    check_source(source, path.name)
    text = dumps(source)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with open(temporary, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    _replace(temporary, path)
    return path


# --- the generated block -------------------------------------------------------------------

START_TAG = "// woodcore:structure -- written by Woodcore from structure.json; what lies between these two lines is replaced"
END_TAG = "// woodcore:/structure"


def typst_string(text):
    """`text` as a Typst string literal, with the three escapes the canonical call grammar of a parametric object knows: backslash, double quote and newline."""
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def block_lines(source, language):
    """The lines of the generated block, between the two tags and without them, for a document written in `language`.

    A group at depth `d` is `#heading(level: d, "<title>")`; a leaf at depth `d` is `#{ set heading(offset: d - 1); include "Sections/<id>.typ" }`, and a plain `#include` at depth 1, where the offset would be 0. A disabled section -- or one under a disabled group, which takes its subtree out with it -- is `// disabled: <id> (<file>)`, a group's line carrying no file.

    **In an absolute document** (`is_absolute`) every line is a plain `#include`: a group's of its own file, `Sections/<group id>.typ`, which holds its heading at its level, and a leaf's of its file, whose headings are written at the level they print at.
    """
    if language not in LANGUAGES:
        _refuse("bad_language", f"language {language!r} -- expected one of {', '.join(LANGUAGES)}", language=language)
    lines = []
    absolute = is_absolute(source)

    def emit(nodes, depth, off):
        for node in nodes:
            node_off = off or not node.get("enabled", True)
            if "children" in node:
                if node_off:
                    lines.append(f"// disabled: {node['id']}" + (f" ({group_file(node['id'])})" if absolute else ""))
                elif absolute:
                    lines.append(f"#include {typst_string(group_file(node['id']))}")
                else:
                    lines.append(f"#heading(level: {depth}, {typst_string(title_of(node, language))})")
                emit(node["children"], depth + 1, node_off)
            elif node_off:
                lines.append(f"// disabled: {node['id']} ({node['file']})")
            elif depth == 1 or absolute:
                lines.append(f"#include {typst_string(node['file'])}")
            else:
                lines.append(f"#{{ set heading(offset: {depth - 1}); include {typst_string(node['file'])} }}")

    emit(source["sections"], 1, False)
    return lines


def block_text(source, language, newline="\n"):
    """The whole block, tags included, ready to be put in an entry file that has none yet -- what a template's entry file carries."""
    return newline.join([START_TAG, *block_lines(source, language), END_TAG]) + newline


def _source_of(structure):
    """`structure` as a checked dict: given as one, or as the path of a structure.json."""
    if isinstance(structure, (str, Path)):
        return read(structure)
    return check_source(structure)


def _entry_text(name, text, new_lines):
    """The text of the entry file `name` with the lines between its two structure tags replaced by `new_lines`, or None where that is what it holds already -- the whole of `sync_entry` but the reading and the writing, so that the operations on the catalogue can say whether an entry can be laid out, and what it would become, before they write anything. Refuses, with the code `entry_unreadable`, a file whose tags cannot be read or that has no block."""
    blocks, problems = pair_tags(text)
    if problems:
        _refuse("entry_unreadable", f"{name}: Woodcore cannot read the tags of this file, so it does not rewrite it -- " + "; ".join(str(p) for p in problems), file=name)
    found = [b for b in blocks if b.kind == "structure"]
    if not found:
        _refuse("entry_unreadable", f"{name}: has no `{START_TAG.split(' --')[0]}` … `{END_TAG}` pair to write the structure between", file=name)
    block = found[0]
    lines = _split(text)
    start_line = lines[block.start]
    ending = start_line[len(_strip(start_line)):] or "\n"
    before = "".join(lines[:block.start + 1])
    old = "".join(lines[block.start + 1:block.end])
    after = "".join(lines[block.end:])
    new = "".join(line + ending for line in new_lines)
    if new == old:
        return None
    return before + new + after


def sync_entry(entry_file, structure, language):
    """Rewrites the structure block of `entry_file` from `structure` (a checked dict, or the path of a structure.json) for a document written in `language`. Returns whether the file changed.

    **Only the lines between the two tags are replaced.** Everything outside them -- the title page, the language and level settings, a comment of the engineer's -- is left as it is, and so are the two tag lines themselves and the file's line endings: the lines written take the ending the start tag's own line has, so a file saved with CRLF stays CRLF and one saved with LF stays LF. A second call with the same structure writes nothing.

    The file must carry exactly one `// woodcore:structure` … `// woodcore:/structure` pair and no tag problem anywhere (`pair_tags`): a file whose tags Woodcore cannot read is one it does not rewrite, and the error says where.
    """
    source = _source_of(structure)
    new_lines = block_lines(source, language)
    path = Path(entry_file)
    with open(path, encoding="utf-8", newline="") as handle:
        text = handle.read()
    new_text = _entry_text(path.name, text, new_lines)
    if new_text is None:
        return False
    temporary = path.with_name(path.name + ".tmp")
    with open(temporary, "w", encoding="utf-8", newline="") as handle:
        handle.write(new_text)
    _replace(temporary, path)
    return True


# --- the tags ------------------------------------------------------------------------------


# --- the headings of a file ----------------------------------------------------------------


# --- the tree ------------------------------------------------------------------------------

NODE_KINDS = ("group", "file", "heading", "object")


# --- switching a section on and off, and naming it -----------------------------------------

def set_enabled(here, mode, node_id, enabled, language=None):
    """Section `node_id` of document `mode` switched on or off. Returns whether anything was written.

    A **CU or a BP** keeps the flag in structure.json, and the entry file's block is written from it (`sync_entry`): a disabled section keeps its file and is a `// disabled:` comment in the entry, a disabled group takes its subtree with it. The entry is written first, so a structure whose entry cannot be rewritten -- tags Woodcore cannot read, no block -- is refused with structure.json as it was. The **report** keeps its sections in its `#include` lines, and a section switched off is that line commented out, `// #include "Sections/…"`, and switched on again the same line without the comment: nothing else of the entry file moves, its line endings included, and the order stays where it was. `node_id` is the node's id; a heading inside a file is not a section and has no state of its own.
    """
    enabled = bool(enabled)
    if mode == "rs":
        return _set_enabled_report(here, node_id, enabled)
    if mode not in MODES:
        raise StructureError(f"document {mode!r} -- expected one of {', '.join(SHARE_MODES)}")
    path = here.structure_file(mode)
    source = read(path)
    found = find(source, node_id)
    if found is None:
        raise StructureError(f"{path.name}: has no section {node_id!r} -- a heading inside a section file is not a section and has no state of its own")
    node = found[0]
    flag_changed = bool(node.get("enabled", True)) != enabled
    node["enabled"] = enabled
    entry_changed = sync_entry(here.document_typ(mode), source, language or document_language(here, mode))
    if flag_changed:
        write(path, source)
    return flag_changed or entry_changed


def _set_enabled_report(here, node_id, enabled):
    entry = here.document_typ("rs")
    text = typst_paths.read_text(entry)
    include = next((i for i in _include_lines(text) if i.id == node_id), None)
    if include is None:
        known = ", ".join(i.id for i in _include_lines(text)) or "none"
        raise StructureError(f"{entry.name}: has no `#include \"Sections/…\"` line for {node_id!r} -- the report's sections are {known}")
    if include.enabled == enabled:
        return False
    import templates
    lines = _split(text)
    line = lines[include.line]
    prefix = templates._INCLUDE.match(_strip(line)).group(1)
    indent = re.match(r"[ \t]*", prefix).group(0)
    lines[include.line] = indent + ("" if enabled else "// ") + line[len(prefix):]
    typst_paths.write_text(entry, "".join(lines))
    return True


def tag_file(text, ids="slug"):
    """`text` with its untagged headings and paragraphs wrapped in object tags -- calc/typst_objects.py's `tag_file`, here for the callers that hold the tree. Refused (typst_objects.ObjectError `tags`) where the file's tags cannot be read."""
    import typst_objects
    return typst_objects.tag_file(text, ids=ids)


def tag_section(here, mode, node_id, ids="slug"):
    """The file of node `node_id` of document `mode` tagged: every untagged top-level heading and paragraph of it wrapped in object tags (`typst_objects.tag_file`), what «Baliser ce fichier» does. `node_id` is a section file's id or the id of anything inside it -- a heading, an object --; a group has no file. Returns the number of objects the file gained, **0 and nothing written** where there was nothing to tag -- a second run, a file that is tagged already.

    The tags are comments, so the document compiles and prints as it did; the file's line endings, its BOM and every byte outside the inserted tag lines are kept. Refused, with the codes of CODES: a document that is none or that the project has not (`bad_mode`, `no_such_document`), a node that is not there (`no_such_node`) or is a group (`not_a_section`), a file whose tags cannot be read -- it is not rewritten, and the error names the line (`tags_unreadable`).
    """
    import typst_objects
    _check_mode(here, mode, None)
    node = find_node(tree(here, mode), node_id) if isinstance(node_id, str) else None
    if node is None:
        _refuse("no_such_node", f"document {mode}: has no section, heading or object {node_id!r}", id=node_id)
    if node.file is None:
        _refuse("not_a_section", f"{node_id!r} is a group of the structure, which has no file to tag", id=node_id)
    path = here.document_dir(mode) / node.file
    text = typst_paths.read_text(path)
    try:
        new = typst_objects.tag_file(text, ids=ids)
    except typst_objects.ObjectError as exc:
        if exc.code != "tags":
            raise
        _refuse("tags_unreadable", f"{node.file}: {exc}", file=node.file)
    if new == text:
        return 0
    typst_paths.write_text(path, new)
    return len(typst_objects.objects(new)) - len(typst_objects.objects(text))


def _clean_title(title):
    if not isinstance(title, str) or not title.strip():
        _refuse("bad_title", "a title cannot be empty")
    if any(ord(ch) < 32 for ch in title):
        _refuse("bad_title", "a title holds a line break or another control character")
    return title.strip()


def set_title(here, mode, node_id, language, title):
    """The title of node `node_id` of document `mode` rewritten. Returns whether anything was written.

    A **group** (a CU or a BP) has its title in structure.json, one per language: `title[language]` is replaced and the entry's block is written again. A **section file** and a **heading** have theirs in the file, in the one language the file is written in: the heading's line is rewritten textually -- its `=` marker, a trailing label and comment, the line ending and every other byte of the file left as they were, and for a `#heading("…")` call the string or the content block between the brackets -- and `language` is not used. A file with no heading has no title to rewrite, and a heading whose title is not plain text (a variable) is refused rather than guessed at.
    """
    title = _clean_title(title)
    if mode in MODES:
        path = here.structure_file(mode)
        source = read(path)
        found = find(source, node_id)
        if found is not None and "children" in found[0]:
            if language not in LANGUAGES:
                raise StructureError(f"language {language!r} -- expected one of {', '.join(LANGUAGES)}")
            group = found[0]
            changed = False
            if is_absolute(source) and language == document_language(here, mode):
                changed = _set_file_title(here.document_dir(mode) / group_file(node_id), title)
            if group["title"][language] == title:
                return changed
            group["title"][language] = title
            sync_entry(here.document_typ(mode), source, document_language(here, mode))
            write(path, source)
            return True
    node = find_node(tree(here, mode), node_id)
    if node is None:
        raise StructureError(f"document {mode}: has no section or heading {node_id!r}")
    if node.kind == "object" and node.object_type != "heading":
        raise StructureError(f"{node.file}: {node.id!r} is {'an' if node.object_type[:1] in 'aeiou' else 'a'} {node.object_type}, which has no title to rewrite")
    if node.line is None:
        raise StructureError(f"{node.file}: has no heading to carry a title -- write one first")
    path = here.document_dir(mode) / node.file
    text = typst_paths.read_text(path)
    heading = next((h for h in scan_headings(text) if h.line == node.line), None)
    if heading is None:
        raise StructureError(f"{node.file}: line {node.line + 1} is no longer a heading -- the tree is out of date")
    if heading.span is None:
        raise StructureError(f"{node.file}, line {node.line + 1}: the title is not plain text Woodcore can rewrite ({heading.title!r})")
    start, end = heading.span
    if heading.form == "call" and text[start - 1:start] == '"':
        written = typst_paths._escape(title)
    else:
        if heading.form == "call" and title.count("[") != title.count("]"):
            raise StructureError("a title in a content block cannot hold a bracket that is not closed")
        written = title
    new_text = text[:start] + written + text[end:]
    if new_text == text:
        return False
    typst_paths.write_text(path, new_text)
    return True


def _set_file_title(path, title):
    """The first heading of the file at `path` given `title`, its `=` and every other byte kept. False where it says that already, or holds no heading Woodcore can rewrite."""
    try:
        text = typst_paths.read_text(path)
    except (OSError, UnicodeDecodeError):
        return False
    headings = scan_headings(text)
    if not headings or headings[0].span is None:
        return False
    start, end = headings[0].span
    written = typst_paths._escape(title) if headings[0].form == "call" and text[start - 1:start] == '"' else title
    new_text = text[:start] + written + text[end:]
    if new_text == text:
        return False
    typst_paths.write_text(path, new_text)
    return True


# --- headings at the level they print at -------------------------------------------------------------------

def _shared_lines(text):
    """The lines of `text` (0-based) that lie inside a block shared with another document, its two tags included."""
    inside = set()
    for block in pair_tags(text)[0]:
        if block.kind == "shared":
            inside.update(range(block.start, block.end + 1))
    return inside


def shift_headings(text, delta, minimum=1):
    """`text` with every heading written `= …` given `delta` more `=` -- fewer where it is negative, never fewer than `minimum` -- **outside the blocks it shares** with another document, which must stay the same bytes in every copy. A `#heading(level: n, …)` call keeps what it says. Every other byte is kept, line endings included. What a section or a chapter takes with it when it moves to another depth in an absolute document."""
    if not delta:
        return text
    shared = _shared_lines(text) if "woodcore:shared" in text else set()
    lines = _split(text)
    for heading in scan_headings(text):
        if heading.form != "markup" or heading.line in shared:
            continue
        line = lines[heading.line]
        body = line.lstrip(" \t")
        indent = line[:len(line) - len(body)]
        marks = len(body) - len(body.lstrip("="))
        if marks != heading.level:
            continue
        lines[heading.line] = indent + "=" * max(minimum, marks + delta) + body[marks:]
    return "".join(lines)


def title_out_of_shared(text):
    """`text` with the opening tag of a shared block moved to just after the heading object it opens with, where it opens with one -- `// woodcore:shared live-loads` then `// woodcore:object heading title` -- so that the title of a shared section is the document's own: written at the level the section prints at there, which two documents placing it at different depths could not share. Nothing else moves; a text with no such block comes back as it is."""
    if "woodcore:shared" not in text:
        return text
    import typst_objects
    objects = typst_objects.objects(text)
    lines = _split(text)
    for block in [b for b in pair_tags(text)[0] if b.kind == "shared"]:
        following = next((k for k in range(block.start + 1, block.end) if lines[k].strip()), None)
        if following is None:
            continue
        inside = [o for o in objects if block.start < o.start and o.end < block.end]
        if inside and inside[0].type == "heading" and inside[0].start == following:
            last = inside[0].end              # a heading object: moved out with its two tags
        elif re.match(r"^=+\s", lines[following]) and not any(o.start <= following <= o.end for o in objects):
            last = following                  # a heading written as markup, untagged: the line alone
        else:
            continue                          # something else opens the block: left as it is
        tag = lines[block.start]
        moved = lines[:block.start] + lines[block.start + 1:last + 1] + [tag] + lines[last + 1:]
        return title_out_of_shared("".join(moved))
    return text


def _group_text(here_or_import, title, level, newline):
    """A chapter's file in an absolute document: the import every section starts with, a blank line, and its heading as a heading object `title`, at its level."""
    return newline.join([here_or_import, "", f"// woodcore:object heading {TITLE_ID}", f"{'=' * level} {title}", f"// woodcore:/object {TITLE_ID}", ""]) + newline


def make_absolute_folder(folder, language, import_line='#import "/commands.typ": *'):
    """The document in `folder` -- its structure.json, its section files and its entry file -- laid out with its headings at the level they print at (see the module's docstring): every section file's headings shifted by its depth less one, outside its shared blocks, its title taken out of a shared block where one opens with it (`title_out_of_shared`); a file written for every chapter, its heading the chapter's title in `language` at its depth; structure.json saying `"headings": "absolute"`, and the entry's block written again. Returns the files written. A document laid out so already is left as it is. What the templates and `make_absolute` are converted with; nothing is checked against another document here."""
    folder = Path(folder)
    path = folder / FILE
    source = read(path)
    if is_absolute(source):
        return []
    written = []
    entry = next((f for f in folder.glob("*.typ")), None)
    newline = "\n"
    if entry is not None:
        newline = _newline(typst_paths.read_text(entry))
    for node, depth, _parent in walk(source):
        if "children" in node:
            target = folder / group_file(node["id"])
            if target.exists():
                _refuse("file_exists", f"{group_file(node['id'])}: is there already -- a chapter's file never overwrites one", file=group_file(node["id"]))
            target.parent.mkdir(parents=True, exist_ok=True)
            typst_paths.write_text(target, _group_text(import_line, title_of(node, language), depth, newline))
            written.append(target)
            continue
        file = folder / node["file"]
        if not file.is_file():
            continue
        text = typst_paths.read_text(file)
        new_text = shift_headings(title_out_of_shared(text), depth - 1)
        if new_text != text:
            typst_paths.write_text(file, new_text)
            written.append(file)
    source["headings"] = ABSOLUTE
    write(path, source)
    written.append(path)
    if entry is not None and sync_entry(entry, source, language):
        written.append(entry)
    return written


def make_absolute(here, language=None):
    """Every document of project `here` that has a structure.json laid out with its headings at the level they print at (`make_absolute_folder`), **the two together**: a section they share comes out the same in both, its title moved out of the shared block in each. A report's file that carries the same shared block has its title moved out likewise, and keeps its levels -- the report's files always wrote theirs. Returns the files written."""
    written = []
    shared_ids = set()
    for mode in MODES:
        if mode not in here.modes:
            continue
        written += make_absolute_folder(here.document_dir(mode), language or document_language(here, mode), _import_line(here))
    for mode in MODES:
        if mode in here.modes:
            for path in (here.document_dir(mode) / SECTIONS_DIR).glob("*.typ"):
                shared_ids.update(_shared_ids_in(path))
    if "rs" in here.modes and shared_ids:
        for path in (here.document_dir("rs") / SECTIONS_DIR).glob("*.typ"):
            if not shared_ids.intersection(_shared_ids_in(path)):
                continue
            text = typst_paths.read_text(path)
            new_text = title_out_of_shared(text)
            if new_text != text:
                typst_paths.write_text(path, new_text)
                written.append(path)
    return written


def _import_line(here):
    import documents
    return documents.import_line(here)


def fit_text(text, level):
    """`text` -- a section file's -- with its first heading outside its shared blocks of level `level`, every heading after it shifted with it (`shift_headings`): what a section placed at a depth of a document is given -- a share, an import. The text as it is where it has no such heading."""
    shared = _shared_lines(text) if "woodcore:shared" in text else set()
    first = next((h for h in scan_headings(text) if h.form == "markup" and h.line not in shared), None)
    return text if first is None else shift_headings(text, level - first.level)


def fit_file(path, depth):
    """The file at `path` written so that its first heading -- outside its shared blocks -- is of level `depth` (`fit_text`). Returns whether it was written."""
    try:
        text = typst_paths.read_text(path)
    except (OSError, UnicodeDecodeError):
        return False
    new_text = fit_text(text, depth)
    if new_text == text:
        return False
    typst_paths.write_text(path, new_text)
    return True


# --- the catalogue: adding, removing, moving and renaming sections -------------------------------------------

ARCHIVES_DIR = "archives"

# Why an operation on the catalogue refuses, one code each, so that a window can say it in its own words (StructureError.code; `values` names what the refusal is about).
CODES = (
    "bad_mode",           # a document that is none of cu, bp, rs
    "no_such_document",   # a project that has no such document: a report laid out alone has no cu and no bp
    "bad_language",       # a language that is none of fr, de, en (`language`)
    "bad_id",             # an id that is not an id: for cu and bp English, lower case, hyphen-separated; for the report a safe file name
    "id_exists",          # the id of another section already (`id`)
    "file_exists",        # a file lies where the section's would (`file`): nothing is ever overwritten
    "bad_title",          # a title that is empty or holds a line break
    "titles_missing",     # a group's title is stated in all three languages (`missing`)
    "no_such_node",       # no section of that id (`id`)
    "not_a_section",      # a heading inside a section file (`a#2`) is not a section
    "not_a_group",        # a section that is a file cannot hold others (`id`)
    "too_deep",           # a tree goes four levels deep (`depth`, `max`)
    "bad_position",       # a place among the siblings that does not exist (`position`, `count`)
    "group_not_empty",    # a group is removed once it is empty (`count`)
    "cycle",              # a group cannot be moved into itself
    "same_id",            # a section renamed what it is called already
    "shared",             # a shared section keeps its id (`shared_with`, `shared_ids`)
    "rs_no_groups",       # the report has no groups: it keeps its sections in its #include lines
    "rs_no_nesting",      # nor any nesting: its sections stand one after the other
    "entry_unreadable",   # an entry file whose tags Woodcore cannot read, that has no block, or that cannot be read (`file`)
    "tags_unreadable",    # a section file whose tags Woodcore cannot read is not tagged (`file`)
    "write_failed",       # the disk refused: what was written has been put back (`error`)
)

# A report's section file stem -- `001-einleitung`, `008-brandschutz`: what `Sections/<stem>.typ` is called. No `#`, which the tree keeps for a file included twice.
_STEM = re.compile(r"^[0-9A-Za-z][0-9A-Za-z_-]*$")


@dataclass
class Edit:
    """What an operation on the catalogue changed -- the window refreshes from it, and a test compares it.

    `op` -- the operation (`add_section`, `add_group`, `remove_section`, `move_node`, `rename_section`), `mode` the document, `id` the section's id -- after a rename, the new one. `structure` -- structure.json was rewritten (a CU or a BP). `entry` -- the entry file was rewritten: its generated block, or the report's `#include` lines. `created` -- section files written new. `archived` -- section files moved into `Sections/archives/`, as their destination. `renamed` -- (old path, new path) of the section files renamed. Nothing changed at all -- a section moved to where it stands -- is an Edit that says so (`changed` is False) and writes nothing."""
    op: str
    mode: str
    id: str
    structure: bool = False
    entry: bool = False
    created: tuple = ()
    archived: tuple = ()
    renamed: tuple = ()

    @property
    def changed(self):
        return bool(self.structure or self.entry or self.created or self.archived or self.renamed)

    def as_dict(self):
        """Plain values, paths as strings: what a log prints."""
        return {"op": self.op, "mode": self.mode, "id": self.id, "structure": self.structure, "entry": self.entry,
                "created": [str(p) for p in self.created], "archived": [str(p) for p in self.archived],
                "renamed": [[str(a), str(b)] for a, b in self.renamed]}


def _stamp():
    """The `yymmdd-hhmmss` an archived file is named after."""
    return datetime.datetime.now().strftime("%y%m%d-%H%M%S")


def _archive_target(folder, name):
    """Where the section file called `name` (an id, or a report's file stem) goes when it is removed: `<document>/Sections/archives/<yymmdd-hhmmss>-<name>.typ`, and `-2`, `-3` … after the name where that one is taken -- two sections removed in one second."""
    archives = Path(folder) / SECTIONS_DIR / ARCHIVES_DIR
    stamp = _stamp()
    target = archives / f"{stamp}-{name}.typ"
    number = 2
    while target.exists():
        target = archives / f"{stamp}-{name}-{number}.typ"
        number += 1
    return target


def _newline(text):
    """The line ending the text of an entry file uses -- what a new section file is written in, so that a project saved with CRLF stays CRLF."""
    return "\r\n" if "\r\n" in text else "\n"


def _skeleton(here, title, newline, level=1, tagged=False):
    """A new section file: the import every section starts with, a blank line, the heading -- at `level`, the depth it lies at in an absolute document, and between the tags of a heading object `title` where `tagged`, every heading of such a document being an object --, a blank line -- as bytes, in `newline`."""
    import documents
    heading = f"{'=' * level} {title}"
    lines = [f"// woodcore:object heading {TITLE_ID}", heading, f"// woodcore:/object {TITLE_ID}"] if tagged else [heading]
    return (newline.join([documents.import_line(here), "", *lines, ""]) + newline).encode("utf-8")


def _read_entry(entry):
    try:
        return typst_paths.read_text(entry)
    except (OSError, UnicodeDecodeError) as exc:
        _refuse("entry_unreadable", f"{Path(entry).name}: could not be read -- {exc}", file=Path(entry).name)


# --- writing, and putting back what was written -----------------------------------------------

def _put(path, data):
    """`data` (bytes) written beside `path` and moved into place: a failed write leaves the old file, and nothing is left beside it."""
    path = Path(path)
    temporary = path.with_name(path.name + ".tmp")
    try:
        temporary.write_bytes(data)
        _replace(temporary, path)
    finally:
        try:
            temporary.unlink()
        except OSError:
            pass


def _step_create(path, data):
    def do():
        if path.exists():
            _refuse("file_exists", f"{path.name}: is there already -- a section never overwrites a file", file=path.name)
        path.parent.mkdir(parents=True, exist_ok=True)
        _put(path, data)

    def undo():
        try:
            path.unlink()
        except FileNotFoundError:
            pass
    return do, undo


def _step_put(path, new_text, old_text):
    return (lambda: _put(path, new_text.encode("utf-8"))), (lambda: _put(path, old_text.encode("utf-8")))


def _step_structure(path, source, raw):
    return (lambda: write(path, source)), (lambda: _put(path, raw))


def _step_move(source, target):
    def do():
        if target.exists():
            _refuse("file_exists", f"{target.name}: is there already -- a section never overwrites a file", file=target.name)
        target.parent.mkdir(parents=True, exist_ok=True)
        _replace(source, target)

    return do, (lambda: _replace(target, source))


def _run(steps):
    """The steps (do, undo) done in order. One that fails puts back, in the opposite order, every one already done, and the failure is said: the disk's as a `write_failed`, a StructureError's as it is."""
    done = []
    try:
        for do, undo in steps:
            do()
            done.append(undo)
    except Exception as exc:
        for undo in reversed(done):
            try:
                undo()
            except Exception:  # broad: an undo that fails must not hide the error being raised, which follows
                pass
        if isinstance(exc, OSError):
            where = Path(exc.filename).name if getattr(exc, "filename", None) else "a file"
            _refuse("write_failed", f"{where}: could not be written ({exc.strerror or exc}) -- what had been written was put back", error=str(exc))
        raise


# --- reading what an operation works on --------------------------------------------------------

@dataclass
class _Open:
    """A CU or a BP as an operation finds it: its structure (checked, and as bytes, to be put back), its entry file's text and the language its group titles are printed in."""
    here: object
    mode: str
    language: str
    path: Path
    source: dict
    raw: bytes
    before: str
    entry: Path
    text: str
    folder: Path


def _check_mode(here, mode, language):
    if mode not in SHARE_MODES:
        _refuse("bad_mode", f"document {mode!r} -- expected one of {', '.join(SHARE_MODES)}", mode=mode)
    if mode not in here.modes:
        _refuse("no_such_document", f"this project has no {mode} document -- it is laid out as a report alone, and migration gives it the three", mode=mode)
    if language is not None and language not in LANGUAGES:
        _refuse("bad_language", f"language {language!r} -- expected one of {', '.join(LANGUAGES)}", language=language)


def _open(here, mode, language):
    _check_mode(here, mode, language)
    path = here.structure_file(mode)
    source = read(path)
    entry = here.document_typ(mode)
    return _Open(here, mode, language or document_language(here, mode), path, source, path.read_bytes(), dumps(source),
                 entry, _read_entry(entry), here.document_dir(mode))


def _check_id(section_id):
    if not isinstance(section_id, str) or not ID_PATTERN.match(section_id):
        _refuse("bad_id", f"id {section_id!r} is not an id -- English, lower case, letters and digits parted by single hyphens, starting with a letter (live-loads)", id=section_id)


def _check_stem(stem):
    if not isinstance(stem, str) or not _STEM.match(stem):
        _refuse("bad_id", f"{stem!r} is not a section's file name -- letters, digits, `-` and `_`, starting with a letter or a digit (008-brandschutz)", id=stem)


def _check_free(ctx, section_id):
    found = find(ctx.source, section_id)
    if found is not None:
        _refuse("id_exists", f"id {section_id!r} is the id of another section already -- an id is unique in its document", id=section_id)
    if (ctx.folder / section_file(section_id)).exists():
        _refuse("file_exists", f"{section_file(section_id)}: is there already -- a section never overwrites a file", file=section_file(section_id))


def _node(source, node_id):
    found = find(source, node_id) if isinstance(node_id, str) else None
    if found is None:
        if isinstance(node_id, str) and ("#" in node_id or "/" in node_id):
            _refuse("not_a_section", f"{node_id!r} is a heading or an object inside a section file, not a section -- a section is a file or a group", id=node_id)
        known = ", ".join(node["id"] for node, _d, _p in walk(source)) or "none"
        _refuse("no_such_node", f"{FILE}: has no section {node_id!r} -- the sections are {known}", id=node_id)
    return found


def _parent(source, parent_id):
    """(the group, the depth a child of it lies at); (None, 1) for the top."""
    if parent_id is None:
        return None, 1
    node, depth, _parent_of = _node(source, parent_id)
    if "children" not in node:
        _refuse("not_a_group", f"{parent_id!r} is a section file -- only a group holds other sections", id=parent_id)
    return node, depth + 1


def _siblings(source, parent):
    return source["sections"] if parent is None else parent["children"]


def _position(position, count):
    """A place among `count` siblings: 0 before the first … `count` after the last, None the end."""
    if position is None:
        return count
    if isinstance(position, bool) or not isinstance(position, int) or not 0 <= position <= count:
        _refuse("bad_position", f"position {position!r} -- among {count} section(s) a section goes at 0 to {count}, or None for the end", position=position, count=count)
    return position


def _height(node):
    """How many levels a node's subtree takes: 1 for a leaf and an empty group."""
    return 1 + max((_height(child) for child in node.get("children", ())), default=0)


def _shared_ids_in(path):
    """The shared ids the section file at `path` carries (opening tags), () for a file that is not there or cannot be read."""
    try:
        text = typst_paths.read_text(path)
    except (OSError, UnicodeDecodeError):
        return ()
    if "woodcore:shared" not in text:
        return ()
    return tuple(dict.fromkeys(t.id for t in scan_tags(text)[0] if t.kind == "shared" and not t.closing))


def _commit(ctx, op, node_id, new_source, creates=(), archive=None, rename=None, puts=()):
    """`new_source` checked, the entry file's block worked out from it, and everything written or put back together -- section files created, then the entry, then structure.json, then the files moved (a file archived or renamed, the least reversible, last). Nothing is written until everything is known to be writable: the structure is checked and the entry's tags read first, so a refusal leaves every file as it was."""
    check_source(new_source, ctx.path.name)
    new_entry = _entry_text(ctx.entry.name, ctx.text, block_lines(new_source, ctx.language))
    structure_changed = dumps(new_source) != ctx.before
    steps = [_step_create(path, data) for path, data in creates]
    steps += [_step_put(path, new_text, old_text) for path, new_text, old_text in puts]
    if new_entry is not None:
        steps.append(_step_put(ctx.entry, new_entry, ctx.text))
    if structure_changed:
        steps.append(_step_structure(ctx.path, new_source, ctx.raw))
    if archive is not None:
        steps.append(_step_move(*archive))
    if rename is not None:
        steps.append(_step_move(*rename))
    _run(steps)
    return Edit(op, ctx.mode, node_id, structure_changed or bool(puts), new_entry is not None, tuple(path for path, _data in creates),
                (archive[1],) if archive else (), (rename,) if rename else ())


# --- the operations -----------------------------------------------------------------------------

def add_section(here, mode, parent_id, position, section_id, title, language=None):
    """A new section -- a file of its own -- in document `mode`, under the group `parent_id` (None for the top) at `position` among its siblings (0 first … the number of siblings last, None the end). Returns an `Edit`.

    For a **CU or a BP** the file is `Sections/<section_id>.typ`, written from the skeleton every section starts with (`#import "/commands.typ": *`, a blank line, `= <title>`, a blank line), in the line ending the document's entry file has; the section is added to structure.json, **enabled**, and the entry's block is written again. `language` is the language the entry's group titles are printed in (`document_language` where None). Refused, with the codes of CODES: an id that is not an id (`bad_id`) or belongs to another section (`id_exists`), a file already lying there (`file_exists` -- nothing is overwritten), a title that is empty (`bad_title`), a parent that is not there (`no_such_node`) or is a file (`not_a_group`), a place that does not exist (`bad_position`), a tree more than four levels deep (`too_deep`), an entry file whose tags cannot be read (`entry_unreadable`). Nothing is written until all of it is known to hold; a write that fails puts back what was written (`write_failed`).

    In the **report** (mode `rs`) a section is a file `Sections/<section_id>.typ` and a line `#include "Sections/<section_id>.typ"` of the entry file, and **`section_id` is the file's stem** -- `008-brandschutz`, with its number, as the report's sections are named (`suggest_id` proposes one). The report has no nesting: `parent_id` must be None (`rs_no_nesting`), and `position` counts the `#include` lines, commented-out ones included -- not the headings the entry file may hold itself. The new line takes its place by the rule of `templates.sync_includes`: the include lines stay where they stand in the entry file and each holds the next section in order, a section switched off staying switched off, so what is between two lines -- a heading, a page break -- stays where it is. The heading `title` is written as it is, markup and all.
    """
    if mode == "rs":
        return _rs_add(here, parent_id, position, section_id, title)
    ctx = _open(here, mode, language)
    title = _clean_title(title)
    _check_id(section_id)
    source = ctx.source
    _check_free(ctx, section_id)
    parent, depth = _parent(source, parent_id)
    if depth > MAX_DEPTH:
        _refuse("too_deep", f"a section under {parent_id!r} would lie {depth} levels deep -- a document's structure goes down {MAX_DEPTH} at most", depth=depth, max=MAX_DEPTH)
    siblings = _siblings(source, parent)
    siblings.insert(_position(position, len(siblings)), {"id": section_id, "file": section_file(section_id), "enabled": True})
    data = _skeleton(ctx.here, title, _newline(ctx.text), depth if is_absolute(source) else 1, tagged=is_absolute(source))
    return _commit(ctx, "add_section", section_id, source, creates=[(ctx.folder / section_file(section_id), data)])


def _clean_titles(titles):
    if not isinstance(titles, dict):
        titles = {}
    extra = sorted(set(titles) - set(LANGUAGES), key=str)
    if extra:
        _refuse("bad_language", f"a group's title is stated in {', '.join(LANGUAGES)} -- not in {', '.join(map(repr, extra))}", language=extra[0])
    missing = [lang for lang in LANGUAGES if not isinstance(titles.get(lang), str) or not titles[lang].strip()]
    if missing:
        _refuse("titles_missing", f"a group needs its title in {', '.join(LANGUAGES)} -- it is printed in the document's language, so it is stated in all three; missing: {', '.join(missing)}", missing=missing)
    return {lang: _clean_title(titles[lang]) for lang in LANGUAGES}


def add_group(here, mode, parent_id, position, group_id, titles, language=None):
    """A new, empty group in document `mode` of a CU or a BP, under `parent_id` (None for the top) at `position`, its `titles` given in all of fr, de and en -- a group prints its title as a heading in the document's own language, so it states all three (`titles_missing`; a language that is none of them is `bad_language`, a title that is empty or holds a line break `bad_title`). Returns an `Edit`; structure.json and the entry's block are written, no file is made. The refusals are `add_section`'s: `bad_id`, `id_exists`, `no_such_node`, `not_a_group`, `bad_position`, `too_deep` -- a group, even an empty one, is a level of the tree -- and `entry_unreadable`.

    The report has no groups (`rs_no_groups`): its sections are the `#include` lines of its entry file and nothing holds them.
    """
    if mode == "rs":
        _refuse("rs_no_groups", "the report has no groups -- its sections stand one after the other in the #include lines of its entry file", mode=mode)
    ctx = _open(here, mode, language)
    clean = _clean_titles(titles)
    _check_id(group_id)
    source = ctx.source
    if find(source, group_id) is not None:
        _refuse("id_exists", f"id {group_id!r} is the id of another section already -- an id is unique in its document", id=group_id)
    parent, depth = _parent(source, parent_id)
    if depth > MAX_DEPTH:
        _refuse("too_deep", f"a group under {parent_id!r} would lie {depth} levels deep -- a document's structure goes down {MAX_DEPTH} at most", depth=depth, max=MAX_DEPTH)
    siblings = _siblings(source, parent)
    siblings.insert(_position(position, len(siblings)), {"id": group_id, "title": clean, "enabled": True, "children": []})
    creates = []
    if is_absolute(source):
        if (ctx.folder / group_file(group_id)).exists():
            _refuse("file_exists", f"{group_file(group_id)}: is there already -- a chapter's file never overwrites one", file=group_file(group_id))
        creates = [(ctx.folder / group_file(group_id), _group_text(_import_line(ctx.here), clean[ctx.language], depth, _newline(ctx.text)).encode("utf-8"))]
    return _commit(ctx, "add_group", group_id, source, creates=creates)


def remove_section(here, mode, node_id, language=None):
    """Section `node_id` of document `mode` taken out of the document -- **and its file kept**: it is moved into `<document>/Sections/archives/<yymmdd-hhmmss>-<id>.typ`, never deleted, which is the rule «Supprimer» archives follows everywhere in Woodcore. Returns an `Edit` whose `archived` holds the destination. A group is removed only once it is empty (`group_not_empty`); an id that is not there is `no_such_node`, a heading inside a file `not_a_section`.

    A **CU or a BP**: the section leaves structure.json, the entry's block is written again, and the file moves. A structure that names a file nobody has written is removed all the same, with nothing to archive. A section shared with another document leaves this document only: the other document's copy is its own file and stays.

    In the **report** (rs) the section's `#include` line is replaced by a comment, `// archived: Sections/<file> (now Sections/archives/<archived file>)`, and the file moves -- unless the entry includes it a second time, when it stays where it is. **The line is commented and not deleted**, so that the entry keeps a trace of what stood there and where it went; but it is no longer an `#include` line, so the tree shows the section gone and not a disabled one whose file does not exist.
    """
    if mode == "rs":
        return _rs_remove(here, node_id)
    ctx = _open(here, mode, language)
    source = ctx.source
    node, _depth, parent = _node(source, node_id)
    if node.get("children"):
        _refuse("group_not_empty", f"group {node_id!r} still holds {len(node['children'])} section(s) -- a group is removed once it is empty", id=node_id, count=len(node["children"]))
    siblings = _siblings(source, parent)
    del siblings[next(i for i, sibling in enumerate(siblings) if sibling is node)]
    archive = None
    own = node.get("file") or (group_file(node_id) if "children" in node and is_absolute(source) else None)
    if own:
        file = ctx.folder / own
        if file.is_file():
            archive = (file, _archive_target(ctx.folder, node_id))
    return _commit(ctx, "remove_section", node_id, source, archive=archive)


def move_node(here, mode, node_id, new_parent_id, position, language=None):
    """Node `node_id` -- a section or a group, with everything under it -- moved under the group `new_parent_id` (None for the top) so that it stands at `position` among that group's children **once it has left its old place** (0 first … the number of children last, None the end). Returns an `Edit`; a node moved to where it stands is an Edit with `changed` False, and nothing is written. No file moves: a section's file is named after its id and its file does not depend on the depth it is included at (the entry's block gives it the offset).

    Refused: a section or a parent that is not there (`no_such_node`), a parent that is a file (`not_a_group`), a group moved into itself or into what it holds (`cycle`), a move that would take the deepest section of the subtree below the fourth level (`too_deep`), a place that does not exist (`bad_position`), an entry that cannot be rewritten (`entry_unreadable`).

    In the **report** the sections stand in the order of their `#include` lines and nothing else, so a section is **moved by moving its line's place in that order**: `new_parent_id` must be None (`rs_no_nesting`) and `position` counts the include lines (commented-out ones too) without the moved one. The include lines stay where they stand in the entry file and exchange sections, as `templates.sync_includes` has them: what is between them -- a heading, a page break -- does not move, a line's indentation stays with its place, and a section switched off stays switched off wherever it goes. **No file is renamed**: the files keep their numbers, which then no longer say the order -- the ids `tree` gives a report's sections are the file names, and a move must not change them.
    """
    if mode == "rs":
        return _rs_move(here, node_id, new_parent_id, position)
    ctx = _open(here, mode, language)
    source = ctx.source
    node, _depth, old_parent = _node(source, node_id)
    if new_parent_id is not None:
        inside = {n["id"] for n, _d, _p in walk({"sections": [node]})}
        if new_parent_id in inside:
            _refuse("cycle", f"{node_id!r} cannot be moved into {new_parent_id!r} -- that is itself, or something it holds", id=node_id, parent=new_parent_id)
    parent, new_depth = _parent(source, new_parent_id)
    deepest = new_depth + _height(node) - 1
    if deepest > MAX_DEPTH:
        _refuse("too_deep", f"{node_id!r} moved there would take a section {deepest} levels deep -- a document's structure goes down {MAX_DEPTH} at most", depth=deepest, max=MAX_DEPTH)
    old = _siblings(source, old_parent)
    del old[next(i for i, sibling in enumerate(old) if sibling is node)]
    new = _siblings(source, parent)
    new.insert(_position(position, len(new)), node)
    puts = []
    if is_absolute(source) and new_depth != _depth:
        # the files the node takes with it: its own and every one under it, their headings shifted by the change of depth
        for sub_node, _d, _p in walk({"sections": [node]}):
            own = sub_node.get("file") or group_file(sub_node["id"])
            file = ctx.folder / own
            try:
                text = typst_paths.read_text(file)
            except (OSError, UnicodeDecodeError):
                continue
            new_text = shift_headings(text, new_depth - _depth)
            if new_text != text:
                puts.append((file, new_text, text))
    return _commit(ctx, "move_node", node_id, source, puts=puts)


def rename_section(here, mode, node_id, new_id, language=None):
    """Section `node_id` of document `mode` given the id `new_id`: its id in the document and -- a section that is a file -- its file, `Sections/<old>.typ` moved to `Sections/<new>.typ` (the bytes untouched; the heading inside is the engineer's prose). Returns an `Edit` whose `renamed` holds the two paths.

    **Ids are meant to be stable**, so a section that is **shared** is refused (`shared`): its id is what the other documents' copies are known by -- a shared section keeps the same id in the convention and in the base de projet. It is shared where structure.json lists documents for it or where its file carries a shared tag (`values`: `shared_with`, `shared_ids`); to rename it, stop sharing first. A group has no file and is not shared: only its id changes. Refused besides: a new id that is not an id (`bad_id`), the id the section has (`same_id`), one another section has (`id_exists`), a file lying at the new name (`file_exists`), a section that is not there (`no_such_node`, `not_a_section`), an entry that cannot be rewritten (`entry_unreadable`).

    In the **report** `node_id` is the file's stem (what `tree` gives) and `new_id` the new one: the file is renamed and **every `#include` line that names it** -- commented-out ones too -- is rewritten, the rest of each line as it was. A report file carrying a shared tag is refused likewise.
    """
    if mode == "rs":
        return _rs_rename(here, node_id, new_id)
    ctx = _open(here, mode, language)
    source = ctx.source
    node, _depth, _parent_of = _node(source, node_id)
    _check_id(new_id)
    if new_id == node_id:
        _refuse("same_id", f"the section is called {node_id!r} already", id=node_id)
    if find(source, new_id) is not None:
        _refuse("id_exists", f"id {new_id!r} is the id of another section already -- an id is unique in its document", id=new_id)
    rename = None
    if "file" in node:
        file = ctx.folder / node["file"]
        shared_ids = _shared_ids_in(file)
        if node.get("shared_with") or shared_ids:
            _refuse("shared", f"section {node_id!r} is shared ({', '.join(node.get('shared_with') or ['by its tags'])}) -- a shared section keeps its id, which is how the documents' copies are known; stop sharing it first",
                    id=node_id, shared_with=list(node.get("shared_with") or ()), shared_ids=list(shared_ids))
        target = ctx.folder / section_file(new_id)
        if target.exists():
            _refuse("file_exists", f"{section_file(new_id)}: is there already -- a section never overwrites a file", file=section_file(new_id))
        node["file"] = section_file(new_id)
        if file.is_file():
            rename = (file, target)
    elif "children" in node and is_absolute(source):
        file, target = ctx.folder / group_file(node_id), ctx.folder / group_file(new_id)
        if target.exists():
            _refuse("file_exists", f"{group_file(new_id)}: is there already -- a section never overwrites a file", file=group_file(new_id))
        if file.is_file():
            rename = (file, target)
    node["id"] = new_id
    return _commit(ctx, "rename_section", new_id, source, rename=rename)


def suggest_id(here, mode, title):
    """An id for a new section called `title` that is free in document `mode`: for a CU or a BP the title's slug (`templates.slug`: accents taken off, hyphens between words -- `Live loads` gives `live-loads`), `section-` before it where it would start with a digit, `-2`, `-3` … after it where an id or a file has it already; for the report the next number, three digits wide, and the slug (`008-brandschutz`), as the report's sections are named. Only a proposal: it is what `add_section` takes, and what a window shows for the engineer to write over."""
    import templates
    _check_mode(here, mode, None)
    base = templates.slug(title)
    if mode == "rs":
        entry = here.document_typ("rs")
        stems = {item["name"][:-4] for item in _rs_items(_read_entry(entry))}
        folder = here.document_dir("rs") / SECTIONS_DIR
        if folder.is_dir():
            stems.update(path.stem for path in folder.glob("*.typ"))
        numbers = [int(m.group(1)) for m in (re.match(r"^(\d+)-", stem) for stem in stems) if m]
        number = max(numbers, default=0) + 1
        return f"{number:0{max(3, len(str(number)))}d}-{base}"
    source = read(here.structure_file(mode))
    folder = here.document_dir(mode)
    if not ID_PATTERN.match(base):
        base = f"section-{base}"
    candidate, number = base, 2
    while find(source, candidate) is not None or (folder / section_file(candidate)).exists():
        candidate = f"{base}-{number}"
        number += 1
    return candidate


# --- the report: the same operations on its #include lines ---------------------------------------

def _rs_items(text):
    """The report's `#include "Sections/…"` lines as items, in order: {id, name, comment, body, line} -- `comment` what stands before the include (`// `, or nothing), `body` the include itself with whatever follows it on the line, `line` the line's index. The pieces are kept apart so that a line can be put in another place and come out as it was."""
    import templates
    lines = _split(text)
    items = []
    for include in _include_lines(text):
        bare = _strip(lines[include.line])
        prefix = templates._INCLUDE.match(bare).group(1)
        indent = re.match(r"[ \t]*", prefix).group(0)
        items.append({"id": include.id, "name": include.name, "comment": prefix[len(indent):], "body": bare[len(prefix):], "line": include.line})
    return items


def _rs_item(items, node_id):
    for item in items:
        if item["id"] == node_id:
            return item
    if isinstance(node_id, str) and ("#" in node_id or "/" in node_id):
        _refuse("not_a_section", f"{node_id!r} is a heading or an object inside a section file, not a section -- the report's sections are its #include lines", id=node_id)
    known = ", ".join(item["id"] for item in items) or "none"
    _refuse("no_such_node", f"the report has no `#include \"Sections/...\"` line for {node_id!r} -- its sections are {known}", id=node_id)


def _rs_lay_out(text, items):
    """`text` with its include lines holding `items` in order: the lines stay where they stand, each gets the next item -- its own comment and its own words, the indentation and the line ending of the place -- and an item too many takes a new line after the last include (or at the end of the file where there is none). Every other byte stays, and a line that holds the item it held comes out as it was."""
    import templates
    lines = _split(text)
    slots = [include.line for include in _include_lines(text)]
    newline = _newline(text)
    out, extra = list(lines), []
    for k, item in enumerate(items):
        if k < len(slots):
            old = lines[slots[k]]
            prefix = templates._INCLUDE.match(_strip(old)).group(1)
            indent = re.match(r"[ \t]*", prefix).group(0)
            out[slots[k]] = indent + item["comment"] + item["body"] + old[len(_strip(old)):]
        else:
            extra.append(item["comment"] + item["body"] + newline)
    if extra:
        if slots:
            last = slots[-1]
            if not out[last].endswith(("\n", "\r")):
                out[last] += newline
            out[last + 1:last + 1] = extra
        else:
            if out and not out[-1].endswith(("\n", "\r")):
                out[-1] += newline
            out.extend(extra)
    return "".join(out)


def _rs_edit(op, node_id, entry, text, new_text, creates=(), moves=(), archived=(), renamed=()):
    steps = [_step_create(path, data) for path, data in creates]
    changed = new_text != text
    if changed:
        steps.append(_step_put(entry, new_text, text))
    steps += [_step_move(*move) for move in moves]
    _run(steps)
    return Edit(op, "rs", node_id, False, changed, tuple(path for path, _data in creates), tuple(archived), tuple(renamed))


def _rs_no_nesting(parent_id):
    if parent_id is not None:
        _refuse("rs_no_nesting", "the report has no nesting -- its sections stand one after the other in the #include lines of its entry file, so a section goes under no group", parent=parent_id)


def _rs_add(here, parent_id, position, section_id, title):
    _rs_no_nesting(parent_id)
    title = _clean_title(title)
    _check_stem(section_id)
    entry = here.document_typ("rs")
    text = _read_entry(entry)
    items = _rs_items(text)
    if section_id.lower() in {item["name"][:-4].lower() for item in items}:
        _refuse("id_exists", f"{section_id!r} is the file of a section of the report already", id=section_id)
    rel = f"{SECTIONS_DIR}/{section_id}.typ"
    file = here.document_dir("rs") / rel
    if file.exists():
        _refuse("file_exists", f"{rel}: is there already -- a section never overwrites a file", file=rel)
    items.insert(_position(position, len(items)), {"id": section_id, "name": f"{section_id}.typ", "comment": "", "body": f'#include "{rel}"'})
    new_text = _rs_lay_out(text, items)
    return _rs_edit("add_section", section_id, entry, text, new_text, creates=[(file, _skeleton(here, title, _newline(text)))])


def _rs_remove(here, node_id):
    entry = here.document_typ("rs")
    text = _read_entry(entry)
    items = _rs_items(text)
    item = _rs_item(items, node_id)
    folder = here.document_dir("rs")
    file = folder / SECTIONS_DIR / item["name"]
    twice = any(other is not item and other["name"] == item["name"] for other in items)
    target = _archive_target(folder, item["name"][:-4]) if file.is_file() and not twice else None
    note = f"// archived: {SECTIONS_DIR}/{item['name']}" + (f" (now {SECTIONS_DIR}/{ARCHIVES_DIR}/{target.name})" if target else "")
    lines = _split(text)
    old = lines[item["line"]]
    lines[item["line"]] = re.match(r"[ \t]*", old).group(0) + note + old[len(_strip(old)):]
    moves = [(file, target)] if target else []
    return _rs_edit("remove_section", node_id, entry, text, "".join(lines), moves=moves, archived=[target] if target else [])


def _rs_move(here, node_id, new_parent_id, position):
    _rs_no_nesting(new_parent_id)
    entry = here.document_typ("rs")
    text = _read_entry(entry)
    items = _rs_items(text)
    item = _rs_item(items, node_id)
    rest = [other for other in items if other is not item]
    rest.insert(_position(position, len(rest)), item)
    return _rs_edit("move_node", node_id, entry, text, _rs_lay_out(text, rest))


def _rs_rename(here, node_id, new_id):
    entry = here.document_typ("rs")
    text = _read_entry(entry)
    items = _rs_items(text)
    item = _rs_item(items, node_id)
    _check_stem(new_id)
    old_name = item["name"]
    if new_id == old_name[:-4]:
        _refuse("same_id", f"the section is called {new_id!r} already", id=new_id)
    if new_id.lower() in {other["name"][:-4].lower() for other in items}:
        _refuse("id_exists", f"{new_id!r} is the file of a section of the report already", id=new_id)
    folder = here.document_dir("rs")
    file = folder / SECTIONS_DIR / old_name
    shared_ids = _shared_ids_in(file)
    if shared_ids:
        _refuse("shared", f"section {node_id!r} carries shared blocks ({', '.join(shared_ids)}) -- a shared section keeps its name, which is how the documents' copies are known; stop sharing it first",
                id=node_id, shared_with=[], shared_ids=list(shared_ids))
    target = folder / SECTIONS_DIR / f"{new_id}.typ"
    if target.exists():
        _refuse("file_exists", f"{SECTIONS_DIR}/{new_id}.typ: is there already -- a section never overwrites a file", file=f"{SECTIONS_DIR}/{new_id}.typ")
    for other in items:
        if other["name"] == old_name:
            other["name"] = f"{new_id}.typ"
            other["body"] = other["body"].replace(f'"{SECTIONS_DIR}/{old_name}"', f'"{SECTIONS_DIR}/{new_id}.typ"')
    moves = [(file, target)] if file.is_file() else []
    return _rs_edit("rename_section", new_id, entry, text, _rs_lay_out(text, items), moves=moves, renamed=[(file, target)] if moves else [])


# --- the tree and the compiled PDF ---------------------------------------------------------


