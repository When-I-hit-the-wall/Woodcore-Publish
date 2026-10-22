"""The models of an export sheet's objects -- the page, a text, a viewport of a plan, a section, a legend, a list of positions, quantities, the title block -- and of a heading and a paragraph: split out of calc/typst_objects.py (issue #30), moved verbatim. typst_objects.py imports every name back.
"""

import math
import re
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
    CHECK_OPTION_KEYS,
    CHOICE_OPTION_KEYS,
    COLUMN_KEYS,
    COLUMN_KINDS,
    Column,
    DEFAULTS,
    KNOWN_COLUMNS,
    LIVE_LOAD_FILLED,
    Model,
    ModelError,
    NormListModel,
    SIGNATURE_KEYS,
    _COLUMN_ID,
    _KEEP,
    _bool_value,
    _drop,
    _id_value,
    _index,
    _move,
    _number_value,
    _put,
    _text_value,
)


# The levels a heading object may have: Typst takes any, a document's structure goes down four (structure.MAX_DEPTH) and a file may hold a heading or two below its own.
HEADING_LEVELS = (1, 6)


SHEET_FORMATS = ("A0", "A1", "A2", "A3", "A4", "A5", "A6")


# What a sheet shows (v0.116): its position plans or its fire-protection plans, never both -- lib/sheet.typ's `sheet(kind:)`.
SHEET_KINDS = ("position", "fire")


# The sheet's formats in millimetres, short side and long side -- lib/sheet.typ's sheet-formats, held equal by tests/test_sheets.py.
SHEET_SIZES = {"A0": (841, 1189), "A1": (594, 841), "A2": (420, 594), "A3": (297, 420), "A4": (210, 297), "A5": (148, 210), "A6": (105, 148)}


def _mm(value, what):
    """A coordinate or a size of a sheet, written as a length in millimetres: a number (taken as millimetres) or a Length."""
    if isinstance(value, Length):
        return value
    if isinstance(value, bool) or not isinstance(value, (int, float)) or (isinstance(value, float) and not math.isfinite(value)):
        raise ModelError("bad_value", f"{what} is a length in millimetres -- got {value!r}")
    if isinstance(value, float):
        value = round(value, 2)
        if value == int(value):
            value = int(value)
    return Length(value, "mm")


def mm_of(value):
    """A length of a sheet in millimetres, as a float -- None where it is none, auto or a length Woodcore cannot convert (an em, a ratio, an expression)."""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    if isinstance(value, Length):
        factor = {"mm": 1.0, "cm": 10.0, "pt": 25.4 / 72, "in": 25.4}.get(value.unit)
        return None if factor is None else float(value.value) * factor
    return None


class _Placed(Model):
    """What every object placed on a sheet shares: its top-left corner, `x` and `y`, in millimetres from the sheet's top-left corner."""

    def position(self):
        """(x, y) in millimetres, None for one Woodcore cannot read (auto, an expression)."""
        return mm_of(self.get("x")), mm_of(self.get("y"))

    def move_to(self, x, y):
        self._set("x", _mm(x, "x:"))
        self._set("y", _mm(y, "y:"))


class SheetPageModel(Model):
    """The sheet's page (`sheet-page`, the show rule `#show: sheet.with(...)`): its ISO format, its orientation and the margin its frame stands at."""
    TYPES = ("sheet-page",)

    def set_format(self, fmt):
        if fmt not in SHEET_FORMATS:
            raise ModelError("bad_value", f"format: is one of {', '.join(SHEET_FORMATS)} -- got {fmt!r}")
        self._set("format", fmt)

    def set_landscape(self, landscape=True):
        self._set("landscape", _bool_value(landscape, "landscape:"))

    def set_margin(self, margin):
        self._set("margin", _mm(margin, "margin:"))

    def set_kind(self, kind):
        """What the sheet shows (v0.116): "position" its position plans, "fire" its fire-protection plans -- never both."""
        if kind not in SHEET_KINDS:
            raise ModelError("bad_value", f"kind: is one of {', '.join(SHEET_KINDS)} -- got {kind!r}")
        self._set("kind", kind)

    def size(self):
        """(width, height) of the sheet in millimetres."""
        fmt = self.get("format")
        short, long = SHEET_SIZES.get(fmt, SHEET_SIZES["A3"])
        return (long, short) if self.get("landscape") is not False else (short, long)


