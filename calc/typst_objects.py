"""The parametric objects of a document's .typ files, read and written back (the three document modes, work package 4.1).

A parametric object is one call of lib/document.typ -- a table, the live loads, a field, a list to tick, a choice, a picture, a plan extract, the signatures, the norms a section names -- written between two tag lines of a section file:

    // woodcore:object live-load-table live-loads
    #live-load-table(
      hidden: ("zone",),
      rows: (
        (storey: [EG], use: [Büro], category: "B", q_k: auto, Q_k: auto),
      ),
    )
    // woodcore:/object live-loads

**Every heading and every paragraph is an object too** (the rework of 01.10.2026): `// woodcore:object heading title` around one markup heading line, `= Titel` (any level), and `// woodcore:object text intro` around one paragraph of markup -- its lines, no blank line between them. Their body is **the markup itself and no call**: `Object.call` is None, the editors' models are `HeadingModel` (a level and a title) and `TextModel` (the paragraph as written), their `to_body()` is what is written back, and `write_object`, `insert_object` and `default_body` take the body as a string. `tag_file` wraps every untagged top-level heading and paragraph of a file in these tags, once and for all (it is what «Baliser ce fichier» does on a report's file), and writes the same text when it is run again.

**The .typ file is the source of truth.** Nothing about an object is kept anywhere else: Woodcore finds it by its tags (calc/structure.py's `pair_tags`, the one reader of the tags), parses the call between them, lets the engineer edit it, and writes the call back between the same two tags -- **only there**, every byte outside the body kept, line endings included (`write_object`).

**The canonical form** is the one Woodcore writes (`serialize`): one named argument per line, two spaces of indent, a trailing comma after every argument, the arguments in the fixed order of the command's signature (ORDER, the signatures of lib/document.typ); the entries of `columns`, `rows`, `options`, `keys` and `notes` one per line (LIST_ARGUMENTS) -- a row of a table on one line, its dictionary inline -- and so an array of dictionaries or of arrays wherever it stands, and any other array inline where its line fits in LINE_WIDTH characters, one element per line where it does not; a one-element array `("x",)`, an empty one `()`, an empty dictionary `(:)`.

**What was edited by hand is told apart without a hash** (`Object.state`): the body is `canonical` where serializing what it parses to gives it back exactly (line endings normalised), `hand_edited` where it parses and does not come back -- a comment, an argument out of order, a row broken over two lines, an argument the command does not take; a heading written as `#heading(...)`, a paragraph with a blank line round it -- and `unreadable` where it does not parse, or the call is not the one the tag names; **a heading or a paragraph is unreadable where no model can be made of it**: it holds nothing, more than a heading, or more than one paragraph (a blank line, a heading line). A markup object is never replaced by a default on the way: where it cannot be read, `Object.canonical` is the body as it is. Woodcore writes a canonical object back silently; a hand-edited one only once the engineer has been warned that his version will be rewritten in Woodcore's form (`write_object(..., force=True)`, `Object.diff()`); an unreadable one is replaced by the type's defaults (`default_call`) under the same id.

**The values** are the literals of Typst's code: a string (written with the escapes `\\\\`, `\\"`, `\\n` and `\\r` only), an integer, a float (its shortest representation), `true`, `false`, `none`, `auto` (AUTO), a length or a ratio or an angle (Length: `80%`, `12pt`, `1.5cm`), an array (a Python list), a dictionary (a Python dict, its order kept), and **content** -- `[...]`, kept as the markup between its brackets and never looked into (Content): `[#doc-value("g_k", domain: ("dead-load", "D1"))]` and `[$q_k$ [kN/m²]]` are read to their closing bracket by the lexer of calc/typst_paths.py, which knows where a string, a raw block, a formula or a comment stops. An argument that is none of these -- `width: 50% + 1cm`, `rows: my-rows` -- is kept as the code it is written as (Expr) and written back verbatim, so an expression the engineer wrote survives an edit of the object around it; the editors refuse to edit an argument that is one (ModelError).

**The editors' models** (`TableModel`, `LiveLoadTableModel`, `ChoiceModel`, `ChecklistModel`, `SignaturesModel`, `NormListModel`, `FieldModel`, `ImageModel`, `PlanModel`, `ExtractModel`, `AnnexesModel`; `model_for`) sit over one call each and give the operations the right pane offers -- a row or a column added, moved, removed, a column hidden, a cell set, a category chosen, a value written over and taken back -- and `to_call()` gives the call back to be written. A model keeps every argument the call had and adds one only where it differs from the command's default, so a call read and written back unchanged is the call it was.

Qt-free and standard library only.
"""

