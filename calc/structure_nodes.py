"""The tree of a document -- its groups and sections from structure.json, the report's from its #include lines, each section's headings and objects, what is shared where -- as the «Structure du document» tab shows it: split out of calc/structure.py (issue #30), moved verbatim. structure.py imports every name back, so structure.tree is still read where it always was.
"""

from dataclasses import dataclass, field
from pathlib import Path
import typst_paths
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


@dataclass(eq=False)
class Node:
    """One row of a document's tree.

    `kind` -- a `group` (a section of a CU or a BP that only holds others and prints its own title as a heading), a `file` (a section file: a `Sections/<id>.typ` of a CU or a BP, a file the report includes), a `heading` (one of the headings inside a file **that carries no object tags**, after the first, which the file's own node stands for) or an `object` (one of the objects of a file that carries tags -- a heading, a paragraph, a table, a list to tick …: `object_type` says which; see below).

    **A file that carries object tags has its objects for children** (calc/typst_objects.py): flat, in the order of the file, **every heading and every paragraph among them** -- a heading is an object, and the file's own first heading is the first of them. Their id is `<file id>/<object id>`, `object_id` the tag's own, `title` a short label (`typst_objects.object_title`: a heading's title, a paragraph's first words, a table's caption), `line` the 0-based line of the **first line of the body** -- the heading's own line for a heading, so that `set_title` rewrites it --, `span` the lines of its two tags, `state` canonical / hand_edited / unreadable, `shared` the id of the shared block it stands in (None outside one). `level` is the **absolute** level of a heading, and for any other object the level of the heading it follows plus one -- where a window indents it. A heading of such a file outside every object (a file half tagged) is a `heading` node among them, as before. A file with no tags keeps its headings as nested `heading` nodes, as it always had.

    `id` -- a group's or a leaf's structure id (CU, BP), a file's stem (RS: `001-einleitung`; `001-einleitung#2` where one file is included twice), a heading's `<file id>#<n>`, n counting the file's headings from 1 so that the first is the file's own and the second is `#2`. Unique in the document, and what `set_enabled`, `set_title` and `align` are given.

    `title` -- in the document's language: a group's from `structure.json`, a file's and a heading's as written in the file (markup source; `plain_title` for the words). `level` -- the **absolute** level it is printed at, the offsets the structure block applies included: a group at depth d is level d, a leaf at depth d has its first heading's level plus d - 1. `file` -- its file, relative to the document's folder and `/`-separated, None for a group. `line` -- the 0-based line of its heading in that file, None where it has none (a group, a file without a heading).

    `enabled` -- its own state: the section's flag, or whether the report's `#include` line is commented out; a heading has no flag and takes its file's. `active` -- whether it is printed: enabled and every group above it enabled, which is what a tab greys the row by and `align` leaves out. `separate_file` -- the node opens a `.typ` file of its own (the «separate .typ» badge): every file node. `shared_with` -- the other documents its file is shared with: what `structure.json` lists, and every document that has a file carrying one of its shared tags. `shared_ids` -- the shared ids its file carries. `parent` -- its parent's id, None at the top. `problems` -- what is wrong with its file, said by name: missing, not readable, a tag Woodcore cannot read.
    """
    kind: str
    id: str
    title: str
    level: int
    file: str = None
    enabled: bool = True
    active: bool = True
    separate_file: bool = False
    shared_with: tuple = ()
    shared_ids: tuple = ()
    line: int = None
    parent: str = None
    problems: tuple = ()
    children: list = field(default_factory=list)
    object_type: str = None
    object_id: str = None
    shared: str = None
    state: str = None
    span: tuple = None

    def as_dict(self):
        """The node and its subtree as plain dicts: what a test compares and a log prints."""
        out = {key: getattr(self, key) for key in ("kind", "id", "title", "level", "file", "enabled", "active", "separate_file", "shared_with", "shared_ids", "line", "parent", "problems",
                                                   "object_type", "object_id", "shared", "state", "span")}
        out["children"] = [child.as_dict() for child in self.children]
        return out


