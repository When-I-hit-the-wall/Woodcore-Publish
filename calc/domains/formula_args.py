"""The arguments of a line of a domain, as the module «Arguments de la ligne» of the «Domaines» tab offers them, and written into the line (issue #113, spec docs/requirements/completed/2026-10-24-onglet-domaines-formulaire-code.md, REQ-008, REQ-009, UI-012, ARCH-RISK-003, ARCH-RISK-010).

**Which arguments** (T44): first what the line *is* -- `var`: its key, symbol, value, unit; `eq`: its key, symbol, calculation, unit, `as-unit`; `verify`: its relation; and for every one its label, description, norm and clause (`norm-section`, «Article», REQ-008) --, then **how it is printed**, the one list «Affichage» of the snow and the unfolded checks set too (calc/line_display.py: lib/display-presets.json's `fine-keys`, then `style`, `role`, `level`), their values that file's `fine-values` -- no list here, no second dictionary (ARCH-006). *auto* writes nothing: the argument is taken out of the line. `role` is offered on `#var` too, which T44 leaves out and the engine accepts (P-4).

**In «Code»** (UI-012, ARCH-016) the module follows the cursor: `command_at` recognises the command of the line it stands on -- at once, without compiling -- and `line_edit` gives the lines of the buffer to replace, which the editor replaces in **one** edit, the cursor and the scroll staying. **In «Formulaire»** the row shows what the line is, and the module the rest (`OTHERS`).

No Qt.
"""

import re
from dataclasses import dataclass, replace

import line_display
import units
from domains import formula_domain as fd
from domains import formula_rows

# What a line is, by command, in the order the module offers it (T44)
CORE = {
    "var": ("key", "symbol", "value", "unit", "label", "descr", "norm", "norm-section"),
    "eq": ("key", "symbol", "formula", "unit", "label", "descr", "norm", "norm-section", "as-unit"),
    "verify": ("formula", "label", "descr", "norm", "norm-section"),
}
# What a row of the form shows itself, under it once chosen (UI-005, UI-006): the module in «Formulaire» shows the others
IN_ROW = ("key", "symbol", "value", "unit", "formula", "label", "descr", "norm", "norm-section")
LEVELS = ("0", "1", "2", "3")


@dataclass
class Argument:
    """One argument of a line: its name, its kind -- `text` (typed), `choice` (a list, *auto* first), `unit` (the units of the result's dimension) --, the values of a list, and its value now ("" where the line leaves it out)."""
    name: str
    kind: str
    choices: tuple = ()
    value: str = ""


def names(kind, everything=True):
    """The arguments of a line of `kind` (var, eq, verify), in order: what it is (with `everything`), then how it is printed (calc/line_display.py). () for a text."""
    if kind not in CORE:
        return ()
    core = CORE[kind] if everything else tuple(n for n in CORE[kind] if n not in IN_ROW)
    return core + tuple(n for n in line_display.display_args(kind) if n not in core)


def value_of(command, name, table=None):
    """The argument `name` of `command` as the module shows it: a calculation in the symbols of `table` (formula_infer.Table) where given."""
    if name == "key":
        return command.key
    if name == "symbol":
        return command.symbol
    if name == "value":
        return "" if command.value is None or command.source else str(command.value)
    if name == "unit":
        return command.unit
    if name == "formula":
        if table is not None:
            from domains import formula_infer
            return formula_infer.to_symbols(command.formula, table)
        return command.formula
    value = command.options.get(name)
    return "" if value is None else str(value)


def arguments(command, everything=True, result=None, table=None):
    """[Argument] of `command` -- see the module's docstring. A variable linked from elsewhere has no value, unit nor symbol of its own to set. `result` gives an `#eq`'s unit its choices: the units of its dimension."""
    fine = line_display.fine_values()
    out = []
    for name in names(command.kind, everything):
        if command.source and command.source[0] == "domain" and name in ("value", "unit", "symbol"):
            continue
        if name == "level":
            out.append(Argument(name, "choice", LEVELS, value_of(command, name)))
        elif name in fine:
            out.append(Argument(name, "choice", line_display.values(command.kind, name), value_of(command, name)))
        elif name == "unit" and command.kind == "eq":
            out.append(Argument(name, "unit", units_of(result), value_of(command, name)))
        else:
            out.append(Argument(name, "text", (), value_of(command, name, table)))
    return out


def units_of(result):
    """The units an `#eq`'s result may be given in: those of its dimension (units.offered_units), () where it does not compute."""
    if result is None or result.error or not result.unit:
        return ()
    parsed = units.parse_unit(result.unit)
    return tuple(u for u in units.offered_units(parsed[1]) if u) if parsed else ()