import copy
import difflib
import math
import re
import unicodedata
from dataclasses import dataclass, field

import structure
import typst_paths
from typst_objects_parse import (  # split out of this module (issue #30): every name it had is still importable from it
    AUTO,
    CALL_TYPES,
    Call,
    Content,
    Expr,
    LINE_WIDTH,
    LIST_ARGUMENTS,
    Length,
    MARKUP_TYPES,
    ORDER,
    ObjectError,
    PLACEHOLDER,
    ParseError,
    RESERVED,
    SHEET_SIGNATURES,
    SHEET_TYPES,
    SHOW_RULES,
    SIGNATURES,
    UNITS,
    _Auto,
    _ESCAPES,
    _IDENT,
    _KEYWORDS,
    _NOT,
    _NUMBER,
    _Parser,
    _SHOW_RULE,
    _WORD_CHAR,
    _argument,
    _as_call,
    _dict_key,
    _float,
    _normalise,
    _number,
    _parameters,
    _string,
    arguments_of,
    content,
    default_call,
    inline,
    length,
    parse_call,
    parse_call_at,
    parse_value,
    same,
    serialize,
    signatures_in,
    variable_cell,
)
from typst_objects_models import (  # split out of this module (issue #30): every name it had is still importable from it
    AnnexesModel,
    CHECK_OPTION_KEYS,
    CHOICE_OPTION_KEYS,
    COLUMN_KEYS,
    COLUMN_KINDS,
    ChecklistModel,
    ChoiceModel,
    Column,
    DEFAULTS,
    ExtractModel,
    FieldModel,
    FirePlanModel,
    ImageModel,
    KNOWN_COLUMNS,
    LIVE_LOAD_FILLED,
    LiveLoadTableModel,
    Model,
    ModelError,
    NormListModel,
    PlanModel,
    SIGNATURE_KEYS,
    SignaturesModel,
    TableModel,
    _COLUMN_ID,
    _KEEP,
    _Options,
    _bool_value,
    _drop,
    _id_value,
    _index,
    _move,
    _number_value,
    _put,
    _text_value,
    _width_value,
)
from typst_objects_sheets import (  # split out of this module (issue #30): every name it had is still importable from it
    FireLegendModel,
    FireViewportModel,
    HEADING_LEVELS,
    HeadingModel,
    LegendModel,
    PositionListModel,
    QuantitiesModel,
    SHEET_FORMATS,
    SHEET_KINDS,
    SHEET_SIZES,
    SectionModel,
    SheetPageModel,
    SheetTextModel,
    TextModel,
    TitleBlockModel,
    ViewportModel,
    _BLANK,
    _Checked,
    _Drawing,
    _HEADING_MARKUP,
    _Placed,
    _balanced,
    _heading_parts,
    _level_value,
    _mm,
    _paragraph_value,
    _title_value,
    mm_of,
)


# --- the commands --------------------------------------------------------------------------


DOCUMENT_TYPES = CALL_TYPES + MARKUP_TYPES
OBJECT_TYPES = DOCUMENT_TYPES + SHEET_TYPES


KNOWN_UNITS = {"q_k": "kN/m²", "Q_k": "kN", "load": "kN/m²"}


START = "// woodcore:object"
END = "// woodcore:/object"


# --- values ----------------------------------------------------------------------------------


# --- parsing ---------------------------------------------------------------------------------


# --- writing -----------------------------------------------------------------------------------


# --- objects in a file ---------------------------------------------------------------------------

STATES = ("canonical", "hand_edited", "unreadable")

# The codes of an ObjectError, which a window turns into its own words.
CODES = ("bad_type", "bad_id", "id_exists", "no_such_object", "tags", "type_mismatch", "hand_edited", "unreadable",
         "changed", "bad_line", "inside_block", "tag_in_body", "not_written", "bad_body")


def _lines(text):
    return re.findall(r"[^\r\n]*(?:\r\n|\r|\n)|[^\r\n]+", text)


def _ending(line):
    return line[len(line.rstrip("\r\n")):]


def _newline_of(text):
    """The line ending a file writes: the first one it has, `\\n` where it has none."""
    found = re.search(r"\r\n|\r|\n", text)
    return found.group() if found else "\n"


