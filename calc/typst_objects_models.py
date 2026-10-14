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


class TableModel(Model):
    """A table of the document (`doc-table`) or one of the two load tables (`live-load-table`, `dead-load-table`): its columns, the columns hidden but kept, and its rows, one dictionary each keyed by column id.

    `columns: auto` of a load table stands for the columns the command knows by id (KNOWN_COLUMNS); it is written out as the list it stands for the moment an operation changes it, and kept as `auto` while nothing does. A cell is set from Typst markup (a string, written as content), a number, `auto`, `none`, Content or an Expr; `auto` only where the command fills the cell from the row -- the live loads' q_k and Q_k.
    """
    TYPES = ("doc-table", "live-load-table", "dead-load-table")

    def __init__(self, call):
        super().__init__(call)
        auto = self.type in KNOWN_COLUMNS
        columns = self._list("columns", of=dict, allow_auto=auto)
        if columns is not AUTO:
            for i, c in enumerate(columns):
                if not isinstance(c.get("id"), str):
                    raise ModelError("not_editable", f"{self.type}: column {i + 1} has no id Woodcore can read", argument="columns")
        hidden = self._list("hidden")
        if not all(isinstance(h, str) for h in hidden):
            raise ModelError("not_editable", f"{self.type}: hidden: names its columns by string ids", argument="hidden")
        self._list("rows", of=dict)

    # -- reading

    def _raw_columns(self):
        value = self._args.get("columns", DEFAULTS[self.type]["columns"])
        if value is AUTO:
            return [{"id": i} for i in KNOWN_COLUMNS[self.type]]
        return copy.deepcopy(list(value))

    def _raw_hidden(self, ids=None):
        return list(self._args.get("hidden", DEFAULTS[self.type]["hidden"]))

    def column_ids(self):
        return [c["id"] for c in self._raw_columns()]

    @property
    def columns(self):
        """The columns in order, as Column."""
        ids = self.column_ids()
        hidden = set(self._raw_hidden(ids))
        known = KNOWN_COLUMNS.get(self.type, ())
        return [Column(c["id"], c.get("title"), c.get("unit"), c.get("kind"), c["id"] in known, c["id"] in hidden) for c in self._raw_columns()]

    def column(self, column_id):
        return next((c for c in self.columns if c.id == column_id), None) or self._no_column(column_id)

    @property
    def hidden(self):
        """The ids of the hidden columns."""
        return self._raw_hidden()

    def is_hidden(self, column_id):
        return column_id in self._raw_hidden()

    @property
    def rows(self):
        """The rows, one dictionary each, copies."""
        return copy.deepcopy(self._list("rows", of=dict))

    @property
    def row_count(self):
        return len(self._list("rows", of=dict))

    def cell(self, row, column_id):
        """The cell as the call holds it, or `_default_cell` where the row leaves it out."""
        rows = self._list("rows", of=dict)
        entry = rows[_index(rows, row, "row")]
        return copy.deepcopy(entry[column_id]) if column_id in entry else self._default_cell(column_id)

    def _default_cell(self, column_id):
        return AUTO if self.type == "live-load-table" and column_id in LIVE_LOAD_FILLED else None

    def _no_column(self, column_id):
        raise ModelError("no_column", f"the table has no column {column_id!r} -- its columns are {', '.join(self.column_ids()) or 'none'}", column=column_id)

    # -- writing

    def _write_columns(self, columns):
        self._set("columns", columns)

    def _write_hidden(self, hidden):
        order = self.column_ids()
        self._set("hidden", sorted(hidden, key=lambda h: order.index(h) if h in order else len(order)))

    def _write_rows(self, rows):
        self._set("rows", rows)

    def _cell_value(self, column_id, value):
        if value is AUTO:
            if self._default_cell(column_id) is not AUTO:
                raise ModelError("no_auto", f"the column {column_id!r} has nothing to be filled from -- auto is for the live loads' {', '.join(LIVE_LOAD_FILLED)}", column=column_id)
            return AUTO
        if value is None or isinstance(value, (Content, Expr)):
            return value
        if isinstance(value, str):
            return _text_value(value, f"column {column_id!r}")
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return _number_value(value, f"column {column_id!r}")
        raise ModelError("bad_value", f"a cell is markup, a number, auto or none -- got {value!r}", column=column_id)

    def add_row(self, index=None, values=None):
        """A row inserted at `index` (at the end where None), holding `values` ({column id: value}, set as `set_cell` sets them). Returns its index."""
        rows = self._list("rows", of=dict)
        at = _index(rows, index, "row", insert=True)
        entry, order = {}, self.column_ids()
        for column_id, value in (values or {}).items():
            if column_id not in order:
                self._no_column(column_id)
            entry = _put(entry, column_id, self._cell_value(column_id, value), order)
        rows.insert(at, entry)
        self._write_rows(rows)
        return at

    def remove_row(self, index):
        rows = self._list("rows", of=dict)
        rows.pop(_index(rows, index, "row"))
        self._write_rows(rows)

    def move_row(self, index, new_index):
        rows = self._list("rows", of=dict)
        _move(rows, index, new_index, "row")
        self._write_rows(rows)

    def add_column(self, column_id, title=None, unit=None, kind=None, index=None):
        """A column inserted at `index` (at the end where None): an id of letters, digits, `_` and `-`, unique in the table; a title (markup, or None for a column the command knows by that id), a unit, a kind (COLUMN_KINDS). Returns its index."""
        if not isinstance(column_id, str) or not _COLUMN_ID.match(column_id) or column_id in RESERVED:
            raise ModelError("bad_id", f"{column_id!r} is not a column id -- letters, digits, `_` and `-`, starting with a letter", column=column_id)
        columns = self._raw_columns()
        if column_id in [c["id"] for c in columns]:
            raise ModelError("id_exists", f"the table has a column {column_id!r} already", column=column_id)
        title = _text_value(title, "title")
        if title is None and column_id not in KNOWN_COLUMNS.get(self.type, ()):
            raise ModelError("no_title", f"the column {column_id!r} needs a title -- only the columns {', '.join(KNOWN_COLUMNS.get(self.type, ())) or 'of no id'} are known by their id alone", column=column_id)
        entry = {"id": column_id}
        entry = self._column_fields(entry, title=title, unit=unit, kind=kind)
        at = _index(columns, index, "column", insert=True)
        columns.insert(at, entry)
        self._write_columns(columns)
        return at

    def _column_fields(self, entry, title=_KEEP, unit=_KEEP, kind=_KEEP):
        for key, value in (("title", title), ("unit", unit), ("kind", kind)):
            if value is _KEEP:
                continue
            if key == "title":
                value = _text_value(value, "title")
            elif key == "unit" and value is not None and not isinstance(value, str):
                raise ModelError("bad_value", f"a unit is a string, \"kN/m²\" -- got {value!r}")
            elif key == "kind" and value is not None and value not in COLUMN_KINDS:
                raise ModelError("bad_value", f"a column's kind is {', '.join(COLUMN_KINDS)} -- got {value!r}")
            entry = _drop(entry, key) if value is None else _put(entry, key, value, COLUMN_KEYS)
        return entry

    def set_column(self, column_id, *, title=_KEEP, unit=_KEEP, kind=_KEEP):
        """A column's title, unit or kind changed -- None takes one off, a column the command knows falling back to its own."""
        columns = self._raw_columns()
        at = next((i for i, c in enumerate(columns) if c["id"] == column_id), None)
        if at is None:
            self._no_column(column_id)
        if title is None and column_id not in KNOWN_COLUMNS.get(self.type, ()):
            raise ModelError("no_title", f"the column {column_id!r} needs a title", column=column_id)
        columns[at] = self._column_fields(columns[at], title=title, unit=unit, kind=kind)
        self._write_columns(columns)

    def remove_column(self, column_id):
        """A column taken out of the table -- out of `hidden` and out of every row with it."""
        columns = self._raw_columns()
        if column_id not in [c["id"] for c in columns]:
            self._no_column(column_id)
        self._write_columns([c for c in columns if c["id"] != column_id])
        self._write_hidden([h for h in self._raw_hidden() if h != column_id])
        self._write_rows([_drop(r, column_id) for r in self._list("rows", of=dict)])

    def move_column(self, column_id, new_index):
        columns = self._raw_columns()
        at = next((i for i, c in enumerate(columns) if c["id"] == column_id), None)
        if at is None:
            self._no_column(column_id)
        _move(columns, at, new_index, "column")
        self._write_columns(columns)

    def set_hidden(self, column_id, hidden=True):
        """A column hidden -- not printed, its cells kept -- or shown again."""
        if column_id not in self.column_ids():
            self._no_column(column_id)
        now = self._raw_hidden()
        if hidden and column_id not in now:
            self._write_hidden(now + [column_id])
        elif not hidden and column_id in now:
            self._write_hidden([h for h in now if h != column_id])

    def hide_column(self, column_id):
        self.set_hidden(column_id, True)

    def show_column(self, column_id):
        self.set_hidden(column_id, False)

    def set_cell(self, row, column_id, value):
        """A cell set: markup (a string, written as content), a number, `auto`, `none`, Content or an Expr."""
        if column_id not in self.column_ids():
            self._no_column(column_id)
        rows = self._list("rows", of=dict)
        at = _index(rows, row, "row")
        rows[at] = _put(rows[at], column_id, self._cell_value(column_id, value), self.column_ids())
        self._write_rows(rows)

    def clear_cell(self, row, column_id):
        """A cell taken out of its row: empty -- or, in a live-load column the category fills, `auto`."""
        rows = self._list("rows", of=dict)
        at = _index(rows, row, "row")
        rows[at] = _drop(rows[at], column_id)
        self._write_rows(rows)

    def set_caption(self, caption):
        self._set("caption", _text_value(caption, "caption"))

    def set_notes(self, notes):
        """The small print: None, one text, or a list of texts, one line each."""
        if isinstance(notes, (list, tuple)):
            self._set("notes", [_text_value(n, "notes") for n in notes])
        else:
            self._set("notes", _text_value(notes, "notes"))

    def set_header(self, header):
        if self.type != "doc-table":
            raise ModelError("bad_argument", f"{self.type} takes no header:")
        self._set("header", _bool_value(header, "header:"))


