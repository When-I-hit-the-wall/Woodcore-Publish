"""Reading a section file of the three documents: its woodcore tags paired (scan_tags, pair_tags), its headings lexed as Typst writes them (scan_headings), and the bookmarks of a compiled PDF matched to them -- split out of calc/structure.py (issue #30), moved verbatim. structure.py imports every name back, so structure.scan_tags and the rest are still read where they always were.
"""

import bisect
import io
import re
from collections import namedtuple
from dataclasses import dataclass, field
from pathlib import Path
import typst_paths


# A section's id: English, lower case, hyphen-separated, never changed by a rename -- it names the file (`Sections/<id>.typ`) and every call that refers to the section.
ID_PATTERN = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")


def _a(kind):
    """«a shared», «an object»: the article a kind of tag is said with."""
    return ("an " if kind[:1] in "aeiou" else "a ") + kind


def walk(source):
    """Every node of the structure in document order -- a group before its children -- as (node, depth, parent), depth counted from 1 and parent None at the top."""
    def visit(nodes, depth, parent):
        for node in nodes:
            yield node, depth, parent
            if isinstance(node.get("children"), list):
                yield from visit(node["children"], depth + 1, node)
    yield from visit(source.get("sections", ()), 1, None)


def _split(text):
    """The lines of `text`, each with its own terminator -- `\\r\\n`, `\\n` or `\\r` -- so that putting them back together gives `text` byte for byte."""
    return re.findall(r"[^\r\n]*(?:\r\n|\r|\n)|[^\r\n]+", text)


def _strip(line):
    return line.rstrip("\r\n")


# The kinds of tag: the generated block of an entry file, a parametric object, a block shared between documents.
KINDS = ("structure", "object", "shared")


# The calls a `woodcore:object` tag may name -- the list of the norms alone since the parametric commands of lib/document.typ were written in raw Typst (spec 2026-10-21-commandes-typst-refonte, REQ-019) --, and the objects whose body is markup and no call -- a heading, a paragraph, a table written in raw Typst (calc/typst_objects.py, calc/typst_raw_table.py) --, and the six objects of an export sheet (lib/sheet.typ, v0.114), which a document's section does not hold. `check_tags` takes another list, or None for none.
OBJECT_TYPES = ("show-norm-list", "heading", "text", "table",
                "sheet-page", "sheet-text", "sheet-viewport", "sheet-section", "sheet-legend", "sheet-fire-viewport", "sheet-fire-legend", "sheet-position-list", "sheet-quantities", "sheet-titleblock")


# What a block may hold: a shared block holds objects -- never another shared block -- and nothing else holds any tag. A block that would straddle two others is caught by the same rule, since its own closing tag then finds another block innermost.
ALLOWED_INSIDE = {"shared": ("object",), "object": (), "structure": ()}


# A tag is a line comment alone on its line, leading white space allowed, and the prefix exact: `// woodcore:`, one space.
_TAG_LINE = re.compile(r"^[ \t]*// woodcore:(?P<close>/)?(?P<kind>[a-z][a-z-]*)(?P<rest>.*)$")


@dataclass(frozen=True)
class Tag:
    """One tag line: where it is (0-based), what kind, whether it closes, and the type and id it names -- `type` only on an opening object tag, `id` on every tag but the structure's."""
    line: int
    kind: str
    closing: bool
    id: str = None
    type: str = None


@dataclass(frozen=True)
class Block:
    """An opening tag and the closing tag that matches it: the lines of the two tags (0-based); what lies between is `range(start + 1, end)`."""
    kind: str
    id: str
    type: str
    start: int
    end: int


@dataclass(frozen=True)
class Problem:
    """Something wrong with the tags of a file, at a line (0-based, printed 1-based)."""
    line: int
    message: str

    def __str__(self):
        return f"line {self.line + 1}: {self.message}"