@dataclass(frozen=True)
class Object:
    """One parametric object of a file: its type and id (the tag's), the lines of its two tags (0-based), where its body lies in the file's text (`body_span`, character offsets: the lines between the tags, the last one's line ending left out) and the body as written. `state` is canonical, hand_edited or unreadable; `call` is what the body parses to (None where it is unreadable, `error` then saying why); `shared` the id of the shared block it stands in, or None.

    **A heading (`heading`) and a paragraph (`text`) are objects whose body is markup and no call**: `markup` is then True, `call` is None whatever the state, and `model()` reads the body (a HeadingModel, a TextModel)."""
    type: str
    id: str
    start: int
    end: int
    body_span: tuple
    body: str
    state: str
    call: Call = None
    error: str = None
    shared: str = None

    @property
    def markup(self):
        """Whether the body is markup -- a heading, a paragraph -- and not the call of a command."""
        return self.type in MARKUP_TYPES

    @property
    def written(self):
        """The body with its line endings made `\\n`: what the canonical form is compared with."""
        return _normalise(self.body)

    @property
    def canonical(self):
        """What Woodcore would write in place of the body: the canonical form of its call, or of the type's defaults where the body cannot be read -- for a heading or a paragraph the body as its model writes it, and the body as it is where no model can read it."""
        return self.replacement() if self.markup else serialize(self.replacement())

    def replacement(self):
        """The call Woodcore writes here where the engineer edits nothing: the body's own call, or the type's defaults (`default_call`) where it is unreadable. For a heading or a paragraph, the **body** that is written, a string: the model's own, or the body as it is where it cannot be read -- markup is never replaced by a default."""
        if self.markup:
            try:
                return model_for_body(self.type, self.written).to_body()
            except ModelError:
                return self.written
        return self.call if self.state != "unreadable" else default_call(self.type)

    def model(self):
        """The editor's model of the object -- `model_for` of its call, a HeadingModel or a TextModel for markup -- or a ModelError where it cannot be edited (unreadable)."""
        if self.markup:
            return model_for_body(self.type, self.written)
        if self.call is None:
            raise ModelError("unreadable", self.error or "the object cannot be read")
        return model_for(self.call)

    def diff(self):
        """A unified diff from the body as written to what Woodcore would write -- empty for a canonical object: what the warning before a hand-written object is overwritten shows."""
        if self.state == "canonical":
            return ""
        before = self.written.split("\n")
        after = self.canonical.split("\n")
        return "\n".join(difflib.unified_diff(before, after, "as written", "as Woodcore writes it", lineterm=""))


def _state(kind, body):
    """(state, call, error) of a body under a tag naming `kind`."""
    text = _normalise(body)
    if kind in MARKUP_TYPES:
        try:
            model = model_for_body(kind, text)
        except ModelError as exc:
            return "unreadable", None, str(exc)
        return ("canonical" if model.to_body() == text else "hand_edited"), None, None
    try:
        found = parse_call(text)
    except ParseError as exc:
        return "unreadable", None, str(exc)
    if found.type != kind:
        return "unreadable", None, f"the tag names {kind} and the body calls #{found.type}"
    try:
        written = serialize(found)
    except ValueError as exc:
        return "unreadable", None, str(exc)
    return ("canonical" if written == text else "hand_edited"), found, None


def scan(text):
    """(objects, problems) of a file's text: every object whose two tags pair (calc/structure.py's `pair_tags`, in the order they are written) and every problem with the tags. A file with a problem is one Woodcore's editors do not rewrite (`write_object` refuses it); its objects are still read."""
    blocks, problems = structure.pair_tags(text)
    lines = _lines(text)
    offsets = [0]
    for line in lines:
        offsets.append(offsets[-1] + len(line))
    shared = [b for b in blocks if b.kind == "shared"]
    found = []
    for block in blocks:
        if block.kind != "object":
            continue
        begin = offsets[block.start + 1]
        if block.end == block.start + 1:
            finish = begin
        else:
            last = lines[block.end - 1]
            finish = offsets[block.end - 1] + len(last) - len(_ending(last))
        body = text[begin:finish]
        state, call, error = _state(block.type, body)
        around = next((s.id for s in shared if s.start < block.start and block.end < s.end), None)
        found.append(Object(block.type, block.id, block.start, block.end, (begin, finish), body, state, call, error, around))
    return found, problems