class LiveLoadTableModel(TableModel):
    """The live loads' table: a row's category of SIA 261 Tabelle 8 (`set_category`), its q_k and Q_k filled from it where they are `auto` and written over where they are a number (`override`, `clear_override`). No ψ: the Reduktionsbeiwerte are never a column of the live loads."""
    TYPES = ("live-load-table",)

    def _needs(self, column_id):
        if column_id not in self.column_ids():
            self._no_column(column_id)

    def set_category(self, row, category):
        """The row's category, `"B"`, as a string -- or None, which takes it off the row and leaves its values empty."""
        self._needs("category")
        rows = self._list("rows", of=dict)
        at = _index(rows, row, "row")
        if category is None:
            rows[at] = _drop(rows[at], "category")
        else:
            rows[at] = _put(rows[at], "category", _id_value(category, "category").strip(), self.column_ids())
        self._write_rows(rows)

    def category(self, row):
        return self.cell(row, "category")

    def override(self, row, column_id, number):
        """A value of the norm written over by the engineer's own number -- printed in orange."""
        if column_id not in LIVE_LOAD_FILLED:
            raise ModelError("not_filled", f"{column_id!r} is not filled from the category -- only {', '.join(LIVE_LOAD_FILLED)} are", column=column_id)
        self._needs(column_id)
        self.set_cell(row, column_id, _number_value(number, column_id))

    def clear_override(self, row, column_id):
        """The value back to the norm's: `auto`."""
        if column_id not in LIVE_LOAD_FILLED:
            raise ModelError("not_filled", f"{column_id!r} is not filled from the category -- only {', '.join(LIVE_LOAD_FILLED)} are", column=column_id)
        self._needs(column_id)
        self.set_cell(row, column_id, AUTO)

    def is_override(self, row, column_id):
        value = self.cell(row, column_id)
        return column_id in LIVE_LOAD_FILLED and isinstance(value, (int, float)) and not isinstance(value, bool)

    def set_cell(self, row, column_id, value):
        if column_id == "category":
            if not (isinstance(value, str) or value is None):
                raise ModelError("bad_value", f"a category of SIA 261 Tabelle 8 is a string, \"B\" -- got {value!r}", column=column_id)
            self.set_category(row, value)
            return
        super().set_cell(row, column_id, value)