def scan_tags(text, object_types=OBJECT_TYPES):
    """Every tag line of `text` as (tags, problems). A line that starts with `// woodcore:` and cannot be read as a tag -- a kind that is none of KINDS, an object tag without its type and id, an id that is not an id -- is a problem and no tag. `object_types` restricts the calls an object tag may name; None allows any."""
    tags, problems = [], []
    for index, line in enumerate(_split(text)):
        found = _TAG_LINE.match(_strip(line).lstrip(chr(0xFEFF)) if index == 0 else _strip(line))      # a byte order mark is not part of the first line
        if found is None:
            continue
        kind, closing, words = found.group("kind"), bool(found.group("close")), found.group("rest").split()
        if kind not in KINDS:
            problems.append(Problem(index, f"`woodcore:{kind}` is not a kind of tag -- expected one of {', '.join(KINDS)}"))
            continue
        if kind == "structure":
            # the opening line carries a comment of its own after the kind; the closing one nothing
            if closing and words:
                problems.append(Problem(index, "the closing structure tag carries nothing after it"))
                continue
            tags.append(Tag(index, kind, closing))
            continue
        arity = 2 if (kind == "object" and not closing) else 1
        if len(words) != arity:
            what = "`woodcore:object <type> <id>`" if arity == 2 else f"`woodcore:{'/' if closing else ''}{kind} <id>`"
            problems.append(Problem(index, f"{_a(kind)} tag reads {what}"))
            continue
        ident = words[-1]
        if not ID_PATTERN.match(ident):
            problems.append(Problem(index, f"{ident!r} is not an id -- lower case, letters and digits parted by single hyphens"))
            continue
        call = words[0] if arity == 2 else None
        if call is not None and object_types is not None and call not in object_types:
            problems.append(Problem(index, f"{call!r} is not a parametric object -- expected one of {', '.join(object_types)}"))
            continue
        tags.append(Tag(index, kind, closing, ident, call))
    return tags, problems


def pair_tags(text, object_types=OBJECT_TYPES):
    """(blocks, problems) of `text`: every opening tag matched with its closing tag, and everything that does not match said.

    Reported: a tag that cannot be read (`scan_tags`); an opening tag never closed; a closing tag with nothing open, or naming another block than the innermost open one; a block inside one that may not hold it (`ALLOWED_INSIDE`); a structure block twice in a file, or an object id or a shared id twice -- an id is unique within its file. A closing tag that names a block further out unwinds to it, the blocks it cuts short reported unclosed, so one slip is one or two problems and not a cascade.
    """
    tags, problems = scan_tags(text, object_types)
    blocks, stack = [], []
    for tag in tags:
        if not tag.closing:
            if stack and tag.kind not in ALLOWED_INSIDE[stack[-1].kind]:
                parent = stack[-1]
                problems.append(Problem(tag.line, f"{_a(tag.kind)} tag cannot stand inside the {parent.kind} block opened at line {parent.line + 1}"))
            stack.append(tag)
            continue
        names = [i for i in range(len(stack) - 1, -1, -1) if stack[i].kind == tag.kind and stack[i].id == tag.id]
        if not stack or not names:
            what = tag.kind + (f" {tag.id}" if tag.id else "")
            inner = f"; the block open is {stack[-1].kind}{' ' + stack[-1].id if stack[-1].id else ''} (line {stack[-1].line + 1})" if stack else ""
            problems.append(Problem(tag.line, f"closes {what}, which is not open{inner}"))
            continue
        at = names[0]
        for cut in stack[at + 1:]:
            problems.append(Problem(cut.line, f"{cut.kind}{' ' + cut.id if cut.id else ''} is never closed before line {tag.line + 1}"))
        opening = stack[at]
        del stack[at:]
        blocks.append(Block(opening.kind, opening.id, opening.type, opening.line, tag.line))
    for tag in stack:
        problems.append(Problem(tag.line, f"{tag.kind}{' ' + tag.id if tag.id else ''} is never closed"))
    seen = {}
    for block in sorted(blocks, key=lambda b: b.start):
        key = (block.kind, block.id)
        if key in seen:
            what = "a structure block" if block.kind == "structure" else f"the {block.kind} id {block.id!r}"
            problems.append(Problem(block.start, f"{what} is used twice in one file (first at line {seen[key] + 1})"))
        else:
            seen[key] = block.start
    problems.sort(key=lambda p: p.line)
    return sorted(blocks, key=lambda b: b.start), problems