def objects(text):
    """Every object of a file's text, in the order they are written (`scan`, the problems left out)."""
    return scan(text)[0]


def find(text, object_id):
    """The object of id `object_id` in a file's text, or None."""
    return next((o for o in objects(text) if o.id == object_id), None)


def free_id(text, base):
    """An object id not used in a file's text, made from `base` (`table`, `live-loads`): the base itself where it is free, else `<base>-2`, `<base>-3`, …"""
    if not structure.ID_PATTERN.match(base):
        raise ObjectError("bad_id", f"{base!r} is not an id -- lower case, letters and digits parted by single hyphens", id=base)
    used = {b.id for b in structure.pair_tags(text)[0] if b.kind == "object"}
    candidate, n = base, 2
    while candidate in used:
        candidate, n = f"{base}-{n}", n + 1
    return candidate


def _markup_body(value, kind):
    """The body of a heading or a paragraph written from `value` -- its text (a string) or its model (HeadingModel, TextModel) -- refused (ObjectError `bad_body`) where it is no such heading or paragraph, and where it is a call."""
    if isinstance(value, Call):
        raise ObjectError("type_mismatch", f"the tag names {kind}, which is markup, and the value is the call #{value.type}", type=kind, call=value.type)
    try:
        if isinstance(value, (HeadingModel, TextModel)):
            if value.type != kind:
                raise ObjectError("type_mismatch", f"the tag names {kind} and the model is a {value.type}'s", type=kind, call=value.type)
            return value.to_body()
        if isinstance(value, str):
            return model_for_body(kind, value).to_body()
    except ModelError as exc:
        raise ObjectError("bad_body", f"the {kind} cannot be written: {exc}", type=kind, reason=exc.values.get("reason")) from None
    raise ObjectError("not_written", f"a {kind} is written from its text or its model -- got {value!r}", type=kind)


def suggest_id(text, kind, body=None):
    """An id for a new object of `kind` in the file `text`, free in it: made of the words of the heading or the paragraph it is to hold (`body`, markup as written -- `einleitung`, `die-bemessung-der`), the command's own name for a call (`doc-table`), `heading` or `text` where there is nothing to make it of; `-2`, `-3` … after it where another object has it. Only a proposal: it is what `insert_object` takes."""
    if kind not in OBJECT_TYPES:
        raise ObjectError("bad_type", f"{kind!r} is not a parametric object -- expected one of {', '.join(OBJECT_TYPES)}", type=kind)
    if kind in MARKUP_TYPES:
        base = _id_base(Untagged(kind, 0, 0, body or "", 1 if kind == "heading" else None), 1, "slug")
    else:
        base = kind
    return free_id(text, base)


def _checked_body(call, kind):
    """The canonical form of `call`, refused where it is not a call of `kind`, where it would not read back as itself, or where a line of it would read as a tag. For a heading or a paragraph `call` is its body (a string) or its model, and the body is what comes back."""
    if kind in MARKUP_TYPES:
        return _markup_body(call, kind)
    if not isinstance(call, Call):
        raise ObjectError("not_written", f"an object is written from a Call -- got {call!r}")
    if call.type != kind:
        raise ObjectError("type_mismatch", f"the tag names {kind} and the call is #{call.type}", type=kind, call=call.type)
    try:
        body = serialize(call)
    except ValueError as exc:
        raise ObjectError("not_written", f"the call of {kind} cannot be written: {exc}", type=kind) from None
    tags, problems = structure.scan_tags(body, None)
    if tags or problems:
        raise ObjectError("tag_in_body", "a line of the object would read as a `// woodcore:` tag -- a content block holds one", type=kind)
    back = parse_call(body)
    if not back.same_as(Call(call.type, {n: call.args[n] for n in arguments_of(call)})):
        raise ObjectError("not_written", f"the call of {kind} would not read back as itself once written", type=kind)
    return body


def _readable(text):
    found, problems = scan(text)
    if problems:
        raise ObjectError("tags", "Woodcore cannot read the tags of this file, so it does not rewrite it -- " + "; ".join(str(p) for p in problems),
                          problems=[str(p) for p in problems])
    return found