def set_argument(command, name, value, table=None):
    """`command` with argument `name` set to `value` -- "" or None taking it out of the line (*auto*). A calculation is typed with the symbols of `table`. Raises formula_domain.DomainError `key_invalid` or `value`. The command returned is a copy: the line is written once the domain is saved."""
    value = "" if value is None else str(value)
    options = dict(command.options)
    if name == "key":
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", value):
            raise fd.DomainError("key_invalid", f"{value!r} is no key: letters, digits and _", key=value)
        return replace(command, key=value, options=options)
    if name == "symbol":
        return replace(command, symbol=fd.symbol_for(value, command.key), options=options)
    if name == "value":
        try:
            number = value.replace(",", ".").replace(" ", "")
            parsed = int(number) if number.lstrip("-").isdigit() else float(number)
        except ValueError:
            raise fd.DomainError("value", f"{value!r} is not a number", text=value)
        return replace(command, value=parsed, options=options)
    if name == "unit":
        return replace(command, unit=units.written_unit(value.strip()), options=options)
    if name == "formula":
        if table is not None:
            from domains import formula_infer
            value = formula_infer.to_keys(value, table)
        return replace(command, formula=value, options=options) if value.strip() else command
    if name == "norm-section":
        options.pop("norm-ref", None)   # one argument, never the two (REQ-008)
    if value == "":
        options.pop(name, None)
    elif name == "level":
        options[name] = int(value)
    else:
        options[name] = value
    return replace(command, options=options)


def written(command):
    """The line as the file writes the command (`formula_domain.to_call`) -- what the module shows under the arguments; as written where the tab has not changed it."""
    if command.written and fd.to_call(command) == command.read_call:
        return command.written.strip()
    if command.written:
        return fd.patched(command.written, command.read_call, fd.to_call(command)).strip()
    return fd.to_call(command)


# --- «Code»: the command of the cursor ---------------------------------------------------------------

@dataclass
class AtLine:
    """What stands on a line of the buffer: the item's index (None where the buffer does not read), the command's kind (`var`, `eq`, `verify`, `text`), the line it begins on, and whether it reads."""
    index: object
    kind: str
    first: int
    reads: bool = True


def command_at(domain, line, text=None):
    """The command of line `line` (from 1) of the domain's file -- `domain` read from the buffer (formula_domain.parse_text) -- or, the buffer not reading, what its line opens with (`#var(`, `#eq(`, `#verify(`), said unread (`reads` False). None for a line out of the body."""
    if domain.state != "unreadable":
        lines = formula_rows.item_lines(domain)
        for i in range(len(domain.commands) - 1, -1, -1):
            c = domain.commands[i]
            last = lines[i] + (c.raw if c.is_text else (c.written or fd.to_call(c))).count("\n")
            if lines[i] <= line <= last:
                return AtLine(i, c.kind if not c.is_text else "text", lines[i])
        return None
    import re
    rows = (text if text is not None else domain.text or "").split("\n")
    if 1 <= line <= len(rows):
        found = re.match(r"\s*#(var|eq|verify)\(", rows[line - 1])
        if found:
            return AtLine(None, found.group(1), line, reads=False)
    return None


def line_edit(domain, index, command):
    """(first line, last line, new text) of the file -- lines from 1 -- that writing `command` in place of item `index` changes: what «Code» replaces in its buffer by one edit (ARCH-016)."""
    lines = formula_rows.item_lines(domain)
    old = domain.commands[index]
    first = lines[index]
    last = first + (old.written or "  " + fd.to_call(old)).count("\n")
    if old.written:
        new = fd.patched(old.written, old.read_call, fd.to_call(command)) if fd.to_call(command) != old.read_call else old.written
    else:
        new = "  " + fd.to_call(command)
    return first, last, new


# --- the domain's level, `#domain(…, level: n)` (UI-021) ----------------------------------------------

_LEVEL = re.compile(r",\s*level:\s*[^,)]+")


def domain_level(domain):
    """The level the domain's header gives its lines, None where it leaves it to the report («auto»)."""
    found = re.search(r"level:\s*(\d)", domain.header_written or "")
    return int(found.group(1)) if found else None


def with_domain_level(domain, level):
    """The file's text with the header's `level:` set to `level` (1, 2, 3) or taken out (None) -- everything else of the header and of the file as it stands. Raises formula_domain.DomainError `value` for another level."""
    if level not in (None, 1, 2, 3):
        raise fd.DomainError("value", f"level {level!r} -- 1, 2, 3 or none", text=str(level))
    text = domain.text or ""
    head = domain.header_written
    if not head or head not in text:
        raise fd.DomainError("unreadable", "the domain's header cannot be found", file=domain.id, reason="header")
    inner = head[:head.rindex(")")]
    inner = _LEVEL.sub("", inner)
    new = inner + (f", level: {level}" if level is not None else "") + head[head.rindex(")"):]
    return text.replace(head, new, 1)
