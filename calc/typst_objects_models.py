"""What the right pane edits of a parametric object -- a table, a live-load table, options, a choice, a checklist, signatures, a list of norms, a field, an image, a plan, an extract, the annexes -- each a Model of the object's arguments: split out of calc/typst_objects.py (issue #30), moved verbatim. typst_objects.py imports every name back.
"""

import copy
import math
import re
from dataclasses import dataclass, field
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


# The columns the two load tables know by their id, in the order `columns: auto` gives them (lib/document.typ's live-load-columns and dead-load-columns), with the unit their heading carries. ψ is never a column of the live loads (the engineer, 01.10.2026): the Reduktionsbeiwerte stay transcribed in calc/norms/ for the load combinations and are shown by no live-load table.
KNOWN_COLUMNS = {
    "live-load-table": ("zone", "storey", "use", "category", "q_k", "Q_k"),
    "dead-load-table": ("zone", "storey", "buildup", "load"),
}


# The live-load columns filled from the row's category where the row leaves them to `auto`.
LIVE_LOAD_FILLED = ("q_k", "Q_k")


# The keys a column, an option, a choice's option and a signature row carry, in the order Woodcore writes them.
COLUMN_KEYS = ("id", "title", "unit", "kind")


COLUMN_KINDS = ("text", "number", "math", "wide")


CHECK_OPTION_KEYS = ("id", "label", "checked", "text")


CHOICE_OPTION_KEYS = ("id", "label")


SIGNATURE_KEYS = ("group", "role", "name", "place", "date")


DEFAULTS = {kind: _parameters(text, kind) for kind, text in SIGNATURES.items()}


class ModelError(ValueError):
    """A model operation refused: a `code` and an English sentence."""

    def __init__(self, code, message, **values):
        self.code = code
        self.values = values
        super().__init__(message)


_KEEP = object()


def _put(entry, key, value, order):
    """`entry` (a dictionary) with `key` set to `value`: in place where it is there already, else before the first key that comes after it in `order` -- so a key added lands where Woodcore would have written it, and the keys the engineer wrote keep their order."""
    if key in entry:
        out = dict(entry)
        out[key] = value
        return out
    rank = order.index(key) if key in order else len(order)
    out, placed = {}, False
    for k, v in entry.items():
        if not placed and k in order and order.index(k) > rank:
            out[key] = value
            placed = True
        out[k] = v
    if not placed:
        out[key] = value
    return out


def _drop(entry, key):
    return {k: v for k, v in entry.items() if k != key}


def _index(items, index, what, insert=False):
    """`index` checked against a list of `len(items)` (one more where it is where to insert)."""
    top = len(items) + (1 if insert else 0)
    if index is None and insert:
        return len(items)
    if isinstance(index, bool) or not isinstance(index, int) or not -top <= index < top:
        raise ModelError("bad_index", f"{what} {index!r} does not exist -- there are {len(items)}", index=index)
    return index % top if index < 0 else index


def _move(items, index, new_index, what):
    index = _index(items, index, what)
    new_index = _index(items, new_index, what)
    item = items.pop(index)
    items.insert(new_index, item)


def _text_value(value, what):
    """A text of the engineer's: None, or markup given as a string or as Content (or an Expr kept as it is)."""
    try:
        return content(value)
    except ValueError as exc:
        raise ModelError("bad_value", f"{what}: {exc}") from None


def _number_value(value, what):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or (isinstance(value, float) and not math.isfinite(value)):
        raise ModelError("bad_value", f"{what} is a number -- got {value!r}")
    return value


def _bool_value(value, what):
    if not isinstance(value, bool):
        raise ModelError("bad_value", f"{what} is true or false -- got {value!r}")
    return value


def _id_value(value, what):
    if not isinstance(value, str) or not value.strip():
        raise ModelError("bad_value", f"{what} is a non-empty string -- got {value!r}")
    return value


