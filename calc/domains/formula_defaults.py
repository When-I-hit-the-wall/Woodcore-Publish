"""The domain's own options: the one line `#calc-defaults(…, scope: "domain")` under its header, read and written option by option (issue #113, spec docs/requirements/completed/2026-10-24-onglet-domaines-formulaire-code.md, REQ-004, D-3, ARCH-RISK-005).

A domain the tab makes opens on `#calc-defaults(presets: "block", scope: "domain")` (`NEW_LINE`, `formula_domain.new_domain`): printed one line a value, its label after it, its clause on the right -- what the files Woodcore writes for the snow or a check have (calc/domains/unfold.py writes the same line, its label `<ZT-01-presets>` behind it). A domain already written keeps what it has; «Affichage» switches each option on or off: ticked, it is written into the one line -- the line put under the header where there was none --; unticked, it is taken out of it; nothing left ticked, the line goes.

**No change to the parser**: `calc-defaults` is none of the commands a domain computes, so the line is a line of a text item (`formula_domain.split_items`), which `body_of` writes back as typed. It is found there, its arguments read with typst_objects' parser, and those this module does not set -- `level`, `display`, `unit`, a label after it -- kept as they are written. The options offered are those lib/formula.typ's `calc-default-names` accepts that a domain sets as a whole: their values are lib/display-presets.json's (`fine-values`, and its presets), read through calc/line_display.py -- nothing new in the engine.

No Qt.
"""

import json
import re
from dataclasses import dataclass, field, replace

import line_display
import typst_objects
import build_reference as ref
from domains import formula_domain as fd

# The options «Affichage» ticks, in the order the line writes them (T73)
OPTIONS = ("presets", "label-position", "descr-position", "norm-position", "style")
# The value an option is ticked with, the engineer's choice in the prototype (T73): «en bloc», the label after the line, the description as a footnote, the clause on the right, a plain line
PROPOSED = {"presets": "block", "label-position": "after", "descr-position": "footnote", "norm-position": "line-right", "style": "normal"}
SCOPE = "domain"
NEW_LINE = '#calc-defaults(presets: "block", scope: "domain")'
_LINE = re.compile(r"^(?P<lead>[ \t]*)#calc-defaults\(")


def values(name):
    """The values option `name` takes: a preset's name for `presets` (lib/display-presets.json, beside its tables), the fine values otherwise."""
    if name == "presets":
        data = json.loads(line_display.PRESETS.read_text(encoding="utf-8"))
        return tuple(k for k, v in data.items() if isinstance(v, dict) and k not in ("commands", "fine-values", "fine-keys"))
    return line_display.fine_values().get(name, ())


@dataclass
class Line:
    """The `#calc-defaults` line of a domain, as written: the text item that holds it (`index`), its line in that text (`row`), its indentation, the options set, every other argument as written (`others`: [(name, source)]), and what follows its `)` -- a label."""
    index: int
    row: int
    lead: str = ""
    options: dict = field(default_factory=dict)
    others: list = field(default_factory=list)
    tail: str = ""

    def text(self):
        """The line written again: the options in `OPTIONS`' order, every other argument as it was, `scope: "domain"` last."""
        parts = [f"{name}: {ref.typst_str(self.options[name])}" for name in OPTIONS if name in self.options]
        parts += [f"{name}: {source}" for name, source in self.others if name != "scope"]
        parts.append(f'scope: {ref.typst_str(SCOPE)}')
        return f"{self.lead}#calc-defaults({', '.join(parts)}){self.tail}"


def find(domain):
    """The domain's `#calc-defaults(…, scope: "domain")` line, or None: the first one a text item holds, standing alone on its line."""
    for index, c in enumerate(domain.commands):
        if not c.is_text:
            continue
        for row, line in enumerate(c.raw.split("\n")):
            found = _LINE.match(line)
            if not found:
                continue
            at = found.end() - len("#calc-defaults(")
            try:
                parser = typst_objects._Parser(line)
                call, end = parser.call(at, positional=True)
                spans, _end = fd._arguments(line, at)
            except (typst_objects.ParseError, ValueError):
                continue
            if call.positional or call.args.get("scope") != SCOPE:
                continue
            options, others = {}, []
            for key, (_start, _value, _stop, source) in spans.items():
                if key in OPTIONS and isinstance(call.args.get(key), str):
                    options[key] = call.args[key]
                elif isinstance(key, str):
                    others.append((key, source))
            return Line(index, row, found.group("lead"), options, others, line[end:])
    return None


def options(domain):
    """{option: value} the domain sets on its `#calc-defaults` line -- {} where it has none."""
    found = find(domain)
    return dict(found.options) if found is not None else {}


def is_block(domain):
    """Whether the domain is printed one line a value (`presets: "block"`): what the state warns of when not (REQ-011)."""
    return options(domain).get("presets") == "block"


def set_option(domain, name, value):
    """The domain's items with option `name` set to `value` on its `#calc-defaults` line -- written in, or, `value` None, taken out; the line put as the first line under the header where there is none, and taken away where no option is left set. The other items are the same objects (the tab knows a command by its identity)."""
    if name not in OPTIONS:
        raise fd.DomainError("defaults_option", f"calc-defaults: {name!r} is none of the domain's options -- {', '.join(OPTIONS)}", name=name)
    if value is not None and value not in values(name):
        raise fd.DomainError("defaults_value", f"calc-defaults: {name}: {value!r} -- {', '.join(values(name))}", name=name, value=value)
    items = list(domain.commands)
    found = find(domain)
    if found is None:
        if value is None:
            return items
        line = Line(0, 0, options={name: value})
        if items and items[0].is_text and items[0].raw.strip() and not items[0].raw.startswith("\n"):
            items[0] = replace(items[0], raw=line.text() + "\n" + items[0].raw)
        else:
            items.insert(0, fd.Command(fd.TEXT, raw=line.text()))
        return items
    if value is None:
        found.options.pop(name, None)
    else:
        found.options[name] = value
    rows = items[found.index].raw.split("\n")
    if found.options or [k for k, _s in found.others if k != "scope"]:
        rows[found.row] = found.text()
    else:
        del rows[found.row]
    raw = "\n".join(rows)
    if raw.strip():
        items[found.index] = replace(items[found.index], raw=raw)
    else:
        del items[found.index]
    return items