def find_node(nodes, node_id):
    """The node with id `node_id` in `nodes` and their subtrees, or None."""
    return next((node for node in flatten(nodes) if node.id == node_id), None)


def document_language(here, mode):
    """The language document `mode` of project `here` is written in: the `doc-lang` of its config.typ, else the language its entry file sets the engine to, else German -- the language a group's title is printed in."""
    import templates   # here and not at the top: the tree is read by modules templates is imported beside
    written = templates.read_languages(here.document_typ(mode))
    for lang in written:
        if lang in LANGUAGES:
            return lang
    return "de"


def _nest(root, root_id, nodes):
    """`nodes` -- headings, in document order -- put under `root` (a list of children) by their levels: a heading goes under the nearest one before it that has a smaller level, and under the root where there is none, so a second `=` of a file with one `=` already stays in the file."""
    stack = []
    for node in nodes:
        while stack and stack[-1].level >= node.level:
            stack.pop()
        parent = stack[-1] if stack else None
        node.parent = parent.id if parent else root_id
        (parent.children if parent else root).append(node)
        stack.append(node)


def _read_section(path):
    """(text, None) of a section file, or (None, why) where it cannot be read -- a structure that names a file nobody has written yet is a tree with a row that says so, not an error."""
    try:
        return typst_paths.read_text(path), None
    except FileNotFoundError:
        return None, "the file does not exist"
    except UnicodeDecodeError:
        return None, "the file is not UTF-8 text"
    except OSError as exc:
        return None, f"the file could not be read -- {exc}"


def _file_node(doc_dir, rel, node_id, offset, enabled, active, parent, listed=()):
    """The node of the section file `rel` of the document in `doc_dir`, with its headings under it. `offset` is the heading offset it is included at (depth - 1); `listed` the documents structure.json says it is shared with."""
    text, error = _read_section(Path(doc_dir) / rel)
    problems = [f"{rel}: {error}"] if error else []
    headings, shared_ids, objects = [], (), []
    if text is not None:
        headings = scan_headings(text)
        if "woodcore:" in text:
            blocks, found = pair_tags(text)
            problems += [f"{rel}, {problem}" for problem in found]
            shared_ids = tuple(dict.fromkeys(b.id for b in blocks if b.kind == "shared"))
            if any(b.kind == "object" for b in blocks):
                import typst_objects    # here and not at the top: typst_objects reads the tags with this module
                objects = typst_objects.scan(text)[0]
    first = headings[0] if headings else None
    node = Node("file", node_id, first.title if first and first.title else node_id,
                (first.level if first else 1) + offset, rel, enabled, active, True, tuple(listed), shared_ids,
                first.line if first else None, parent, tuple(problems))
    if not objects:
        _nest(node.children, node_id,
              [Node("heading", f"{node_id}#{k}", h.title, h.level + offset, rel, enabled, active, False, (), (), h.line)
               for k, h in enumerate(headings[1:], 2)])
        return node
    node.children = _object_nodes(node, objects, headings, offset)
    return node


def _object_nodes(node, objects, headings, offset):
    """The children of a file that carries object tags: one `object` node per object, flat, in file order -- and, among them, a `heading` node for each heading that stands outside every object (but the file's own first). A heading is shown at its absolute level; any other object at the level of the heading shown before it, plus one: where a window indents it."""
    import typst_objects
    inside = [range(o.start + 1, o.end) for o in objects]
    items = []
    for o in objects:
        child = Node("object", f"{node.id}/{o.id}", typst_objects.object_title(o), node.level, node.file, node.enabled, node.active, False, (), (), o.start + 1, node.id,
                     (), [], o.type, o.id, o.shared, o.state, (o.start, o.end))
        if o.type == "heading":
            try:
                child.level = typst_objects.model_for_body("heading", o.written).level + offset
            except typst_objects.ModelError:
                child.level = None      # a heading that cannot be read: it sits where the heading before it left the level
        items.append((o.start, child))
    for k, h in enumerate(headings[1:], 2):
        if any(h.line in span for span in inside):
            continue
        items.append((h.line, Node("heading", f"{node.id}#{k}", h.title, h.level + offset, node.file, node.enabled, node.active, False, (), (), h.line, node.id)))
    items.sort(key=lambda item: item[0])
    level = node.level
    for _line, child in items:
        if child.kind == "object" and child.object_type != "heading":
            child.level = level + 1
        elif child.level is None:
            child.level = level
        else:
            level = child.level
    return [child for _line, child in items]