class _Options(Model):
    """What a list to tick and a choice share: their label and their options, each a dictionary with an id and a label."""
    OPTION_KEYS = ()

    def __init__(self, call):
        super().__init__(call)
        for i, o in enumerate(self._list("options", of=dict)):
            if not isinstance(o.get("id"), str):
                raise ModelError("not_editable", f"{self.type}: option {i + 1} has no id Woodcore can read", argument="options")

    @property
    def label(self):
        return self.get("label")

    def set_label(self, label):
        self._set("label", _text_value(label, "label"))

    @property
    def options(self):
        return copy.deepcopy(self._list("options", of=dict))

    def option_ids(self):
        return [o["id"] for o in self._list("options", of=dict)]

    def _at(self, option_id):
        at = next((i for i, o in enumerate(self._list("options", of=dict)) if o["id"] == option_id), None)
        if at is None:
            raise ModelError("no_option", f"there is no option {option_id!r} -- the options are {', '.join(self.option_ids()) or 'none'}", option=option_id)
        return at

    def _new_option(self, option_id, fields, index):
        options = self._list("options", of=dict)
        option_id = _id_value(option_id, "an option's id")
        if option_id in self.option_ids():
            raise ModelError("id_exists", f"there is an option {option_id!r} already", option=option_id)
        entry = {"id": option_id}
        for key, value in fields:
            entry = _put(entry, key, value, self.OPTION_KEYS)
        at = _index(options, index, "option", insert=True)
        options.insert(at, entry)
        self._set("options", options)
        return at

    def _edit_option(self, option_id, key, value):
        options = self._list("options", of=dict)
        at = self._at(option_id)
        options[at] = _drop(options[at], key) if value is None else _put(options[at], key, value, self.OPTION_KEYS)
        self._set("options", options)

    def remove_option(self, option_id):
        options = self._list("options", of=dict)
        options.pop(self._at(option_id))
        self._set("options", options)

    def move_option(self, option_id, new_index):
        options = self._list("options", of=dict)
        _move(options, self._at(option_id), new_index, "option")
        self._set("options", options)

    def set_option_label(self, option_id, label):
        label = _text_value(label, "label")
        if label is None:
            raise ModelError("bad_value", "an option has a label")
        self._edit_option(option_id, "label", label)