def check_tags(text, object_types=OBJECT_TYPES):
    """The problems `pair_tags` finds in `text`, as printable strings -- empty for a file Woodcore's editors may rewrite."""
    return [str(problem) for problem in pair_tags(text, object_types)[1]]


@dataclass(frozen=True)
class Heading:
    """One heading of a Typst file: its level as written, its title as written (the markup source, white space trimmed, a trailing label and a trailing comment left out), the line it starts on (0-based), its form -- `markup` for `= Title`, `call` for `#heading(…)` -- and `span`, where in the file the title's own text lies, which `set_title` rewrites. `span` is None where the title is not text Woodcore can rewrite, a variable for instance."""
    level: int
    title: str
    line: int
    form: str
    span: tuple = None


# A comment that ends a heading's line: `//`, but not the one of `https://`. And a label: `= Title <intro>`.
_COMMENT = re.compile(r"(?<!:)//")


_LABEL = re.compile(r"[ \t]*<[A-Za-z_][\w:.-]*>[ \t]*$")


_NAMED = re.compile(r"^([A-Za-z_][\w-]*)[ \t\r\n]*:[ \t\r\n]*")


CALL = "#heading"


def _skip_string(text, i):
    """The index after the string whose opening quote is at `i`."""
    n = len(text)
    i += 1
    while i < n:
        if text[i] == "\\":
            i += 2
        elif text[i] == '"':
            return i + 1
        else:
            i += 1
    return n


def _skip_content(text, i):
    """The index after the content block whose `[` is at `i`: brackets counted, `\\` escaping one, quotes being the smart quotes of markup and so nothing here."""
    n, depth = len(text), 0
    while i < n:
        c = text[i]
        if c == "\\":
            i += 2
            continue
        if c == "[":
            depth += 1
        elif c == "]":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    return n


def _arguments(text, open_at):
    """The arguments of the call whose `(` is at `open_at`, as ([(name, start, end)], the index after its `)`): `name` None for a positional argument, `start` and `end` the span of its value with white space trimmed."""
    n, i, depth = len(text), open_at + 1, 0
    args, begin = [], open_at + 1

    def add(stop):
        first, last = begin, stop
        while first < last and text[first].isspace():
            first += 1
        while last > first and text[last - 1].isspace():
            last -= 1
        if first == last:
            return
        named = _NAMED.match(text[first:last])
        args.append((named.group(1), first + named.end(), last) if named else (None, first, last))

    while i < n:
        c = text[i]
        if c == '"':
            i = _skip_string(text, i)
            continue
        if c == "[":
            i = _skip_content(text, i)
            continue
        if text.startswith("//", i):
            stop = text.find("\n", i)
            i = n if stop < 0 else stop
            continue
        if text.startswith("/*", i):
            stop = text.find("*/", i + 2)
            i = n if stop < 0 else stop + 2
            continue
        if c in "({":
            depth += 1
        elif c in ")}":
            if depth == 0:
                add(i)
                return args, i + 1
            depth -= 1
        elif c == "," and depth == 0:
            add(i)
            begin = i + 1
        i += 1
    add(n)
    return args, n


def _call_end(text, start):
    """The index after the `#name(...)[...]` chain that starts at `start`, found by running the lexer of typst_paths over it alone: a call with a string, a content block or a nested call in its arguments ends where Typst says it does."""
    lexer = typst_paths._Lexer(text)
    lexer.i = start
    opened = False
    while lexer.i < lexer.n:
        frame = lexer.stack[-1]
        getattr(lexer, "_" + frame[0])(frame)
        if len(lexer.stack) > 1:
            opened = True
        elif opened:
            break
    return lexer.i


def _block_end(text, start, end):
    """Where a heading in a content block stops: at the first `]` on its line that closes nothing opened in the title -- `[= Title]` is the heading «Title» and not «Title]»."""
    depth, i = 0, start
    while i < end:
        c = text[i]
        if c == "\\":
            i += 2
            continue
        if c == "[":
            depth += 1
        elif c == "]":
            if depth == 0:
                return i
            depth -= 1
        i += 1
    return end