class SheetTextModel(_Placed):
    """A text of the sheet (`sheet-text`): where it stands, its words (markup), their size and weight, and the width it wraps at."""
    TYPES = ("sheet-text",)

    def set_body(self, body):
        self._set("body", _text_value(body, "body"))

    def set_size(self, size):
        if isinstance(size, (int, float)) and not isinstance(size, bool):
            size = Length(size, "pt")
        if not isinstance(size, Length):
            raise ModelError("bad_value", f"size: is a length, 10pt -- got {size!r}")
        self._set("size", size)

    def set_weight(self, weight):
        if weight not in ("regular", "bold") and not (isinstance(weight, int) and not isinstance(weight, bool) and 100 <= weight <= 900):
            raise ModelError("bad_value", f"weight: is \"regular\", \"bold\" or a weight from 100 to 900 -- got {weight!r}")
        self._set("weight", weight)

    def set_width(self, width):
        self._set("width", AUTO if width is AUTO or width is None else _mm(width, "width:"))


class _Drawing(_Placed):
    """A plan placed on a sheet at a scale (`sheet-viewport`, `sheet-section`): which plan, and its size -- a scale 1:n, or a width where the plan is not calibrated, never both."""

    def set_plan(self, plan):
        if plan is not None:
            plan = _id_value(plan, "plan:")
        self._set("plan", plan)

    def _clear(self, name):
        """Takes an argument out of the call: its default, none, is what it then means."""
        self._args.pop(name, None)
        self._present.discard(name)

    def set_scale(self, n):
        """Prints the plan at 1:n: the width given goes, a drawing having one size."""
        if n is None:
            return self._clear("scale")
        n = _number_value(n, "scale:")
        if n <= 0:
            raise ModelError("bad_value", f"scale: is greater than 0 -- got {n!r}")
        self._clear("width")
        self._set("scale", n)

    def set_width(self, width):
        """Prints the plan at this width in millimetres: the scale given goes."""
        if width is None:
            return self._clear("width")
        self._clear("scale")
        self._set("width", _mm(width, "width:"))


class ViewportModel(_Drawing):
    """A position plan on the sheet (`sheet-viewport`): which plan, where, at which scale or width, the positions on a halo, its axes, its scale bar and the line under it."""
    TYPES = ("sheet-viewport",)

    def set_highlight(self, highlight):
        if isinstance(highlight, (list, tuple)):
            highlight = [_id_value(h, "highlight:") for h in highlight]
        elif highlight is not None:
            highlight = _id_value(highlight, "highlight:")
        self._set("highlight", highlight)

    def set_axes(self, shown=True):
        self._set("axes", _bool_value(shown, "axes:"))

    def set_dimensions(self, shown=True):
        """The plan's dimensions printed on the sheet, or left out (issue #9)."""
        self._set("dimensions", _bool_value(shown, "dimensions:"))

    def set_lengths(self, shown=True):
        """The lengths beside the plan's elements printed on the sheet, or left out (issue #9)."""
        self._set("lengths", _bool_value(shown, "lengths:"))

    def set_centres(self, shown=True):
        """The stiffness centre, the mass centre and the building's outline printed on the sheet where the plan prints them, or left out (issue #54)."""
        self._set("centres", _bool_value(shown, "centres:"))

    def set_scale_bar(self, shown=True):
        self._set("scale-bar", _bool_value(shown, "scale-bar:"))

    def set_caption(self, caption):
        self._set("caption", caption if caption is AUTO else _text_value(caption, "caption"))

    def set_title(self, title):
        """The line above the plan (v0.116): AUTO «Nom — description, étage (éch. 1:n)» from the plan, None none, else the engineer's words."""
        self._set("title", title if title is AUTO or title is None else _text_value(title, "title"))