def write_object(text, object_id, call, *, force=False, expected=None):
    """`text` with the body of object `object_id` replaced by the canonical form of `call`, and **nothing else changed**: every byte outside the body is kept, the body is written with the line ending of the object's start tag, and a second call with the same `call` writes the same text. For a heading or a paragraph `call` is the new body, a string (`= Titel`, the paragraph's markup) or a HeadingModel or a TextModel.

    Refused (ObjectError, CODES): a file whose tags cannot be read, an id with no object, a call that is not of the type the tag names; a body written by hand (`hand_edited`) or one that cannot be read (`unreadable`) unless `force` -- the engineer having been told, with `Object.diff()`, that his version will be rewritten or replaced; and, where `expected` is given (the body as the editor loaded it), a body that has changed since.
    """
    found = _readable(text)
    target = next((o for o in found if o.id == object_id), None)
    if target is None:
        raise ObjectError("no_such_object", f"the file holds no object {object_id!r}" + (f" -- its objects are {', '.join(o.id for o in found)}" if found else ""), id=object_id)
    body = _checked_body(call, target.type)
    if expected is not None and _normalise(expected) != target.written:
        raise ObjectError("changed", f"the object {object_id!r} has been changed since it was loaded", object=target, id=object_id)
    if target.state != "canonical" and not force:
        what = "was edited by hand and would be rewritten in Woodcore's form" if target.state == "hand_edited" else "cannot be read and would be replaced"
        raise ObjectError(target.state, f"the object {object_id!r} {what} -- write it with force=True once that is said", object=target, id=object_id)
    lines = _lines(text)
    newline = _ending(lines[target.start]) or _newline_of(text)
    new_body = body.replace("\n", newline)
    begin, finish = target.body_span
    if target.end == target.start + 1:
        new_body += newline     # no line between the tags: the body takes a line of its own before the closing tag
    return text[:begin] + new_body + text[finish:]


def insert_object(text, after_line, kind, object_id, call=None):
    """`text` with a new object of `kind` and id `object_id` inserted after line `after_line` (0-based; -1 puts it before the first line): its start tag, the canonical form of `call` (the type's defaults where None; for a heading or a paragraph its body, a string or a model, `= […]` and `[…]` where None) and its end tag, each on a line of its own, in the file's line ending. Everything else is kept byte for byte.

    Refused: a file whose tags cannot be read, a kind that is no parametric object, an id that is not an id or that another object of the file carries, a line that is not in the file, and a place inside an object or the generated structure block -- an object stands in markup, beside another or inside a shared block.
    """
    if kind not in OBJECT_TYPES:
        raise ObjectError("bad_type", f"{kind!r} is not a parametric object -- expected one of {', '.join(OBJECT_TYPES)}", type=kind)
    if not isinstance(object_id, str) or not structure.ID_PATTERN.match(object_id):
        raise ObjectError("bad_id", f"{object_id!r} is not an id -- lower case, letters and digits parted by single hyphens", id=object_id)
    _readable(text)
    blocks = structure.pair_tags(text)[0]
    if any(b.kind == "object" and b.id == object_id for b in blocks):
        raise ObjectError("id_exists", f"another object of the file is called {object_id!r} -- an id names one object in its file", id=object_id)
    if call is None:
        call = default_body(kind) if kind in MARKUP_TYPES else default_call(kind)
    body = _checked_body(call, kind)
    lines = _lines(text)
    if not isinstance(after_line, int) or isinstance(after_line, bool) or not -1 <= after_line < len(lines):
        raise ObjectError("bad_line", f"line {after_line!r} is not in the file (0-based, -1 before the first)", line=after_line)
    for block in blocks:
        if block.kind in ("object", "structure") and block.start <= after_line < block.end:
            raise ObjectError("inside_block", f"line {after_line + 1} lies inside the {block.kind} block of lines {block.start + 1}-{block.end + 1}", line=after_line)
    newline = _newline_of(text)
    new = f"{START} {kind} {object_id}{newline}" + body.replace("\n", newline) + f"{newline}{END} {object_id}{newline}"
    head = "".join(lines[:after_line + 1])
    if head and not _ending(head):
        head += newline         # the last line had no line ending of its own
    return head + new + "".join(lines[after_line + 1:])


def remove_object(text, object_id):
    """`text` without object `object_id`: its two tag lines and everything between them. Refused where the file's tags cannot be read or there is no such object."""
    found = _readable(text)
    target = next((o for o in found if o.id == object_id), None)
    if target is None:
        raise ObjectError("no_such_object", f"the file holds no object {object_id!r}", id=object_id)
    lines = _lines(text)
    return "".join(lines[:target.start] + lines[target.end + 1:])


