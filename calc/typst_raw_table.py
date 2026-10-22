"""A table written in raw Typst, `#table(…)` -- alone or in a `#figure(table(…), caption: […])` --, read into a model the «Structure du document» tab edits without showing any code, and written back (spec docs/requirements/completed/2026-10-21-commandes-typst-refonte.md, ARCH-004, REQ-019, Q-012; docs/architecture/principles.md, rule 15).

**The subset read** (ARCH-004): the named arguments, `columns:` -- a number or an array of widths -- and `align:` -- one alignment or an array -- edited, every other kept verbatim; the positional arguments a cell `[…]`, a `table.header([…], …)` and a `table.hline(…)`. Anything else -- a spread `..rows`, a `for`, a `table.cell(colspan: …)`, a `columns:` computed, cells that do not fill the last row -- makes the table **read only** (`RawTableError` `not_editable`): it is shown, never rewritten nor replaced.

**Written by replacing a span** (ARCH-004): a cell set rewrites its brackets' content alone, every other byte of the file kept; a row or a column added, moved or removed, a column hidden or aligned, rewrites the table's own arguments, one row a line, and nothing outside the call. A table read and written back unchanged is the same bytes.

**What the panel keeps** (Q-012): a column **hidden** -- kept, not printed -- and its **alignment**. A hidden column is not in `columns:` nor in `align:`; its cells are kept in a Typst comment at the end of each line, `// woodcore:hidden 3=[…]`, the column's place `3` (from 1, among all the columns) and its content, which Typst never prints and Woodcore reads back. The unit and the id of a column, a category and the orange override of the live loads have no raw form and are gone with `#doc-table` and `#live-load-table`.

Qt-free; the call is found by calc/typst_calls.py, which knows where a string or a bracket stops.
"""

import re
from dataclasses import dataclass

import typst_calls

HIDDEN = "// woodcore:hidden"
INDENT = "  "


class RawTableError(ValueError):
    """A table Woodcore does not edit, with a code: `no_table` (no `table(` in the body), `not_editable` (out of the subset, said why)."""

    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


@dataclass
class RawColumn:
    """One column of a raw table: its id (stable while the model lives), its width and its alignment as Typst writes them, its heading's content, whether it is hidden."""
    id: str
    width: str = "auto"
    align: str = None
    title: str = None
    hidden: bool = False
    known: bool = False    # what the table pane reads of a doc-table's column: a raw table knows no column by its id
    kind: str = None
    unit: str = None


def _content(text):
    """The markup between a cell's brackets, or None where `text` is no `[…]` alone."""
    text = text.strip()
    if not text.startswith("["):
        return None
    end = typst_calls.closing(text, 0)
    return text[1:end] if end == len(text) - 1 else None


def _items(text):
    """The items of an array literal `(a, b, c)` as written, or None where `text` is none."""
    text = text.strip()
    if not (text.startswith("(") and text.endswith(")")) or typst_calls.closing(text, 0) != len(text) - 1:
        return None
    inner = text[1:-1]
    return [inner[a:b].strip() for a, b in typst_calls.split(inner) if inner[a:b].strip()]


def _hidden_cells(line):
    """{place: content} of the comment `// woodcore:hidden 3=[…] 5=[…]` a line of the table ends with."""
    at = line.find(HIDDEN)
    if at < 0:
        return {}
    rest, out = line[at + len(HIDDEN):], {}
    i = 0
    while i < len(rest):
        found = re.compile(r"\s*(\d+)=\[").match(rest, i)
        if not found:
            break
        start = found.end() - 1
        end = typst_calls.closing(rest, start)
        if end is None:
            break
        out[int(found.group(1))] = rest[start + 1:end]
        i = end + 1
    return out


def _strip_comment(text):
    """`text` without the hidden cells' comment that ends one of its lines."""
    return re.sub(r"[ \t]*" + re.escape(HIDDEN) + r"[^\n]*", "", text)


