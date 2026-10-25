"""The rows of the «Domaines» tab's «Formulaire»: a domain's items as the form shows them, the line of the file each begins on, and the gestures on them -- insert, delete, move one or several -- with the refusal of a move that would put a line above what it is computed from (issue #113, spec docs/requirements/completed/2026-10-24-onglet-domaines-formulaire-code.md, REQ-003, REQ-016, UI-005, ARCH-011, D-16).

**A row is an item of the domain** (ARCH-011): a command alone on its line, or a run of the engineer's own Typst (a text item, which may hold several lines of the file). Items **glued** on one line (`formula_domain.same_line`: `- $0°$ bis $30°$: #eq(…)`, spec 2026-10-14-commandes-en-ligne-domaine) are **one** row, a row of text that holds its commands (D-16) -- the file and what Typst prints never changing. A text that is only blank lines (the paragraph between two commands) is no row: it stays where it is in the items.

**Its number is the line it begins on in the file** (`item_lines`): counted on what `formula_domain.body_of` writes (`body_pieces`), from the header's line -- never guessed, and the same numbers the state of the domain names its faults by.

**A move is refused** when a line would stand above a line it is computed from (`order_refusal`, the keys each line reads being `formula_domain.compute`'s `Result.uses`): for every line of the rows moved and every line that stays, as Typst would stop on it. This replaces the drop of a pill (`fm_drop_order` of issue #40, formula_layout.py) for one row and for several.

No Qt. This module replaces calc/domains/formula_layout.py, the place of the pills (issue #40), which has no use since the pills are gone.
"""

from dataclasses import dataclass

from domains import formula_domain as fd
from domains import formula_links


@dataclass
class Row:
    """One row of the form: the items it holds (indices into `domain.commands`, in order), its kind -- `var`, `eq`, `verify`, or `text` for a text and for a line of text holding commands --, and the line of the file it begins on."""
    items: tuple
    kind: str
    line: int = 0

    @property
    def first(self):
        return self.items[0]

    def commands(self, domain):
        """The commands of the row (a text row's embedded ones too), with their indices."""
        return [(i, domain.commands[i]) for i in self.items if not domain.commands[i].is_text]


def _blank(c):
    return c.is_text and not c.raw.strip()


def header_line(domain):
    """The line of the file (from 1) the domain's header `#domain(…)[` stands on: after the lines before its body, the import's -- two for a file not yet written (`file_text`)."""
    if domain.text is None:
        return 3
    span, _why = fd._body_span(domain.text)
    return (span[0] + 1) if span is not None else 1


def item_lines(domain):
    """[the line of the file (from 1) each item of `domain` begins on] -- counted on the body `body_of` writes, piece by piece."""
    line = header_line(domain)
    out = [0] * len(domain.commands)
    first = True
    for index, text, glued in fd.body_pieces(domain):
        if not first and not glued:
            line += 1
        first = False
        if index is not None:
            out[index] = line
        line += text.count("\n")
    return out


def rows(domain):
    """The rows of `domain`, in order -- see the module's docstring."""
    lines = item_lines(domain)
    out, run = [], []
    commands = domain.commands
    for i, c in enumerate(commands):
        if run and fd.same_line(commands[run[-1]], c):
            run.append(i)
            continue
        if run:
            out.append(run)
        run = [i]
    if run:
        out.append(run)
    result = []
    for group in out:
        if len(group) == 1 and _blank(commands[group[0]]):
            continue
        c = commands[group[0]]
        kind = c.kind if len(group) == 1 and not c.is_text else "text"
        line = lines[group[0]]
        if len(group) == 1 and c.is_text:
            # a text that opens on a blank line (the paragraph after a command) begins where its words do
            line += len(c.raw) - len(c.raw.lstrip("\n")) if c.raw.strip() else 0
        result.append(Row(tuple(group), kind, line))
    return result


# --- the gestures ---------------------------------------------------------------------------------

def insert(domain, at, command):
    """The domain's items with `command` put before the item `at` (at the end where `at` is past it)."""
    items = list(domain.commands)
    at = len(items) if at is None or at > len(items) else max(0, at)
    items.insert(at, command)
    return items


def insert_before_row(domain, row_index, commands):
    """The items with `commands` put before the row `row_index` of `rows(domain)` (at the end past the last): where the + between two rows, a line typed at the foot and «Valider» of the links write. Returns (items, the index of the first one put)."""
    shown = rows(domain)
    at = shown[row_index].first if 0 <= row_index < len(shown) else len(domain.commands)
    items = list(domain.commands)
    for k, command in enumerate(commands):
        items.insert(at + k, command)
    return items, at


def delete(domain, row_indices):
    """The items without the rows `row_indices` -- every item of each, its glued commands with it."""
    shown = rows(domain)
    gone = {i for r in row_indices if 0 <= r < len(shown) for i in shown[r].items}
    return [c for i, c in enumerate(domain.commands) if i not in gone]


def symbol_of(domain, index, results=None):
    """What a refusal names a line by: its symbol, else its key, else its kind -- a relation for a check."""
    c = domain.commands[index]
    r = results[index] if results is not None and index < len(results) else None
    if c.kind == "verify":
        return c.formula
    return c.symbol or (r.symbol if r is not None else "") or c.key or c.kind


def order_refusal(domain, results, order, moved):
    """None where the items of `domain` may stand in `order` (a permutation of their indices); else ("order", user, used): the first line that would stand above a line it is computed from -- `user` reads `used`, which would be lower. `moved` the indices moved, which come first in the search, as the prototype's `orderCheck` does."""
    position = {old: new for new, old in enumerate(order)}
    deps = formula_links.dependencies(domain, results)
    for j in sorted(position, key=lambda j: (j not in moved, position[j])):
        for d in deps.get(j, {}).get("uses", ()):
            if position[d] > position[j]:
                return ("order", symbol_of(domain, j, results), symbol_of(domain, d, results))
    return None


def move(domain, results, row_indices, target):
    """The rows `row_indices` moved together, in their order, before the row `target` (past the last row: at the end). Returns (items, None), or (None, refusal) where a line would stand above what it is computed from (`order_refusal`) -- the domain unchanged. A move that changes nothing gives (None, None)."""
    shown = rows(domain)
    picked = sorted(set(r for r in row_indices if 0 <= r < len(shown)))
    if not picked:
        return None, None
    moved = [i for r in picked for i in shown[r].items]
    rest = [i for i in range(len(domain.commands)) if i not in set(moved)]
    while target < len(shown) and target in picked:
        target += 1
    at = rest.index(shown[target].first) if target < len(shown) else len(rest)
    order = rest[:at] + moved + rest[at:]
    if order == list(range(len(domain.commands))):
        return None, None
    refusal = order_refusal(domain, results, order, set(moved))
    if refusal is not None:
        return None, refusal
    return [domain.commands[i] for i in order], None