class FireViewportModel(_Drawing):
    """A fire-protection plan on the sheet (`sheet-fire-viewport`, v0.115): which plan, where, at which scale or width, the legend drawn on it, its scale bar and the line under it."""
    TYPES = ("sheet-fire-viewport",)

    def set_legend(self, shown=True):
        self._set("legend", _bool_value(shown, "legend:"))

    def set_scale_bar(self, shown=True):
        self._set("scale-bar", _bool_value(shown, "scale-bar:"))

    def set_caption(self, caption):
        self._set("caption", caption if caption is AUTO else _text_value(caption, "caption"))

    def set_title(self, title):
        """The line above the plan (v0.116): AUTO «Nom — description, étage (éch. 1:n)» from the plan, None none, else the engineer's words."""
        self._set("title", title if title is AUTO or title is None else _text_value(title, "title"))


class SectionModel(_Drawing):
    """A schematic section on the sheet (`sheet-section`): the section plan, the storey highlighted, where, at which scale or width, and its title (`auto` «Coupe schématique (éch. 1:n)»)."""
    TYPES = ("sheet-section",)

    def set_storey(self, storey):
        if storey is not None:
            storey = _id_value(storey, "storey:")
        self._set("storey", storey)

    def set_title(self, title):
        self._set("title", title if title is AUTO else _text_value(title, "title"))


class LegendModel(_Placed):
    """The sheet's legend (`sheet-legend`): the plans whose symbols it lists (`auto`, those of the sheet's viewports), where, its width and its title."""
    TYPES = ("sheet-legend",)

    def set_plans(self, plans):
        if plans is not AUTO:
            if isinstance(plans, (list, tuple)):
                plans = [_id_value(p, "plans:") for p in plans]
            else:
                plans = _id_value(plans, "plans:")
        self._set("plans", plans)

    def set_width(self, width):
        self._set("width", _mm(width, "width:"))

    def set_title(self, title):
        self._set("title", title if title is AUTO else _text_value(title, "title"))


class FireLegendModel(LegendModel):
    """The legend of a sheet's fire-protection plans (`sheet-fire-legend`, v0.115): the fire plans whose symbols it lists (`auto`, those of the sheet's fire viewports), where, its width and its title -- as `sheet-legend`'s own."""
    TYPES = ("sheet-fire-legend",)


class PositionListModel(_Placed):
    """The list of the positions on a sheet (`sheet-position-list`, v0.116): which positions -- those of the sheet's plans (`plans: auto`) or of given plans, every position, or one storey's --, where, its width and its title."""
    TYPES = ("sheet-position-list",)
    SCOPES = ("plans", "all", "storey")

    def set_plans(self, plans):
        if plans is not AUTO:
            if isinstance(plans, (list, tuple)):
                plans = [_id_value(p, "plans:") for p in plans]
            else:
                plans = _id_value(plans, "plans:")
        self._set("plans", plans)

    def set_scope(self, scope):
        if scope not in self.SCOPES:
            raise ModelError("bad_value", f"scope: is one of {', '.join(self.SCOPES)} -- got {scope!r}")
        self._set("scope", scope)

    def set_storey(self, storey):
        if storey is not None and (not isinstance(storey, str) or len(storey) != 1):
            raise ModelError("bad_value", f"storey: is a storey's numbering character, \"0\" -- got {storey!r}")
        self._set("storey", storey)

    def set_width(self, width):
        self._set("width", _mm(width, "width:"))

    def set_title(self, title):
        self._set("title", title if title is AUTO or title is None else _text_value(title, "title"))