class Model:
    """What every editor's model shares: the call it sits over, its arguments read with their defaults, and `to_call()`. An argument is written where the call had it, and otherwise only where it differs from the command's default; an argument the command does not take is left out, as the canonical form leaves it out."""
    TYPES = ()
    markup = False

    def __init__(self, call):
        if not isinstance(call, Call) or call.type not in self.TYPES:
            raise ModelError("wrong_type", f"{type(self).__name__} edits {', '.join(self.TYPES)} -- got {getattr(call, 'type', call)!r}")
        self.type = call.type
        order = ORDER[call.type]
        self._present = {name for name in call.args if name in order}
        self._args = {name: copy.deepcopy(call.args[name]) for name in order if name in call.args}

    @classmethod
    def from_call(cls, call):
        return cls(call)

    def get(self, name):
        """The argument `name`, as the call has it or as its default."""
        if name not in ORDER[self.type]:
            raise ModelError("bad_argument", f"{self.type} takes no argument {name!r}")
        return copy.deepcopy(self._args[name] if name in self._args else DEFAULTS[self.type][name])

    def _set(self, name, value):
        if name not in ORDER[self.type]:
            raise ModelError("bad_argument", f"{self.type} takes no argument {name!r}")
        if name not in self._present and same(value, DEFAULTS[self.type][name]):
            self._args.pop(name, None)
        else:
            self._args[name] = value

    def _list(self, name, of=None, allow_auto=False):
        """An argument that is an array -- of dictionaries where `of` is dict -- refused where it is an expression or anything else Woodcore cannot edit."""
        value = self._args.get(name, DEFAULTS[self.type][name])
        if value is AUTO and allow_auto:
            return value
        if not isinstance(value, (list, tuple)) or (of is dict and not all(isinstance(v, dict) for v in value)):
            raise ModelError("not_editable", f"{self.type}: {name}: is {inline(value)}, which Woodcore's editor cannot edit -- write it as an array" + (" of dictionaries" if of is dict else ""), argument=name)
        return list(value)

    def to_call(self):
        """The call to write: every argument the model holds, in the command's order."""
        return Call(self.type, {name: copy.deepcopy(self._args[name]) for name in ORDER[self.type] if name in self._args})

    def serialize(self):
        return serialize(self.to_call())


@dataclass(frozen=True)
class Column:
    """One column of a table as the editor shows it: its id, its title (content, a string, or None -- the command's own heading for a column it knows by its id), its unit and its kind (None: the column's own), whether the command knows it by its id, and whether it is hidden."""
    id: str
    title: object = None
    unit: object = None
    kind: object = None
    known: bool = False
    hidden: bool = False


_COLUMN_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")


class NormListModel(Model):
    """The norms a section names (`show-norm-list`): its keys, in order -- strings naming a document of calc/norms/norms.json or of the project's references.bib, and content for a line of the engineer's own -- and the project's references.bib."""
    TYPES = ("show-norm-list",)

    def __init__(self, call):
        super().__init__(call)
        self._list("keys")

    @property
    def keys(self):
        return copy.deepcopy(self._list("keys"))

    def has_key(self, key):
        return key in [k for k in self._list("keys") if isinstance(k, str)]

    def add_key(self, key, index=None):
        """A document named by its key, `"SIA 260"`. Returns its index."""
        key = _id_value(key, "a key").strip()
        keys = self._list("keys")
        if self.has_key(key):
            raise ModelError("id_exists", f"the list names {key!r} already", key=key)
        at = _index(keys, index, "key", insert=True)
        keys.insert(at, key)
        self._set("keys", keys)
        return at

    def add_text(self, markup, index=None):
        """A line in the engineer's own words, printed as it is. Returns its index."""
        text = _text_value(markup, "a line")
        if text is None:
            raise ModelError("bad_value", "a line holds text")
        keys = self._list("keys")
        at = _index(keys, index, "key", insert=True)
        keys.insert(at, text)
        self._set("keys", keys)
        return at

    def remove(self, index):
        keys = self._list("keys")
        keys.pop(_index(keys, index, "key"))
        self._set("keys", keys)

    def remove_key(self, key):
        if not self.has_key(key):
            raise ModelError("no_key", f"the list does not name {key!r}", key=key)
        self._set("keys", [k for k in self._list("keys") if k != key])

    def move(self, index, new_index):
        keys = self._list("keys")
        _move(keys, index, new_index, "key")
        self._set("keys", keys)

    def select(self, key, selected=True):
        """What the section's checklist of norms does: a key named (at the end) or no longer named."""
        if selected and not self.has_key(key):
            self.add_key(key)
        elif not selected and self.has_key(key):
            self.remove_key(key)

    @property
    def project(self):
        return self.get("project")

    def set_project(self, path):
        if path is not None:
            path = _id_value(path, "project:")
        self._set("project", path)