# --- the editors' models -------------------------------------------------------------------------


# --- the objects of an export sheet (lib/sheet.typ, v0.114) --------------------------------------


# --- a heading and a paragraph: objects whose body is markup --------------------------------------


MARKUP_MODELS = {"heading": HeadingModel, "text": TextModel}


def default_body(kind):
    """The body Woodcore writes for a new heading or paragraph: `= […]`, `[…]` -- the mark a text still to be written carries (lib/document.typ's doc-placeholder)."""
    if kind not in MARKUP_TYPES:
        raise ObjectError("bad_type", f"{kind!r} is not a markup object -- expected one of {', '.join(MARKUP_TYPES)}", type=kind)
    return MARKUP_MODELS[kind]().to_body()


def model_for_body(kind, body):
    """The model of a heading or a paragraph read from its body (a string), or a ModelError where there is none -- `reason` in its `values` says why: empty, several, not_a_heading, heading_in_text, unbalanced, level."""
    if kind not in MARKUP_MODELS:
        raise ModelError("wrong_type", f"{kind!r} is not a markup object -- expected one of {', '.join(MARKUP_TYPES)}")
    return MARKUP_MODELS[kind].from_body(body)


def model_of(item):
    """The editor's model of an `Object` (whatever it is: a call's model, a HeadingModel, a TextModel) or of a `Call` -- a ModelError where the object cannot be read."""
    if isinstance(item, Object):
        return item.model()
    return model_for(item)


MODELS = {
    "doc-table": TableModel,
    "live-load-table": LiveLoadTableModel,
    "dead-load-table": TableModel,
    "doc-field": FieldModel,
    "doc-checklist": ChecklistModel,
    "doc-choice": ChoiceModel,
    "doc-image": ImageModel,
    "doc-plan": PlanModel,
    "doc-fire-plan": FirePlanModel,
    "doc-extract": ExtractModel,
    "doc-annexes": AnnexesModel,
    "doc-signatures": SignaturesModel,
    "show-norm-list": NormListModel,
    "sheet-page": SheetPageModel,
    "sheet-text": SheetTextModel,
    "sheet-viewport": ViewportModel,
    "sheet-section": SectionModel,
    "sheet-legend": LegendModel,
    "sheet-fire-viewport": FireViewportModel,
    "sheet-fire-legend": FireLegendModel,
    "sheet-position-list": PositionListModel,
    "sheet-quantities": QuantitiesModel,
    "sheet-titleblock": TitleBlockModel,
}


def model_for(call):
    """The editor's model of `call`, by its type."""
    kind = getattr(call, "type", None)
    if kind not in MODELS:
        raise ModelError("wrong_type", f"{kind!r} is not a call of lib/document.typ or lib/sheet.typ -- expected one of {', '.join(CALL_TYPES + SHEET_TYPES)}")
    return MODELS[kind](call)


# --- a short label for an object ---------------------------------------------------------------------

_LABEL_TAIL = re.compile(r"[ \t]*<[A-Za-z_][\w:.-]*>[ \t]*$")


def _plain(markup):
    """The words of a piece of markup, for a label: formulas and the calls of the engine left out, emphasis marks and escapes taken off, white space collapsed."""
    text = re.sub(r"\$[^$]*\$", " ", markup)
    text = re.sub(r"#[A-Za-z_][\w.-]*(?:\((?:[^()]|\([^()]*\))*\))?(?:\[[^\]]*\])?", " ", text)
    return " ".join(structure.plain_title(text).split())


def _clip(text, limit):
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0] if " " in text[:limit] else text[:limit]
    return cut.rstrip(" ,;:.-") + chr(0x2026)


def object_title(obj, limit=60):
    """A short label for an object, for the tree and its rows: a heading's own title (its label and comment left out, its markup reduced to the words Typst prints -- never cut, the PDF's outline carries it whole), the first words of a paragraph, a table's or a picture's caption, a field's, a list's or a choice's label -- and the id where the body says nothing readable. At most `limit` characters, cut at a word and ended with an ellipsis."""
    if obj.type == "heading":
        try:
            title = _LABEL_TAIL.sub("", structure._COMMENT.split(model_for_body("heading", obj.written).title)[0])
        except ModelError:
            return obj.id
        return _plain(title) or title.strip() or obj.id
    if obj.type == "text":
        return _clip(_plain(obj.written) or obj.id, limit)
    call = obj.call
    if call is not None:
        for key in ("caption", "label", "body", "title"):
            value = call.args.get(key)
            if isinstance(value, Content):
                words = _plain(value.markup)
            elif isinstance(value, str):
                words = value.strip()
            else:
                words = ""
            if words and words != PLACEHOLDER:
                return _clip(words, limit)
        for key in ("file", "plan"):
            value = call.args.get(key)
            if isinstance(value, str) and value:
                return _clip(value, limit)
    return obj.type