class QuantitiesModel(_Placed):
    """The quantities on a sheet (`sheet-quantities`, issue #9): what -- the sheet's plans (`plans: auto`) or given plans, every plan, or chosen positions --, where, its width and its title."""
    TYPES = ("sheet-quantities",)
    SCOPES = ("plans", "all", "positions")

    def set_plans(self, plans):
        if plans is not AUTO:
            if isinstance(plans, (list, tuple)):
                plans = [_id_value(p, "plans:") for p in plans]
            else:
                plans = _id_value(plans, "plans:")
        self._set("plans", plans)

    def set_scope(self, scope):
        if scope not in self.SCOPES:
            raise ModelError("bad_value", f"scope: is one of {', '.join(self.SCOPES)} -- got {scope!r}")
        self._set("scope", scope)

    def set_positions(self, positions):
        self._set("positions", [_id_value(p, "positions:") for p in positions] if isinstance(positions, (list, tuple)) else _id_value(positions, "positions:"))

    def set_width(self, width):
        self._set("width", _mm(width, "width:"))

    def set_title(self, title):
        self._set("title", title if title is AUTO or title is None else _text_value(title, "title"))


class TitleBlockModel(Model):
    """The sheet's title block (`sheet-titleblock`): where it stands (`auto` against the frame's bottom-right corner) and each of its cells, `auto` taking the project's value."""
    TYPES = ("sheet-titleblock",)
    CELLS = ("object", "element", "client", "architect", "phase", "project-number", "plan-number", "index",
             "revision-date", "revision-author", "modification", "drawn-by", "date", "scale", "size")

    def set_cell(self, name, value):
        """One cell: `AUTO` the project's value where the cell has one, None empty, else the engineer's words."""
        if name not in self.CELLS:
            raise ModelError("bad_argument", f"the title block has no cell {name!r} -- its cells are {', '.join(self.CELLS)}")
        if value is AUTO and DEFAULTS[self.type][name] is not AUTO:
            raise ModelError("bad_value", f"{name}: takes no auto -- the project has no value for it")
        self._set(name, value if value is AUTO else _text_value(value, name))

    def move_to(self, x, y):
        """Where it stands; AUTO for both sets it against the frame's corner."""
        self._set("x", AUTO if x is AUTO else _mm(x, "x:"))
        self._set("y", AUTO if y is AUTO else _mm(y, "y:"))



# `= Titel`, `== Titel`: the markup form of a heading, the one Woodcore writes.
_HEADING_MARKUP = re.compile(r"^(=+)[ \t]+(\S.*)$")


_BLANK = re.compile(r"^[ \t]*$")


class _Checked(typst_paths._Lexer):
    """The lexer of calc/typst_paths.py, which also notes a raw block or a block comment that is never closed -- what would swallow the tag that ends the object."""

    def __init__(self, text):
        super().__init__(text)
        self.unclosed = False

    def _raw(self, j):
        end = super()._raw(j)
        opening = 0
        while j + opening < self.n and self.text[j + opening] == "`":
            opening += 1
        if opening != 2 and end >= self.n and not (end - j >= 2 * opening and self.text.endswith("`" * opening)):
            self.unclosed = True
        return end

    def _block_comment(self, j):
        end = super()._block_comment(j)
        if end >= self.n and not self.text.endswith("*/"):
            self.unclosed = True
        return end


def _balanced(markup):
    """Whether `markup` closes everything it opens -- a call, a content block, a formula, a raw block, a comment -- so that the tag line after it is a tag line and not the inside of something."""
    # read as the file holds it, the line ending after it: a paragraph that ends with a call -- `#show-annexes()` -- has closed it there, where the lexer would otherwise wait for what may follow a call
    lexer = _Checked(markup + "\n")
    lexer.run()
    return len(lexer.stack) == 1 and not lexer.unclosed


def _level_value(level):
    low, high = HEADING_LEVELS
    if isinstance(level, bool) or not isinstance(level, int) or not low <= level <= high:
        raise ModelError("bad_value", f"a heading's level is a whole number from {low} to {high} -- got {level!r}", reason="level")
    return level


def _title_value(title):
    """A heading's title as written: one line of markup, not empty."""
    if not isinstance(title, str):
        raise ModelError("bad_value", f"a heading's title is Typst markup, a string -- got {title!r}", reason="type")
    title = _normalise(title).strip()
    if not title:
        raise ModelError("bad_value", "a heading has a title", reason="empty")
    if "\n" in title:
        raise ModelError("bad_value", "a heading's title is one line", reason="several")
    if not _balanced(title):
        raise ModelError("bad_value", f"{title!r} does not close what it opens -- a bracket, a formula, a raw block", reason="unbalanced")
    return title