class _HeadingLexer(typst_paths._Lexer):
    """The lexer of calc/typst_paths.py, which knows where markup is and where it is not, made to report the headings it passes instead of the paths.

    A heading is `=` and white space at the start of a line **of markup** -- the start of the file, the start of a content block, or after a line break -- or a `#heading` call at the start of one. The base lexer hands control to `_markup` whenever it is in markup; what this adds is that **at every entry and after every newline the line's start is looked at**: a line that follows an `#import` or a `#let` is the lexer's own code mode giving way to markup in the middle of a newline, which no search for `\\n` in plain text would ever see, and `#import "/commands.typ": *` followed by `= Title` is what every section file starts with. A comment, a raw block, a string and a formula are never markup, so a `=` in them is nothing.
    """

    def __init__(self, text):
        super().__init__(text)
        self.stack[0].append(True)              # the file starts a line; every markup frame carries "not yet looked at its start"
        self.headings = []
        self.seen = set()
        self.starts = [0] + [m.end() for m in re.finditer("\n", text)]

    def _push(self, kind, closer=None, flag=0):
        super()._push(kind, closer, flag)
        if kind == "markup":
            self.stack[-1].append(True)

    def _line(self, pos):
        return bisect.bisect_right(self.starts, pos) - 1

    def _markup(self, frame):
        text, i = self.text, self.i
        if frame[3]:
            frame[3] = False
            self._heading_at(i, frame)          # `[= Title]`: a block starts a line
        start = text.rfind("\n", 0, i) + 1
        if not text[start:i].strip(" \t"):
            self._heading_at(start, frame)      # only indentation before `i`: it is the start of a line
        stop = text.find("\n", i)
        end = self.n if stop < 0 else stop
        match = typst_paths._MARKUP_SPECIAL.search(text, i, end)
        if match is None:
            self.i = self.n if stop < 0 else stop + 1
            return
        if match.group() == "\\" and (match.start() + 1 == stop or (text.startswith("\r", match.start() + 1) and match.start() + 2 == stop)):
            self.i = stop + 1                   # a `\` line break: the next line starts a line
            return
        super()._markup(frame)

    def _heading_at(self, pos, frame):
        text, n = self.text, self.n
        p = pos
        while p < n and text[p] in " \t":
            p += 1
        if p >= n or p in self.seen:
            return
        if text[p] == "=":
            q = p
            while q < n and text[q] == "=":
                q += 1
            if q < n and text[q] not in " \t\r\n":
                return                          # `=foo` and `==>` are text
            self.seen.add(p)
            stop = text.find("\n", q)
            stop = n if stop < 0 else stop
            if stop > q and text[stop - 1] == "\r":
                stop -= 1
            start = q
            while start < stop and text[start] in " \t":
                start += 1
            end = stop
            if frame[1] == "]":
                end = _block_end(text, start, end)      # `[= Title]`: the block's bracket closes the heading
            comment = _COMMENT.search(text, start, end)
            if comment:
                end = comment.start()
            label = _LABEL.search(text, start, end)
            if label:
                end = label.start()
            while end > start and text[end - 1] in " \t":
                end -= 1
            self.headings.append(Heading(q - p, text[start:end], self._line(p), "markup", (start, end)))
        elif text.startswith(CALL, p) and p + len(CALL) < n and text[p + len(CALL)] in "([":
            self.seen.add(p)
            self._call(p)

    def _call(self, p):
        """The `#heading(level: 2, "Title")`, `#heading(level: 2)[Title]` or `#heading[Title]` at `p`."""
        text = self.text
        end = _call_end(text, p)
        i = p + len(CALL)
        args, after = [], i
        if text[i] == "(":
            args, after = _arguments(text, i)
            after = min(after, end)
        named = {name: (s, e) for name, s, e in args if name}
        positional = [(s, e) for name, s, e in args if name is None]
        level = None
        for key in ("level", "depth"):
            if key in named and text[named[key][0]:named[key][1]].isdigit():
                level = int(text[named[key][0]:named[key][1]])
                break
        body = positional[0] if positional else None
        if body is None and after < len(text) and text[after] == "[":
            body = (after, _skip_content(text, after))
        title, span = "", None
        if body is not None:
            s, e = body
            raw = text[s:e]
            if raw.startswith('"') and _skip_string(text, s) == e:
                span, title = (s + 1, e - 1), typst_paths._unescape(text[s + 1:e - 1])
            elif raw.startswith("[") and _skip_content(text, s) == e:
                s, e = s + 1, e - 1
                while s < e and text[s].isspace():
                    s += 1
                while e > s and text[e - 1].isspace():
                    e -= 1
                span, title = (s, e), text[s:e]
            else:
                title = raw
        self.headings.append(Heading(level or 1, title.strip(), self._line(p), "call", span))