class ChecklistModel(_Options):
    """A list to tick (`doc-checklist`): its label, its options -- id, label, ticked or not, and the paragraph printed under a ticked one -- and whether only the ticked ones are printed."""
    TYPES = ("doc-checklist",)
    OPTION_KEYS = CHECK_OPTION_KEYS

    def add_option(self, option_id, label, checked=False, text=None, index=None):
        label = _text_value(label, "label")
        if label is None:
            raise ModelError("bad_value", "an option has a label")
        fields = [("label", label), ("checked", _bool_value(checked, "checked"))]
        text = _text_value(text, "text")
        if text is not None:
            fields.append(("text", text))
        return self._new_option(option_id, fields, index)

    def set_checked(self, option_id, checked=True):
        self._edit_option(option_id, "checked", _bool_value(checked, "checked"))

    def is_checked(self, option_id):
        return bool(self._list("options", of=dict)[self._at(option_id)].get("checked", False))

    def set_option_text(self, option_id, text):
        self._edit_option(option_id, "text", _text_value(text, "text"))

    @property
    def only_checked(self):
        return self.get("only-checked")

    def set_only_checked(self, only=True):
        self._set("only-checked", _bool_value(only, "only-checked:"))


class ChoiceModel(_Options):
    """One choice among several (`doc-choice`): its label, its options, the one chosen -- or an answer of the engineer's own where none fits, the two never together -- and whether the answer alone is printed."""
    TYPES = ("doc-choice",)
    OPTION_KEYS = CHOICE_OPTION_KEYS

    def add_option(self, option_id, label, index=None):
        label = _text_value(label, "label")
        if label is None:
            raise ModelError("bad_value", "an option has a label")
        return self._new_option(option_id, [("label", label)], index)

    def remove_option(self, option_id):
        super().remove_option(option_id)
        if self.get("selected") == option_id:
            self._set("selected", None)

    @property
    def selected(self):
        return self.get("selected")

    @property
    def other(self):
        return self.get("other")

    def select(self, option_id):
        """The option chosen, by its id -- None chooses nothing. Takes an answer of the engineer's own off."""
        if option_id is not None:
            self._at(option_id)
            self._set("other", None)
        self._set("selected", option_id)

    def set_other(self, text):
        """An answer in the engineer's own words, where no option fits -- takes the option chosen off."""
        text = _text_value(text, "other")
        if text is not None:
            self._set("selected", None)
        self._set("other", text)

    @property
    def only_selected(self):
        return self.get("only-selected")

    def set_only_selected(self, only=True):
        self._set("only-selected", _bool_value(only, "only-selected:"))