def _heading_parts(body):
    """(level, title) of a body that is one heading -- `= Titel`, or the call `#heading(level: 2, "Titel")` written on one line -- or a ModelError saying what it is instead."""
    text = _normalise(body).strip()
    if not text:
        raise ModelError("unreadable", "the heading object holds nothing", reason="empty")
    if "\n" in text:
        raise ModelError("unreadable", "a heading object holds one heading line and nothing else", reason="several")
    found = _HEADING_MARKUP.match(text)
    if found:
        return len(found.group(1)), found.group(2).rstrip()
    headings = structure.scan_headings(text)
    if len(headings) == 1 and headings[0].line == 0 and headings[0].form == "call" and headings[0].title:
        return headings[0].level, headings[0].title
    raise ModelError("unreadable", f"{text!r} is no heading -- a heading object holds `= Titel`", reason="not_a_heading")


def _paragraph_value(markup):
    """One paragraph of markup as written: its lines, no blank line between them, nothing before the first line but its own indentation and nothing after the last -- or a ModelError saying why it is not one."""
    if isinstance(markup, Content):
        markup = markup.markup
    if not isinstance(markup, str):
        raise ModelError("bad_value", f"a paragraph is Typst markup, a string -- got {markup!r}", reason="type")
    lines = _normalise(markup).split("\n")
    while lines and _BLANK.match(lines[0]):
        lines.pop(0)
    while lines and _BLANK.match(lines[-1]):
        lines.pop()
    if not lines:
        raise ModelError("unreadable", "the paragraph object holds nothing", reason="empty")
    if any(_BLANK.match(line) for line in lines):
        raise ModelError("unreadable", "a paragraph object holds one paragraph -- a blank line starts another one, which is an object of its own", reason="several")
    text = "\n".join(lines).rstrip()
    if structure.scan_headings(text):
        raise ModelError("unreadable", "a paragraph object holds no heading -- a heading is an object of its own", reason="heading_in_text")
    tags, problems = structure.scan_tags(text, None)
    if tags or problems:
        raise ModelError("bad_value", "a line of the paragraph would read as a `// woodcore:` tag", reason="tag_in_body")
    if not _balanced(text):
        raise ModelError("bad_value", "the paragraph does not close what it opens -- a call, a bracket, a formula, a raw block, a comment", reason="unbalanced")
    return text


class HeadingModel:
    """A heading of the document (`heading`): its level -- the number of `=` -- and its title, one line of markup as written, a trailing `<label>` of the engineer's included. `to_body()` is `= Titel`, what is written between the tags. A heading written as the call `#heading(...)` is read as one and written back as `= Titel`."""
    TYPES = ("heading",)
    type = "heading"
    markup = True

    def __init__(self, level=1, title=None):
        self._level = _level_value(level)
        self._title = _title_value(PLACEHOLDER if title is None else title)

    @classmethod
    def from_body(cls, body):
        level, title = _heading_parts(body)
        return cls(level, title)

    @property
    def level(self):
        return self._level

    @property
    def title(self):
        return self._title

    def set_level(self, level):
        self._level = _level_value(level)

    def set_title(self, title):
        self._title = _title_value(title)

    def to_body(self):
        return "=" * self._level + " " + self._title

    def serialize(self):
        return self.to_body()


class TextModel:
    """A paragraph of the document (`text`): its markup as written -- lines, a list, a formula, a `#cite-norm(...)` -- and nothing more: no blank line in it (that starts another paragraph), no heading, no line that reads as a tag. `to_body()` is the text, what is written between the tags; the editor shows it in a plain box."""
    TYPES = ("text",)
    type = "text"
    markup = True

    def __init__(self, text=None):
        self._text = _paragraph_value(PLACEHOLDER if text is None else text)

    @classmethod
    def from_body(cls, body):
        return cls(body)

    @property
    def text(self):
        return self._text

    def set_text(self, markup):
        self._text = _paragraph_value(markup)

    def to_body(self):
        return self._text

    def serialize(self):
        return self.to_body()