@dataclass(frozen=True)
class Include:
    """One `#include "Sections/<name>"` line of the report's entry file: its line (0-based), the file's name, whether it is printed and the id the tree gives it."""
    line: int
    name: str
    enabled: bool
    id: str


def _include_lines(text):
    """The `#include "Sections/…"` lines of a report's entry file, commented out or not, in order -- templates.sync_includes' own pattern, so the two agree on what a section's line is. A file included twice gets `#2` after its stem the second time, so that every line has an id."""
    import templates
    found, counts = [], {}
    for index, line in enumerate(_split(text)):
        match = templates._INCLUDE.match(_strip(line))
        if match is None:
            continue
        name = match.group(2)
        stem = name[:-len(".typ")]
        counts[stem] = counts.get(stem, 0) + 1
        found.append(Include(index, name, not match.group(1).strip().startswith("//"), stem if counts[stem] == 1 else f"{stem}#{counts[stem]}"))
    return found


def section_files(here, mode):
    """[(file, printed)] of document `mode`: each section file its structure names -- a CU's or a BP's structure.json, the report's `#include` lines --, from the document's folder, and whether the document prints it (its own `enabled` and its groups'). What `tree` lists of a document's files, without reading a heading of them: the graph of dependencies' (spec 2026-10-21-graphe-dependances, ARCH-RISK-1104), which reads every section at every export. [] where the structure cannot be read."""
    if mode not in here.modes:
        return []
    if mode == "rs":
        try:
            text = typst_paths.read_text(here.document_typ("rs"))
        except (OSError, UnicodeDecodeError):
            return []
        return [(f"{SECTIONS_DIR}/{include.name}", include.enabled) for include in _include_lines(text)]
    try:
        source = read(here.structure_file(mode))
    except Exception:   # broad: a structure.json that cannot be read is the Structure tab's to say (StructureError)
        return []
    absolute = is_absolute(source)
    out = []

    def walk(nodes, active):
        for entry in nodes:
            printed = active and bool(entry.get("enabled", True))
            if "children" in entry:
                if absolute:
                    out.append((group_file(entry["id"]), printed))
                walk(entry["children"], printed)
            elif entry.get("file"):
                out.append((entry["file"], printed))
    walk(source["sections"], True)
    return out


def _tree_report(here):
    """The report's tree: one node per `#include` line of the entry file, in order, each with the headings of its file; a heading the entry file carries itself stands among them. No nesting between files: the report keeps no structure beside its include lines, so what the tree shows of the order is the order there."""
    entry = here.document_typ("rs")
    try:
        text = typst_paths.read_text(entry)
    except (OSError, UnicodeDecodeError) as exc:
        raise StructureError(f"{entry.name}: could not be read -- {exc}") from None
    items = []
    for k, h in enumerate(scan_headings(text), 1):
        items.append((h.line, Node("heading", f"{entry.stem}#{k}", h.title, h.level, entry.name, True, True, False, (), (), h.line)))
    for include in _include_lines(text):
        items.append((include.line, _file_node(entry.parent, f"{SECTIONS_DIR}/{include.name}", include.id, 0, include.enabled, include.enabled, None)))
    items.sort(key=lambda item: item[0])
    return [node for _line, node in items]


