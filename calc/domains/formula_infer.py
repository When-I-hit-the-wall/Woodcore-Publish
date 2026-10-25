"""What the engineer types in the «Domaines» tab, read as a line of the domain: the command a new line is, and a calculation typed with the symbols shown (issue #113, spec docs/requirements/completed/2026-10-24-onglet-domaines-formulaire-code.md, REQ-001, REQ-002, D-6, D-11, ARCH-RISK-004).

**The line inferred** (`infer_line`, the prototype's `inferLine`): «sigma_(m,d) <= f_(m,d)» holds a relation and is a `verify`; «h = 240 mm» a symbol, `=`, a number and a unit (or none) is a `var`; «M_d = q_d * l^2 / 8» a symbol and an expression is an `eq`; anything else is the engineer's own text. The key comes from the symbol (`formula_domain.key_from_symbol`: `M_(y,d)` → `M_y_d`), made unique among the keys taken. A command chosen on the pill wins over what is inferred: the same text is then read into that command's fields.

**A calculation typed with the symbols** (REQ-002, D-6): the field shows `sigma_(m,d) / f_(m,d)`, the file holds `sigma_m_d / f_m_d`. The translation is `formula_domain.typst_formula` and `display_formula`, the field «Calcul» of v0.117 -- not a second one --, given the table `symbol_table` makes: the lines **above** the line typed, each by the symbol it is typed with. A symbol is typed as such where it is a plain name with one subscript (`q_k`, `f_(m,d,"Tab")`, spaces after the commas allowed); a composed one -- (g_k + a_k)_"gew" -- is typed by its key, and so is a symbol two keys bear but the lowest: the higher is then typed by its key, and the table says so (`Table.shadowed`).

No Qt.
"""

import re
from dataclasses import dataclass, field

import units
from domains import formula_domain as fd

KINDS = ("var", "eq", "verify", "text")
_RELATION = re.compile(r"<=|>=|≤|≥|!=|≠|<|>")
_EQUALS = re.compile(r"^([^=<>≤≥]+?)\s*=\s*(.*)$", re.S)
_NUMBER_UNIT = re.compile(r"^(-?[0-9]+(?:[.,][0-9]+)?)\s*(.*)$", re.S)
# A symbol the engineer may type as it is shown: a name, and at most one subscript -- a word, a parenthesised list, a quoted word
_TYPABLE = re.compile(r'^[A-Za-z]+(?:_(?:[A-Za-z0-9]+|\([^()]*\)|"[^"]*"))?$')


@dataclass
class Inferred:
    """A line inferred from what is typed: its command (`kind`, one of KINDS), whether it was chosen rather than inferred, and its fields -- var: symbol, key, value, unit; eq: symbol, key, formula; verify: relation; text: text."""
    kind: str
    chosen: bool = False
    fields: dict = field(default_factory=dict)


def _number(text):
    text = text.replace(",", ".")
    return int(text) if re.fullmatch(r"-?[0-9]+", text) else float(text)


def infer_line(text, taken=(), kind=None):
    """The line `text` would be -- see the module's docstring -- None where nothing is typed. `taken` the keys the domain holds already; `kind`, a command chosen on the pill, which wins."""
    text = (text or "").strip()
    if not text and kind is None:
        return None
    inferred = _infer_kind(text)
    kind = kind or inferred
    out = Inferred(kind, chosen=kind != inferred)
    found = _EQUALS.match(text)
    if kind == "verify":
        out.fields = {"relation": text}
    elif kind == "text":
        out.fields = {"text": text}
    elif kind == "var":
        symbol, rest = (found.group(1).strip(), found.group(2).strip()) if found else (text, "")
        number = _NUMBER_UNIT.match(rest)
        value, unit = (number.group(1), number.group(2).strip()) if number else (rest, "")
        out.fields = {"symbol": symbol, "value": value, "unit": unit}
    else:
        symbol, formula = (found.group(1).strip(), found.group(2).strip()) if found else ("", text)
        out.fields = {"symbol": symbol, "formula": formula}
    if kind in ("var", "eq"):
        symbol = out.fields["symbol"]
        out.fields["key"] = fd.key_from_symbol(symbol, set(taken)) if symbol else ""
    return out