def scan_headings(text):
    """The headings of a Typst file in document order, as `Heading`s.

    `= Title`, `== Title`, … at the start of a line of markup, and `#heading(level: n, …)` at the start of one, outside comments, raw blocks, strings and formulas -- found by the lexer of calc/typst_paths.py, the one scanner of Typst this project has. A heading in a content block (`#if … [`) is found as well: it is in the document whenever the condition holds. The title is what is written, markup included; `plain_title` reduces it to the words Typst prints.
    """
    shift = 1 if text.startswith("\ufeff") else 0
    lexer = _HeadingLexer(text[shift:])
    lexer.run()
    if not shift:
        return lexer.headings
    return [Heading(h.level, h.title, h.line, h.form, (h.span[0] + shift, h.span[1] + shift) if h.span else None) for h in lexer.headings]


def flatten(nodes):
    """The nodes of `nodes` and of their subtrees, in document order (a node before its children), each once -- so the tree `tree` returns and a flat list of its nodes both give the same."""
    seen, out = set(), []

    def visit(items):
        for node in items:
            if id(node) in seen:
                continue
            seen.add(id(node))
            out.append(node)
            visit(node.children)

    visit(nodes)
    return out


Bookmark = namedtuple("Bookmark", "level title page y")


Bookmark.__doc__ = "One bookmark of a compiled PDF: its level as Typst counts a heading's (1 at the top of the outline), its title, its page (0-based) and where on the page it points (`y`, in points from the page's top edge; None where the PDF says none). The same four fields, in the same order and with the same meanings, as calc/tools/pdf_pane.py's Bookmark, so the outline the pane reads from its document and the one `bookmarks_from_pdf` reads from the file are interchangeable."


def _bookmark(item):
    """`item` as a `Bookmark`: one already, any 4-tuple (level, title, page, y) -- pdf_pane's Bookmark is one --, or an object with those four attributes (y optional)."""
    if isinstance(item, Bookmark):
        return item
    if isinstance(item, (tuple, list)):
        return Bookmark(*item[:4])
    return Bookmark(item.level, item.title, item.page, getattr(item, "y", None))


_TYPOGRAPHY = str.maketrans({
    "\u201c": '"', "\u201d": '"', "\u201e": '"', "\u00ab": '"', "\u00bb": '"', "\u2018": "'", "\u2019": "'",
    "\u2013": "-", "\u2014": "-", "\u2212": "-", "\u00a0": " ", "\u202f": " ", "\u2009": " ", "~": " ",
})


_EMPHASIS = re.compile(r"(?<!\\)\*|(?<![\w\\])_|_(?!\w)|`")


_NUMBERING = re.compile(r"^(?:\d+(?:\.\d+)*[.)]?|[A-Za-z][.)]|[IVXLCDMivxlcdm]+\.) +(?=\S)")


def plain_title(text):
    """The words a heading prints, from its markup source: emphasis and raw marks dropped, escapes resolved, the typography Typst sets (smart quotes, dashes, non-breaking spaces) written back as the plain characters -- so that a title as written in the file and the same title as the PDF's outline has it compare equal."""
    text = _EMPHASIS.sub("", text)
    text = re.sub(r"\\(.)", r"\1", text, flags=re.S)
    text = text.replace("---", "-").replace("--", "-").replace("\u2026", "...")
    return text.translate(_TYPOGRAPHY)