def _group_title(folder, group_id):
    """(title, line, problem) of an absolute document's chapter, as its file writes it: the first heading's title and line, or (None, None, why) where the file says none."""
    text, error = _read_section(Path(folder) / group_file(group_id))
    if text is None:
        return None, None, f"{group_file(group_id)}: {error}"
    headings = scan_headings(text)
    if not headings:
        return None, None, f"{group_file(group_id)}: holds no heading"
    return headings[0].title, headings[0].line, None


def _tree_structured(here, mode, language):
    """The tree of a CU or a BP: structure.json's sections, a group as a group and a leaf as the node of its file with the headings of the file under it. In an absolute document a group's title is its file's first heading, and its node names that file; a leaf's headings are read at the level they are written at."""
    source = read(here.structure_file(mode))
    folder = here.document_dir(mode)
    absolute = is_absolute(source)

    def build(nodes, depth, parent, active):
        out = []
        for entry in nodes:
            own = bool(entry.get("enabled", True))
            printed = active and own
            if "children" in entry:
                node = Node("group", entry["id"], title_of(entry, language), depth, None, own, printed, False, (), (), None, parent)
                if absolute:
                    title, line, problem = _group_title(folder, entry["id"])
                    node.file, node.separate_file, node.line = group_file(entry["id"]), True, line
                    if title:
                        node.title = title
                    if problem:
                        node.problems = (problem,)
                node.children = build(entry["children"], depth + 1, entry["id"], printed)
            else:
                node = _file_node(folder, entry["file"], entry["id"], 0 if absolute else depth - 1, own, printed, parent, entry.get("shared_with", ()))
            out.append(node)
        return out

    return build(source["sections"], 1, None, True)


def _shared_index(here):
    """{mode: {shared id}} for every document of the project: the shared ids the section files in its `Sections/` carry. A file whose tags cannot be read carries none."""
    index = {}
    for mode in here.modes:
        ids = set()
        for path in sorted((here.document_dir(mode) / SECTIONS_DIR).glob("*.typ")):
            text, _error = _read_section(path)
            if text is None or "woodcore:shared" not in text:
                continue
            ids.update(b.id for b in pair_tags(text)[0] if b.kind == "shared")
        index[mode] = ids
    return index


def _fill_shared(here, mode, nodes):
    """`shared_with` of every file node: what structure.json lists, and every other document that has a file carrying one of the node's shared ids -- in SHARE_MODES' order."""
    files = [n for n in flatten(nodes) if n.kind == "file"]
    if not any(n.shared_ids for n in files):
        return
    index = _shared_index(here)
    for node in files:
        modes = set(node.shared_with)
        modes.update(other for other, ids in index.items() if other != mode and ids.intersection(node.shared_ids))
        node.shared_with = tuple(m for m in SHARE_MODES if m in modes)


def tree(here, mode, language=None):
    """The structure of document `mode` of project `here` (calc/project.py), as a list of top-level `Node`s in document order -- the subtree of each under `children`.

    A **CU or a BP** (`mode` cu or bp) is read from its `structure.json`: groups, and leaves that are section files whose headings are scanned. The **report** (rs) has no structure.json: its tree is its entry file's `#include "Sections/…"` lines -- enabled, and commented out, which is how a disabled section is written there (templates.sync_includes) -- each with the headings of the file it includes; the entry's own headings stand among them. `language` is the language a group's title is given in: the document's own (`document_language`) unless named. A section file that is not there, or whose tags cannot be read, is a node with `problems` and not an error; a structure.json or an entry file that cannot be read is a StructureError.
    """
    if mode not in SHARE_MODES:
        raise StructureError(f"document {mode!r} -- expected one of {', '.join(SHARE_MODES)}")
    if mode not in here.modes:
        raise StructureError(f"this project has no {mode} document -- it is laid out as a report alone, and migration gives it the three")
    if language is None:
        language = document_language(here, mode)
    elif language not in LANGUAGES:
        raise StructureError(f"language {language!r} -- expected one of {', '.join(LANGUAGES)}")
    nodes = _tree_report(here) if mode == "rs" else _tree_structured(here, mode, language)
    _fill_shared(here, mode, nodes)
    return nodes