class SignaturesModel(Model):
    """The signatures (`doc-signatures`): one row per signatory -- group, role, name, place, date, each left out where it is to be written by hand -- and whether the place and date are printed."""
    TYPES = ("doc-signatures",)

    def __init__(self, call):
        super().__init__(call)
        self._list("rows", of=dict)

    @property
    def rows(self):
        return copy.deepcopy(self._list("rows", of=dict))

    def add_row(self, index=None, **fields):
        rows = self._list("rows", of=dict)
        entry = {}
        for key, value in fields.items():
            if key not in SIGNATURE_KEYS:
                raise ModelError("bad_key", f"a signature row carries {', '.join(SIGNATURE_KEYS)} -- not {key!r}")
            value = _text_value(value, key)
            if value is not None:
                entry = _put(entry, key, value, SIGNATURE_KEYS)
        at = _index(rows, index, "row", insert=True)
        rows.insert(at, entry)
        self._set("rows", rows)
        return at

    def remove_row(self, index):
        rows = self._list("rows", of=dict)
        rows.pop(_index(rows, index, "row"))
        self._set("rows", rows)

    def move_row(self, index, new_index):
        rows = self._list("rows", of=dict)
        _move(rows, index, new_index, "row")
        self._set("rows", rows)

    def set_field(self, index, key, value):
        """One field of a row -- None takes it off, to be written by hand."""
        if key not in SIGNATURE_KEYS:
            raise ModelError("bad_key", f"a signature row carries {', '.join(SIGNATURE_KEYS)} -- not {key!r}")
        rows = self._list("rows", of=dict)
        at = _index(rows, index, "row")
        value = _text_value(value, key)
        rows[at] = _drop(rows[at], key) if value is None else _put(rows[at], key, value, SIGNATURE_KEYS)
        self._set("rows", rows)

    @property
    def place_date(self):
        return self.get("place-date")

    def set_place_date(self, shown=True):
        self._set("place-date", _bool_value(shown, "place-date:"))


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


class FieldModel(Model):
    """One labelled value (`doc-field`): its label, its value -- a number, markup, or none for «[…]» -- and its unit."""
    TYPES = ("doc-field",)

    def set_label(self, label):
        self._set("label", _text_value(label, "label"))

    def set_value(self, value):
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            self._set("value", _number_value(value, "value"))
        else:
            self._set("value", _text_value(value, "value"))

    def set_unit(self, unit):
        if unit is not None and not isinstance(unit, str):
            raise ModelError("bad_value", f"a unit is a string -- got {unit!r}")
        self._set("unit", unit)


def _width_value(width):
    if isinstance(width, Expr):
        return width
    try:
        return length(width)
    except ValueError as exc:
        raise ModelError("bad_value", f"width: {exc}") from None