# --- tagging a file that has no tags --------------------------------------------------------------------

@dataclass(frozen=True)
class Untagged:
    """A heading or a paragraph of a file that stands outside every object tag: its `kind` (`heading`, `text`), the lines it covers (`start` and `end`, 0-based, both included) and its `text`, those lines with LF endings -- for a heading its `level`."""
    kind: str
    start: int
    end: int
    text: str
    level: int = None


class _TopLines(structure._HeadingLexer):
    """The heading lexer of calc/structure.py, which also notes every line that starts **at the top of the file's own markup** -- not inside a call, a content block, a formula, a raw block or a comment, where a blank line or a line of text means nothing about the document's paragraphs."""

    def __init__(self, text):
        super().__init__(text)
        self.top = set()

    def _markup(self, frame):
        if len(self.stack) == 1:
            i = self.i
            start = self.text.rfind("\n", 0, i) + 1
            if not self.text[start:i].strip(" \t\r"):
                self.top.add(self._line(start))
        super()._markup(frame)


def _is_code(unit):
    """Whether the unit that starts with `#` is code and not a paragraph that happens to begin with a call: a statement (`#import`, `#set`, `#let`, `#for`, …), a block, or one expression and nothing after it on its lines -- `#show-calc(…)`, `#figure(…)`, `#v(1em)`."""
    found = re.match(r"#([A-Za-z_][\w-]*)", unit)
    if found is None or found.group(1) in typst_paths.STATEMENT_KEYWORDS:
        return True
    rest = unit[structure._call_end(unit, 0):].strip()
    return not rest or rest.startswith("//")


def _unit_kind(lines):
    """What a unit -- a line of the file's own markup and the lines of the construct it opens -- is: a `heading`, a `text`, or one of what is not a paragraph (`comment`, `raw`, `code`)."""
    first = lines[0].lstrip()
    if first.startswith("//") or first.startswith("/*"):
        return "comment"
    if first.startswith("="):
        return "heading" if _HEADING_MARKUP.match(first.rstrip()) else "text"
    if first.startswith("```"):
        return "raw"
    if first.startswith("#"):
        return "code" if _is_code("\n".join(lines).lstrip()) else "text"
    return "text"


def untagged(text):
    """The headings and paragraphs of `text` that no object tag wraps, in file order, as `Untagged` -- what `tag_file` wraps.

    A heading is a line of markup that starts with `=` and a space, and a paragraph is a run of lines of markup with no blank line between them -- a list is one -- found by the lexer of calc/typst_paths.py at the top of the file: **not** inside a call, a content block, a formula or a raw block, so that a table's rows, a figure's arguments and what an `#if` prints are not looked into. Left alone, and never wrapped: a line comment or a block comment (a tag among them), a raw block, the import line and every other `#` line that is code -- a statement, a call that stands alone on its lines (`#show-plan(…)`, `#grid(…)`, `#v(1em)`) -- the lines inside an object already, and a paragraph that holds a blank line inside a construct it opens. A paragraph that begins with a call and goes on with words (`#cite-norm(…) sets …`) is a paragraph. Refused (ObjectError `tags`) where the file's tags cannot be read.
    """
    blocks, problems = structure.pair_tags(text)
    if problems:
        raise ObjectError("tags", "Woodcore cannot read the tags of this file, so it does not tag it -- " + "; ".join(str(p) for p in problems),
                          problems=[str(p) for p in problems])
    lines = _lines(text)
    if not lines:
        return []
    bare = [line.rstrip("\r\n") for line in lines]
    bare[0] = bare[0].lstrip(chr(0xFEFF))
    lexer = _TopLines("\n".join(bare))
    lexer.run()
    taken = set()
    for block in blocks:
        if block.kind == "object":
            taken.update(range(block.start, block.end + 1))
    blank = [not line.strip() for line in bare]
    starts = [k for k in range(len(bare)) if k in lexer.top and not blank[k]]
    found, run = [], None

    def flush():
        nonlocal run
        if run is not None:
            found.append(Untagged("text", run[0], run[1], "\n".join(bare[run[0]:run[1] + 1])))
            run = None

    for n, k in enumerate(starts):
        stop = (starts[n + 1] if n + 1 < len(starts) else len(bare)) - 1
        while stop > k and blank[stop]:
            stop -= 1
        if k in taken:
            flush()
            continue
        kind = _unit_kind(bare[k:stop + 1])
        if kind == "heading":
            flush()
            found.append(Untagged("heading", k, stop, bare[k], len(_HEADING_MARKUP.match(bare[k].lstrip()).group(1))))
        elif kind == "text" and not any(blank[k:stop + 1]):
            if run is not None and run[1] + 1 == k:
                run[1] = stop
            else:
                flush()
                run = [k, stop]
        else:
            flush()
    flush()
    return found


