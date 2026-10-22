"""A document's structure.json -- its constants, its check, its key order, its reading -- and the error every refusal of the catalogue is: split out of calc/structure.py (issue #30), moved verbatim. structure.py imports every name back, so structure.StructureError and structure.read are still read where they always were.
"""

import json
from pathlib import Path
import validation
from domains._common import fail as _fail  # one copy of the domains' helpers (spec 2026-10-19-base-saine-nettoyage, G4)
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


FILE = "structure.json"


FORMAT = "woodcore-structure"


SCHEMA_VERSION = "1.0"


# The documents that have a structure.json. RS has none: its sections are the report's own `#include` lines.
MODES = ("cu", "bp")


# The other documents a section may be shared with (sharing copies the file into their folders): the three modes.
SHARE_MODES = ("cu", "bp", "rs")


# A group's title is printed in the document's language, so it is stated in all three.
LANGUAGES = ("fr", "de", "en")


SECTIONS_DIR = "Sections"


# How deep the tree goes: a chapter, its sections, their sub-sections, their sub-sub-sections -- the four heading levels config.typ gives their own white (v0.100).
MAX_DEPTH = 4


# What a node may carry. A group has `title` and `children` and no file; a leaf has `file` and no title (it takes its title from the first heading of its file) and no children; `shared_with` is a leaf's alone, the file being the unit of sharing.
NODE_KEYS = ("id", "title", "file", "enabled", "shared_with", "children")


TOP_KEYS = ("schema_version", "format", "document", "headings", "sections")


# What `headings` says where a document writes its headings at the level they print at, and gives each chapter a file of its own (06.10.2026). Absent, the document is laid out with offsets, as it was until then.
ABSOLUTE = "absolute"


class StructureError(validation.ValidationError):
    """A structure that cannot be read, written or synced into an entry file, said by name. A ValidationError, so whatever catches a defect of a source catches this.

    The operations on the catalogue (add_section, add_group, remove_section, move_node, rename_section) refuse with a `code` -- one of CODES -- and the `values` the refusal is about (`id`, `position`, `depth` …), beside the English sentence: the window writes its own sentence for the code, as it does for an `engine.Note`. An error raised by the older functions states no code (""), and its sentence is all there is to it.
    """

    def __init__(self, message="", code="", **values):
        super().__init__(message)
        self.code = code
        self.values = values


def blank(document):
    """An empty structure for `document` (cu or bp): what a new document starts with before a template fills it."""
    return {"schema_version": SCHEMA_VERSION, "format": FORMAT, "document": document, "sections": []}


def is_absolute(source):
    """Whether a structure writes its headings at the level they print at, its chapters in files of their own."""
    return source.get("headings") == ABSOLUTE


def group_file(group_id):
    """Where a chapter's file lies in an absolute document: `Sections/<id>.typ`, as a section's -- the ids of a document's chapters and sections being unique together."""
    return section_file(group_id)


def section_file(section_id):
    """Where a leaf's file lies in its document's folder: `Sections/<id>.typ`."""
    return f"{SECTIONS_DIR}/{section_id}.typ"


def leaves(source):
    """The leaves -- the sections that are files -- in document order, as (node, depth)."""
    return [(node, depth) for node, depth, _parent in walk(source) if "file" in node]


def named_files(source):
    """Every file the structure names, in document order, as (node, file): each leaf's, and in an absolute document each chapter's (`group_file`) -- what a template must carry and what is copied of a document."""
    absolute = is_absolute(source)
    out = []
    for node, _depth, _parent in walk(source):
        if "file" in node:
            out.append((node, node["file"]))
        elif absolute and "children" in node:
            out.append((node, group_file(node["id"])))
    return out


def find(source, section_id):
    """(node, depth, parent) of the section `section_id`, or None."""
    for found in walk(source):
        if found[0].get("id") == section_id:
            return found
    return None


def title_of(node, language):
    """A group's title in `language` -- a leaf has none, its heading being in its file."""
    return node.get("title", {}).get(language, "")