class RawTableModel:
    """The model of a raw table: its columns (`RawColumn`), its rows (lists of the cells' content, one per column, hidden ones included), whether it has a header, its figure's caption. The operations are `TableModel`'s -- what the table pane calls -- and `to_body()` gives the body back."""

    type = "table"

    def __init__(self, body):
        self.body = body
        self._parse()
        self._structure = False   # True once an operation changed more than a cell: the table's arguments are written again

    @classmethod
    def from_body(cls, body):
        return cls(body)

    # -- reading ----------------------------------------------------------------------------------------------------

    def _parse(self):
        text = self.body
        found = re.search(r"(?<![\w.-])table\(", text)
        if not found:
            raise RawTableError("no_table", "no table( in this object -- it is no raw table")
        self.open = found.end() - 1
        self.close = typst_calls.closing(text, self.open)
        if self.close is None:
            raise RawTableError("not_editable", "the table's ( is never closed")
        args = text[self.open + 1:self.close]
        self.named, positional = [], []
        columns_text = align_text = None
        for a, b in typst_calls.split(args):
            raw = args[a:b]
            item = typst_calls.mask_comments(_strip_comment(raw)).strip()   # a comment the engineer wrote is no argument: the table is read, and is hand-edited since Woodcore would not write it
            if not item:
                continue
            if item.startswith(".."):
                raise RawTableError("not_editable", "a spread (..) in the table's arguments -- Woodcore shows the table and leaves it as written")
            key = re.match(r"([A-Za-z_][A-Za-z0-9_-]*)\s*:(?!:)", item)
            if key and not item.startswith("["):
                name, value = key.group(1), item[key.end():].strip()
                if name == "columns":
                    columns_text = value
                elif name == "align":
                    align_text = value
                else:
                    self.named.append((name, value))
                continue
            positional.append((self.open + 1 + a, self.open + 1 + b, item))
        # the columns: a number, or an array of widths
        if columns_text is None:
            widths = ["auto"]
        elif re.fullmatch(r"\d+", columns_text):
            widths = ["auto"] * int(columns_text)
        else:
            widths = _items(columns_text)
            if widths is None:
                raise RawTableError("not_editable", f"columns: {columns_text} is computed -- Woodcore edits a number or an array of widths")
        n = len(widths)
        if align_text is None:
            aligns = [None] * n
        else:
            listed = _items(align_text)
            aligns = listed if listed is not None else [align_text] * n
            if len(aligns) != n:
                raise RawTableError("not_editable", f"align: names {len(aligns)} alignments for {n} columns")
        # the hidden columns, named by the comment of the header line, or of the first row's
        lines = text[self.open:self.close].split("\n")
        hidden_places = sorted({place for line in lines for place in _hidden_cells(line)})
        total = n + len(hidden_places)
        shown_places = [p for p in range(1, total + 1) if p not in hidden_places]
        self.columns = []
        for place in range(1, total + 1):
            if place in hidden_places:
                self.columns.append(RawColumn(f"c{place}", hidden=True))
            else:
                k = shown_places.index(place)
                self.columns.append(RawColumn(f"c{place}", widths[k], aligns[k]))
        # the header, the cells and the lines
        self.header = False
        self.rows, self.hlines, self._spans = [], [], {}
        cells = []
        for start, end, item in positional:
            line = self.body[self.body.rfind("\n", 0, end) + 1:self.body.find("\n", end) if self.body.find("\n", end) >= 0 else len(self.body)]
            if item.startswith("table.header("):
                inner_open = item.index("(")
                inner = item[inner_open + 1:typst_calls.closing(item, inner_open)]
                titles = [_content(inner[a:b]) for a, b in typst_calls.split(inner) if inner[a:b].strip()]
                if any(t is None for t in titles) or len(titles) != n:
                    raise RawTableError("not_editable", "a header that is not one cell [...] for each column")
                hidden = _hidden_cells(line)
                k = 0
                for column in self.columns:
                    if column.hidden:
                        column.title = hidden.get(int(column.id[1:]))
                    else:
                        column.title = titles[k]
                        k += 1
                self.header = True
            elif item.startswith("table.hline("):
                # where a line stands: above the header, right under it, before a row, at the end -- the three rules of a document's table (doc-tables)
                where = "top" if not self.header and not cells else "header" if not cells else len(cells) // n
                self.hlines.append((where, item))
            else:
                content = _content(item)
                if content is None:
                    raise RawTableError("not_editable", f"{item[:40]!r} is no cell [...] -- a table.cell, a for or a call: Woodcore shows the table and leaves it as written")
                offset = self.body.index("[", start) + 1
                cells.append((content, offset, line))
        if len(cells) % n:
            raise RawTableError("not_editable", f"{len(cells)} cells do not fill rows of {n} columns")
        # a line after the last row is the table's end: it stays last when a row is added
        self.hlines = [("end" if at == len(cells) // n and cells else at, item) for at, item in self.hlines]
        for r in range(len(cells) // n):
            chunk = cells[r * n:(r + 1) * n]
            hidden = _hidden_cells(chunk[-1][2])
            row, k = [], 0
            for column in self.columns:
                if column.hidden:
                    row.append(hidden.get(int(column.id[1:]), ""))
                else:
                    content, offset, _line = chunk[k]
                    self._spans[(r, column.id)] = (offset, offset + len(content))
                    row.append(content)
                    k += 1
            self.rows.append(row)
        # the caption of the figure the table stands in, where it stands in one
        self.caption_span = None
        before = text[:found.start()]
        figure = re.search(r"figure\(\s*$", before)
        if figure:
            fig_open = before.rindex("(")
            fig_close = typst_calls.closing(text, fig_open)
            if fig_close is not None:
                fig_args = text[fig_open + 1:fig_close]
                for a, b in typst_calls.split(fig_args):
                    part = fig_args[a:b]
                    key = re.match(r"\s*caption\s*:\s*", part)
                    if key and _content(part[key.end():]) is not None:
                        bracket = fig_open + 1 + a + key.end() + (len(part[key.end():]) - len(part[key.end():].lstrip()))
                        self.caption_span = (bracket + 1, typst_calls.closing(text, bracket))

    # -- what the pane reads ---------------------------------------------------------------------------------------

    def column_ids(self):
        return [c.id for c in self.columns]

    @property
    def row_count(self):
        return len(self.rows)

    def _at(self, column_id):
        for i, c in enumerate(self.columns):
            if c.id == column_id:
                return i
        raise RawTableError("no_column", f"no column {column_id!r}")

    def column(self, column_id):
        return self.columns[self._at(column_id)]

    def is_hidden(self, column_id):
        return self.column(column_id).hidden

    def cell(self, row, column_id):
        return self.rows[row][self._at(column_id)]

    def get(self, name):
        """What the pane reads of the table as a whole: its caption (the figure's), its notes (a raw table has none), whether it has a header."""
        if name == "caption":
            return None if self.caption_span is None else self.body[self.caption_span[0]:self.caption_span[1]]
        if name == "notes":
            return None
        if name == "header":
            return self.header
        raise RawTableError("bad_argument", f"a raw table has no {name!r}")

    # -- what the pane changes ---------------------------------------------------------------------------------------

    def set_cell(self, row, column_id, value):
        """A cell set: its brackets' content rewritten alone where the table's shape has not changed (ARCH-004), the rows written again otherwise."""
        text = "" if value is None else str(getattr(value, "markup", value))
        if "\n" in text:
            text = " ".join(text.split("\n"))
        at = self._at(column_id)
        self.rows[row][at] = text
        span = self._spans.get((row, column_id))
        if span is not None and not self._structure and not self.columns[at].hidden:
            start, end = span
            delta = len(text) - (end - start)
            self.body = self.body[:start] + text + self.body[end:]
            self._spans = {k: ((s + delta, e + delta) if s >= end else ((s, e + delta) if k == (row, column_id) else (s, e))) for k, (s, e) in self._spans.items()}
            if self.close >= end:
                self.close += delta
            if self.caption_span and self.caption_span[0] >= end:
                self.caption_span = (self.caption_span[0] + delta, self.caption_span[1] + delta)
        else:
            self._structure = True

    def clear_cell(self, row, column_id):
        self.set_cell(row, column_id, "")

    def add_row(self, index=None, values=None):
        index = len(self.rows) if index is None else index
        self.rows.insert(index, ["" for _c in self.columns])
        self._structure = True
        return index

    def remove_row(self, index):
        del self.rows[index]
        self._structure = True

    def move_row(self, index, new_index):
        self.rows.insert(new_index, self.rows.pop(index))
        self._structure = True

    def add_column(self, column_id, title=None, unit=None, kind=None, index=None):
        if column_id in self.column_ids():
            raise RawTableError("id_exists", f"a column {column_id!r} is there already")
        index = len(self.columns) if index is None else index
        self.columns.insert(index, RawColumn(column_id, "auto", None, title or ""))
        for row in self.rows:
            row.insert(index, "")
        self._structure = True

    def remove_column(self, column_id):
        at = self._at(column_id)
        del self.columns[at]
        for row in self.rows:
            del row[at]
        self._structure = True

    def move_column(self, column_id, new_index):
        at = self._at(column_id)
        self.columns.insert(new_index, self.columns.pop(at))
        for row in self.rows:
            row.insert(new_index, row.pop(at))
        self._structure = True

    def set_hidden(self, column_id, hidden=True):
        column = self.column(column_id)
        if hidden and not column.hidden and sum(1 for c in self.columns if not c.hidden) == 1:
            raise RawTableError("last_column", "the last column printed cannot be hidden")
        column.hidden = bool(hidden)
        self._structure = True

    def hide_column(self, column_id):
        self.set_hidden(column_id, True)

    def show_column(self, column_id):
        self.set_hidden(column_id, False)

    def set_column(self, column_id, *, title=None, unit=None, kind=None):
        self.column(column_id).title = "" if title is None else str(getattr(title, "markup", title))
        self.header = True
        self._structure = True

    def set_align(self, column_id, align):
        """A column's alignment -- `left`, `center`, `right` or None for the table's own -- written into `align:` (Q-012)."""
        if align not in (None, "left", "center", "right"):
            raise RawTableError("bad_align", f"align {align!r} -- left, center or right")
        self.column(column_id).align = align
        self._structure = True

    def set_header(self, header):
        self.header = bool(header)
        self._structure = True

    def set_caption(self, caption):
        """The figure's caption rewritten alone; a table in no figure has none to set."""
        if self.caption_span is None:
            raise RawTableError("no_caption", "the table stands in no #figure: its caption is written around it")
        start, end = self.caption_span
        text = "" if caption is None else str(caption)
        self.body = self.body[:start] + text + self.body[end:]
        delta = len(text) - (end - start)
        self.caption_span = (start, end + delta)
        if start < self.open:
            self.open += delta
            self.close += delta
            self._spans = {k: (s + delta, e + delta) for k, (s, e) in self._spans.items()}

    def set_notes(self, notes):
        if notes:
            raise RawTableError("no_notes", "a raw table carries no notes: write them under it, as a paragraph")

    # -- writing ---------------------------------------------------------------------------------------------------

    def _arguments(self, indent):
        """The table's arguments as Woodcore writes them: `columns:`, `align:` where a column has one, the other named ones as written, the header, one row a line -- the hidden columns' cells in the comment at its end --, the lines where they stood."""
        inner = indent + INDENT
        shown = [c for c in self.columns if not c.hidden]
        hidden = [(i + 1, c) for i, c in enumerate(self.columns) if c.hidden]
        widths = [c.width for c in shown]
        lines = [inner + "columns: " + (str(len(shown)) if all(w == "auto" for w in widths) else "(" + ", ".join(widths) + (",)" if len(widths) == 1 else ")")) + ","]
        if any(c.align for c in shown):
            aligns = [c.align or "auto" for c in shown]
            lines.append(inner + "align: (" + ", ".join(aligns) + (",)" if len(aligns) == 1 else ")") + ",")
        lines += [inner + f"{name}: {value}," for name, value in self.named]

        def tail(contents):
            # the hidden columns' cells, in the comment at the end of the line, by their place among all the columns
            parts = [f"{place}=[{contents[place - 1]}]" for place, _c in hidden]
            return ("  " + HIDDEN + " " + " ".join(parts)) if parts else ""

        hlines = dict()
        for at, item in self.hlines:
            hlines.setdefault(at if isinstance(at, str) else min(at, len(self.rows)), []).append(item)
        lines += [inner + item + "," for item in hlines.get("top", [])]
        if self.header:
            titles = [c.title or "" for c in self.columns]
            lines.append(inner + "table.header(" + ", ".join(f"[{c.title or ''}]" for c in shown) + ")," + tail(titles))
        lines += [inner + item + "," for item in hlines.get("header", [])]
        for r, row in enumerate(self.rows):
            lines += [inner + item + "," for item in hlines.get(r, [])]
            cells = [row[i] for i, c in enumerate(self.columns) if not c.hidden]
            lines.append(inner + ", ".join(f"[{c}]" for c in cells) + "," + tail(row))
        lines += [inner + item + "," for item in hlines.get(len(self.rows), []) + hlines.get("end", [])]
        return "\n" + "\n".join(lines) + "\n" + indent

    def to_body(self):
        """The body to write between the object's tags: as it was read where nothing changed, its cells rewritten in place where only cells did, the table's arguments written again once its shape changed -- every byte outside the call kept."""
        if not self._structure:
            return self.body
        line_start = self.body.rfind("\n", 0, self.open) + 1
        indent = re.match(r"[ \t]*", self.body[line_start:]).group(0)
        return self.body[:self.open + 1] + self._arguments(indent) + self.body[self.close:]