def _slug(text):
    out = []
    for char in unicodedata.normalize("NFKD", text.strip().lower()):
        if unicodedata.combining(char):
            continue
        out.append(char if char.isascii() and char.isalnum() else "-")
    return re.sub("-+", "-", "".join(out)).strip("-")


def _id_base(item, ordinal, style):
    """The id an untagged heading or paragraph is given, before it is made unique: `title`, `h2`, … and `p1`, `p2`, … in the `plain` style (what the templates carry), the words it begins with in the `slug` style (`einleitung`, `die-bemessung-der`)."""
    if style == "plain":
        if item.kind == "text":
            return f"p{ordinal}"
        return "title" if ordinal == 1 else f"h{ordinal}"
    words = _plain(item.text.lstrip("= ").strip()) or item.text
    if item.kind == "heading":
        base = _slug(_LABEL_TAIL.sub("", words))[:40].strip("-")
        return base if base and base[0].isalpha() else "heading" + ("-" + base if base else "")
    base = _slug(" ".join(words.split()[:4]))[:32].strip("-")
    return base if base and base[0].isalpha() else "text" + ("-" + base if base else "")


def tag_file(text, ids="slug"):
    """`text` with every untagged heading and paragraph wrapped in object tags (`untagged`): `// woodcore:object heading einleitung` … `// woodcore:/object einleitung` around a heading line, `// woodcore:object text …` around a paragraph. **Nothing else changes**: every byte outside the inserted tag lines is kept, the tags take the file's own line ending, a last line with no line ending keeps having none, and a second run changes nothing -- it is `text` itself that comes back. A file whose tags cannot be read is refused (ObjectError `tags`), like every write of this module.

    The tags are comments, so the document compiles and prints as it did. `ids` is `"slug"` (the default: an id made of the heading's words, or of the first words of a paragraph -- `einleitung`, `die-bemessung-der`, unique in the file) or `"plain"`, the one the templates carry: `title` for the file's first heading, `h2`, `h3` for the others and `p1`, `p2`, … for the paragraphs, in the order they stand.
    """
    if ids not in ("slug", "plain"):
        raise ObjectError("bad_id", f"ids is 'slug' or 'plain' -- got {ids!r}", id=ids)
    items = untagged(text)
    if not items:
        return text
    used = {b.id for b in structure.pair_tags(text)[0] if b.kind == "object"}
    counts = {"heading": 0, "text": 0}
    first, last, kinds = {}, {}, {}
    for item in items:
        counts[item.kind] += 1
        base = _id_base(item, counts[item.kind], ids)
        name, n = base, 2
        while name in used:
            name, n = f"{base}-{n}", n + 1
        used.add(name)
        first[item.start], last[item.end], kinds[item.start] = name, name, item.kind
    lines = _lines(text)
    bom = chr(0xFEFF) if text.startswith(chr(0xFEFF)) else ""     # the byte order mark stays the first character of the file
    if bom:
        lines[0] = lines[0][1:]
    newline = _newline_of(text)
    out = []
    for k, line in enumerate(lines):
        if k in first:
            out.append(f"{START} {kinds[k]} {first[k]}{newline}")
        if k in last:
            ending = _ending(line)
            out.append(line if ending else line + newline)
            out.append(f"{END} {last[k]}" + (newline if ending else ""))
        else:
            out.append(line)
    return bom + "".join(out)