def check_source(source, where=FILE):
    """The structure as Woodcore writes it, checked -- the schema first, then everything the schema walker cannot say (docs/architecture/data-contracts.md §3.6). Raises a ValidationError naming the section and the field."""
    if not isinstance(source, dict):
        _fail(where, "is not a JSON object")
    try:
        validation.validate_structure(source, "structure")
    except validation.ValidationError as exc:
        _fail(where, str(exc))
    extra = sorted(set(source) - set(TOP_KEYS))
    if extra:
        _fail(where, f"carries {', '.join(map(repr, extra))} -- a structure holds {', '.join(TOP_KEYS)} and nothing else")
    if source["document"] not in MODES:
        _fail(where, f"document is {source['document']!r} -- expected one of {', '.join(MODES)}, the documents that have a structure.json")
    if "headings" in source and source["headings"] != ABSOLUTE:
        _fail(where, f"headings is {source['headings']!r} -- {ABSOLUTE!r}, or no such key for a document laid out with offsets")
    seen = {}

    def visit(nodes, depth):
        for position, node in enumerate(nodes, 1):
            # Named by its own id where it has a usable one, so a defect is found in the tab's tree and not by counting.
            who = f"{where}, section {node.get('id', position)!r}"
            if depth > MAX_DEPTH:
                _fail(who, f"lies {depth} levels deep -- a document's structure goes down {MAX_DEPTH} at most")
            extra = sorted(set(node) - set(NODE_KEYS))
            if extra:
                _fail(who, f"carries {', '.join(map(repr, extra))} -- a section holds {', '.join(NODE_KEYS)} and nothing else")
            section_id = node["id"]
            if not ID_PATTERN.match(section_id):
                _fail(who, f"id {section_id!r} is not an id -- English, lower case, letters and digits parted by single hyphens, starting with a letter (live-loads)")
            if section_id in seen:
                _fail(who, f"id {section_id!r} is the id of another section already -- an id is unique in its document")
            seen[section_id] = True
            group, leaf = "children" in node, "file" in node
            if group == leaf:
                _fail(who, "is " + ("both a group (children) and a section file (file)" if group else "neither a group (children) nor a section file (file)"))
            if group:
                for lang in LANGUAGES:
                    title = node.get("title", {}).get(lang)
                    if not isinstance(title, str) or not title.strip():
                        _fail(who, f"a group needs its title in {lang} -- it is printed in the document's language, so it is stated in all of {', '.join(LANGUAGES)}")
                    if any(ord(ch) < 32 for ch in title):
                        _fail(who, f"title in {lang} holds a line break or another control character")
                if "shared_with" in node:
                    _fail(who, "shared_with belongs to a section file -- sharing copies a file, so a group is not shared")
                visit(node["children"], depth + 1)
            else:
                if "title" in node:
                    _fail(who, "a section file takes its title from the first heading of its file -- it states none here (a second place for it would drift)")
                if node["file"] != section_file(section_id):
                    _fail(who, f"file is {node['file']!r} -- a section file is named after its id: {section_file(section_id)!r}")
                shared = node.get("shared_with", [])
                for mode in shared:
                    if mode not in SHARE_MODES or mode == source["document"]:
                        _fail(who, f"shared_with lists {mode!r} -- the other documents it is shared with: {', '.join(m for m in SHARE_MODES if m != source['document'])}")
                if len(set(shared)) != len(shared):
                    _fail(who, f"shared_with lists a document twice: {shared!r}")

    visit(source["sections"], 1)
    return source


def ordered(source):
    """The structure in the one shape Woodcore writes: keys in a fixed order, `enabled` always stated, the languages of a title in the order of LANGUAGES, `shared_with` left out where empty. Nothing is checked here (`write` does)."""
    def node_out(node):
        out = {"id": node["id"]}
        if "title" in node:
            out["title"] = {lang: node["title"][lang] for lang in LANGUAGES}
        if "file" in node:
            out["file"] = node["file"]
        out["enabled"] = bool(node.get("enabled", True))
        if node.get("shared_with"):
            out["shared_with"] = list(node["shared_with"])
        if "children" in node:
            out["children"] = [node_out(child) for child in node["children"]]
        return out
    out = {"schema_version": SCHEMA_VERSION, "format": FORMAT, "document": source["document"]}
    if is_absolute(source):
        out["headings"] = ABSOLUTE
    out["sections"] = [node_out(node) for node in source["sections"]]
    return out


def dumps(source):
    """The text of a structure as it is written: ordered, two-space indent, one trailing newline."""
    return json.dumps(ordered(source), ensure_ascii=False, indent=2) + "\n"


def read(path):
    """A document's structure, read and checked. A missing or unreadable file is an error, not a blank structure: a CU or BP folder without its structure.json is a document Woodcore cannot lay out, and saying so is better than printing nothing."""
    path = Path(path)
    try:
        source = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        _fail(str(path), f"could not be read -- {exc}")
    return check_source(source, path.name)