def _infer_kind(text):
    if _RELATION.search(text):
        return "verify"
    found = _EQUALS.match(text)
    if not found or not found.group(2).strip():
        return "text"
    number = _NUMBER_UNIT.match(found.group(2).strip())
    if number:
        unit = number.group(2).strip()
        if not unit or (units.parse_unit(units.written_unit(unit)) is not None and not re.search(r"[A-Za-z_]\w*\s*[*/+\-^]", unit)):
            return "var"
    return "eq"


def command_of(inferred, taken=(), variables=()):
    """The Command an inferred line writes (D-11): a key from its symbol, a calculation typed with the symbols written with the keys (`variables`, the table above it), a number read with a decimal comma. Raises formula_domain.DomainError `missing` (with the field) or `value`."""
    f, kind = inferred.fields, inferred.kind
    if kind == "text":
        if not f.get("text", "").strip():
            raise fd.DomainError("missing", "a text needs words", field="text")
        return fd.Command(fd.TEXT, raw=f["text"])
    if kind == "verify":
        relation = fd.typst_formula(f.get("relation", ""), list(variables))
        if not relation:
            raise fd.DomainError("missing", "a check needs its relation", field="relation")
        return fd.Command("verify", formula=relation)
    symbol = (f.get("symbol") or "").strip()
    key = (f.get("key") or "").strip() or (fd.key_from_symbol(symbol, set(taken)) if symbol else "")
    if not key:
        raise fd.DomainError("missing", "a line needs its symbol", field="symbol")
    if key in set(taken):
        raise fd.DomainError("key_taken", f"{key!r} is defined already in this domain", key=key)
    command = fd.Command(kind, key=key, symbol=fd.symbol_for(symbol, key))
    if kind == "var":
        try:
            command.value = _number((f.get("value") or "").replace(" ", ""))
        except ValueError:
            raise fd.DomainError("value", f"{f.get('value')!r} is not a number", text=f.get("value") or "")
        command.unit = units.written_unit((f.get("unit") or "").strip())
    else:
        command.formula = fd.typst_formula(f.get("formula", ""), list(variables))
        if not command.formula:
            raise fd.DomainError("missing", "an equation needs its calculation", field="formula")
        command.unit = units.written_unit((f.get("unit") or "").strip())
    if (f.get("label") or "").strip():
        command.options["label"] = f["label"].strip()
    return command


@dataclass
class Table:
    """The symbols a calculation is typed with on a line: [(key, what it is typed by)] of the lines above, in their order, and the keys whose symbol another key below bears (`shadowed`: typed by their key)."""
    pairs: list
    shadowed: list = field(default_factory=list)

    def typed(self, key):
        return dict(self.pairs).get(key, key)


def typed_symbol(symbol):
    """The symbol as it is typed -- its spaces taken out --, or "" where it is not typed as such (a composed symbol: typed by its key)."""
    plain = re.sub(r"\s+", "", symbol or "")
    return plain if plain and _TYPABLE.match(plain) else ""


def symbol_table(domain, upto=None, results=None):
    """The table of the lines above item `upto` (every line where None) -- see the module's docstring. `results` gives a linked variable the symbol of its source (REQ-010)."""
    commands = domain.commands if upto is None else domain.commands[:upto]
    keys = {c.key for c in domain.commands if c.defines}
    last = {}
    for i, c in enumerate(commands):
        if c.defines:
            last[c.key] = i
    by_symbol, typed = {}, {}
    for key, i in last.items():
        c = commands[i]
        r = results[i] if results is not None and i < len(results) else None
        s = typed_symbol(c.symbol or (r.symbol if r is not None else ""))
        if not s or s == key or (s in keys and s != key):
            continue
        typed[key] = s
        by_symbol.setdefault(s, []).append(i)
    shadowed = []
    for s, where in by_symbol.items():
        for i in sorted(where)[:-1]:   # the lowest keeps the symbol, the others are typed by their key
            shadowed.append(commands[i].key)
            typed.pop(commands[i].key, None)
    pairs = [(key, typed.get(key, key)) for key in sorted(last, key=last.get)]
    return Table(pairs, shadowed)


def to_symbols(formula, table):
    """A formula of the file as the field shows it: each key as the symbol it is typed by (`display_formula`)."""
    return fd.display_formula(formula, [(k, s) for k, s in table.pairs if s != k])


def to_keys(text, table):
    """A calculation typed with the symbols, as the file writes it (`typst_formula`): the keys, numbers with their units quoted."""
    return fd.typst_formula(text, table.pairs)