def normalize_title(text):
    """A title as `align` compares it: `plain_title`, any leading numbering taken off -- «1.2 », «3) », «A. » -- as many times as there are, white space collapsed, case folded. The PDF's outline carries the numbering Typst gives a heading and the file does not, and a title that itself starts with a number loses it on both sides."""
    text = " ".join(plain_title(text).split())
    while True:
        stripped = _NUMBERING.sub("", text, count=1)
        if stripped == text:
            break
        text = stripped
    return text.casefold()


def align(nodes, bookmarks):
    """The nodes of a tree mapped to the bookmarks of its compiled PDF: {node id: Bookmark}.

    `nodes` is what `tree` returns -- or any list of its nodes -- and `bookmarks` the outline of the PDF in document order: `Bookmark`s, (level, title, page, y) tuples or objects with those attributes, from `bookmarks_from_pdf` or from the pane (calc/tools/pdf_pane.py), which read the same outline. The result holds the bookmarks as `Bookmark`s, y as it was given. Only the nodes that are printed (`active`) are looked for: a disabled section is not in the PDF. Both lists are in document order and the match is **greedy** -- each node takes the next bookmark, from the one after the last matched, whose level is its own and whose normalised title is its own (`normalize_title`), and where none has its level, the next with its title at any level (Typst nests a level-3 heading that follows a level-1 at depth 2). **A bookmark no node takes is skipped**: the headings the engine prints itself -- «Inhaltsverzeichnis», the heading of a calculation, the bibliography's -- are in the PDF and in no file. A node no bookmark has is left out of the result; nothing is raised. **A heading object maps like a heading** -- the first heading of a file, which is the file's own, to the bookmark of its file -- and **any other object** (a paragraph, a table …) **has none**.
    """
    marks = [_bookmark(b) for b in bookmarks]
    keyed = [(m.level, normalize_title(m.title)) for m in marks]
    found, at, by_id = {}, 0, {}
    for node in flatten(nodes):
        by_id[node.id] = node
        if not node.active:
            continue
        if node.kind == "object":
            # A heading is an object of its file: it has a bookmark. The file's first heading is the file's own, and takes the bookmark its file did; any other object is no heading and has none.
            if node.object_type != "heading":
                continue
            owner = by_id.get(node.parent)
            if owner is not None and owner.kind == "file" and owner.line is not None and owner.line == node.line and owner.id in found:
                found[node.id] = found[owner.id]
                continue
        key = normalize_title(node.title)
        if not key:
            continue
        hit = next((j for j in range(at, len(marks)) if keyed[j] == (node.level, key)), None)
        if hit is None:
            hit = next((j for j in range(at, len(marks)) if keyed[j][1] == key), None)
        if hit is None:
            continue
        found[node.id] = marks[hit]
        at = hit + 1
    return found


def bookmarks_from_pdf(source, from_bottom=False):
    """The outline of a PDF as `Bookmark`s in document order: [(level, title, page, y)], level 1 at the top of the outline -- the level of the heading as Typst counts it --, page 0-based, `y` where the bookmark points on the page in points **from the page's top edge**, as the pane's bookmarks have it. The PDF itself states it from the bottom, which is what `from_bottom` gives back. A bookmark with no page is left out.

    `source` is a path, the bytes of the file or an open binary file: the file is read whole and closed at once, so nothing holds a Windows file handle on a PDF that is about to be compiled again.
    """
    from pypdf import PdfReader
    if isinstance(source, (bytes, bytearray)):
        data = bytes(source)
    elif hasattr(source, "read"):
        data = source.read()
    else:
        data = Path(source).read_bytes()
    reader = PdfReader(io.BytesIO(data))
    found = []

    def walk(items, depth):
        for item in items:
            if isinstance(item, list):
                walk(item, depth + 1)
                continue
            try:
                page = reader.get_destination_page_number(item)
            except Exception:  # broad: pypdf raises a family of its own -- a bookmark that cannot be followed is left out, the others kept
                continue
            if page is None or page < 0:
                continue
            top = item.top
            y = float(top) if isinstance(top, (int, float)) else None
            if y is not None and not from_bottom:
                y = float(reader.pages[page].mediabox.height) - y
            found.append(Bookmark(depth, str(item.title), page, y))

    walk(reader.outline, 1)
    return found