class ImageModel(Model):
    """A picture of the document (`doc-image`): its file, as a path from the project's folder, its caption, its width and what its frame says while there is no file."""
    TYPES = ("doc-image",)

    def set_file(self, path):
        if path is not None:
            path = _id_value(path, "file:")
        self._set("file", path)

    def set_caption(self, caption):
        self._set("caption", _text_value(caption, "caption"))

    def set_width(self, width):
        self._set("width", _width_value(width))

    def set_placeholder(self, placeholder):
        self._set("placeholder", _text_value(placeholder, "placeholder"))


class PlanModel(Model):
    """An extract of a position plan (`doc-plan`): which plan, the positions set on a halo, the detail around them, its zoom, the axes, the legend, the scale bar, its width and its caption (`auto` the plan's own)."""
    TYPES = ("doc-plan",)

    def set_plan(self, plan):
        if plan is not None:
            plan = _id_value(plan, "plan:")
        self._set("plan", plan)

    def set_highlight(self, highlight):
        """None, one position, or several."""
        if isinstance(highlight, (list, tuple)):
            highlight = [_id_value(h, "highlight:") for h in highlight]
        elif highlight is not None:
            highlight = _id_value(highlight, "highlight:")
        self._set("highlight", highlight)

    def set_detail(self, detail=True):
        self._set("detail", _bool_value(detail, "detail:"))

    def set_zoom(self, zoom):
        self._set("zoom", _number_value(zoom, "zoom:"))

    def set_axes(self, shown=True):
        self._set("axes", _bool_value(shown, "axes:"))

    def set_dimensions(self, shown=True):
        """The plan's dimensions printed, or left out (issue #9)."""
        self._set("dimensions", _bool_value(shown, "dimensions:"))

    def set_lengths(self, shown=True):
        """The lengths beside the plan's elements printed, or left out (issue #9)."""
        self._set("lengths", _bool_value(shown, "lengths:"))

    def set_legend(self, shown=True):
        self._set("legend", _bool_value(shown, "legend:"))

    def set_scale_bar(self, shown=True):
        self._set("scale-bar", _bool_value(shown, "scale-bar:"))

    def set_width(self, width):
        self._set("width", _width_value(width))

    def set_caption(self, caption):
        self._set("caption", caption if caption is AUTO else _text_value(caption, "caption"))


class FirePlanModel(Model):
    """A fire-protection plan (`doc-fire-plan`, v0.115): which plan -- by its id in Woodcore's «Plan de protection incendie» tab --, the legend drawn on it, the scale bar, its width and its caption (`auto` the plan's own)."""
    TYPES = ("doc-fire-plan",)

    def set_plan(self, plan):
        if plan is not None:
            plan = _id_value(plan, "plan:")
        self._set("plan", plan)

    def set_legend(self, shown=True):
        self._set("legend", _bool_value(shown, "legend:"))

    def set_scale_bar(self, shown=True):
        self._set("scale-bar", _bool_value(shown, "scale-bar:"))

    def set_width(self, width):
        self._set("width", _width_value(width))

    def set_caption(self, caption):
        self._set("caption", caption if caption is AUTO else _text_value(caption, "caption"))


class ExtractModel(Model):
    """An excerpt of an annex (`doc-extract`, v0.115): which excerpt -- by its id in Woodcore's «Annexes» tab --, its width and its caption (`auto` the one `show-extract` writes: the source and its page)."""
    TYPES = ("doc-extract",)

    def set_excerpt(self, excerpt):
        if excerpt is not None:
            excerpt = _id_value(excerpt, "excerpt:")
        self._set("excerpt", excerpt)

    def set_width(self, width):
        self._set("width", _width_value(width))

    def set_caption(self, caption):
        self._set("caption", caption if caption is AUTO else _text_value(caption, "caption"))


class AnnexesModel(Model):
    """The annexes of the project at this point of the document (`doc-annexes`, v0.115): the level each annex's name is set as a heading at -- or none, its name in bold on its cover page."""
    TYPES = ("doc-annexes",)

    def set_heading(self, level):
        if level is not None and (isinstance(level, bool) or not isinstance(level, int) or level < 1):
            raise ModelError("bad_value", f"heading: is the level of a heading, 2, or none -- got {level!r}")
        self._set("heading", level)
