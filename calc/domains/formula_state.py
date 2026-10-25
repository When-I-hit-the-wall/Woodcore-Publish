"""The state of a domain of the «Domaines» tab: what is wrong with it, what is worth knowing, each said once, at its line (issue #113, spec docs/requirements/completed/2026-10-24-onglet-domaines-formulaire-code.md, REQ-005, REQ-006, REQ-007, REQ-011, REQ-013, REQ-015, UI-009, UI-015).

**Red** (`error`): the file does not read -- at the line and column Typst names (formula_errors.read_fault) --; a name nobody declared above; two dimensions added; a link that finds nothing. **A fault is said once** (REQ-006): a line that fails only because a line above it does (`Result.blocked_by`) is no error of its own -- it is counted with its cause, «3 lignes plus bas en dépendent», and its row is marked `blocked`, not red.

**Orange** (`warning`, the file compiles): a check that does not hold (D-7, the engineer's answer 6: news of the structure, not a fault of the file); a unit asked for that is not the result's; a domain of the tab read by its name that is not printed above in a document (D-8, calc/domains/formula_order.py); a domain without `presets: "block"`, printed in one paragraph -- which leads to the domain's options.

**The fix of a message** (REQ-013, D-5): a name unknown here that the export knows offers its link -- «Lier q_k1 depuis Neige · SL» --, the same `#var(…, domain: …)` the other two ways write.

Every message is a code and its values, which the window words in its own language (`fm_e_<code>`, `fm_w_<code>`; calc/tools/formula_tab_words.py), never cut; the report keeps Typst's English. **The colour of a row** (UI-009) is its message's; a line of a check unfolded by a specialised tab takes the colour of its state there (REQ-015, ARCH-RISK-018): a conflict and a line taken out red, a line changed outside Woodcore and data changed orange, the engineer's own value the accent, a line in step none. The colours' tokens are calc/tools/theme.json's.

No Qt.
"""

from dataclasses import dataclass, field

import units
from domains import formula_defaults

# The theme token of a row's stripe, by its state (UI-009, ARCH-RISK-018)
COLOURS = {"error": "danger", "warning": "warning", "blocked": "muted", "own": "accent",
           "conflict": "danger", "missing": "danger", "local": "warning", "data": "warning"}
# A line of an unfolded check, by its state in calc/domains/unfold.py, as its row's stripe says it
UNFOLD_STATES = ("conflict", "missing", "local", "data", "own")


@dataclass
class Message:
    """One message of the state: `level` error or warning, a `code` the window words, its `values`, the item it is about (None for the file or the domain), its line and column in the file, how many lines below depend on it, and its fix where it has one -- {"kind": "link", key, calc, instance, …} or {"kind": "options"}."""
    level: str
    code: str
    values: dict = field(default_factory=dict)
    item: object = None
    line: object = None
    col: object = None
    dependents: int = 0
    fix: object = None


@dataclass
class State:
    messages: list = field(default_factory=list)
    rows: dict = field(default_factory=dict)    # item index -> error | blocked | warning

    @property
    def errors(self):
        return [m for m in self.messages if m.level == "error"]

    @property
    def warnings(self):
        return [m for m in self.messages if m.level == "warning"]

    def of_item(self, index):
        return [m for m in self.messages if m.item == index]


def _ratio(sides):
    try:
        (lv, lu), (rv, ru) = sides
        lq, rq = units.quantity(float(lv), lu), units.quantity(float(rv), ru)
        return lq.base / rq.base if lq is not None and rq is not None and rq.base else None
    except (TypeError, ValueError):
        return None


def state(domain, results, lines, here=None, candidates=(), tab_domains=(), listing=None, unfold_states=None):
    """The State of `domain`, computed (`results`), its items beginning on `lines` (formula_rows.item_lines) -- see the module's docstring. `candidates` the variables of the project a link may take ({key, calc, instance, label, symbol, value, unit}); `tab_domains` the domains of the tab, for the warning of a domain read by its name (with `here`, and `listing` formula_order.includes read once); `unfold_states` {item index: its state} of a check unfolded."""
    from domains import formula_errors, formula_order
    out = State()
    if domain.state == "unreadable":
        fault = formula_errors.read_fault(domain.text or "")
        if fault is not None:
            out.messages.append(Message("error", "read_" + fault["code"], {}, None, fault["line"], fault["col"]))
        else:
            out.messages.append(Message("error", "unreadable", {"reason": domain.problem}))
        return out
    dependents = {}
    for r in results:
        if r.blocked_by is not None:
            dependents[r.blocked_by] = dependents.get(r.blocked_by, 0) + 1
    by_key = {}
    for cand in candidates:
        by_key.setdefault(cand["key"], cand)
    for i, (c, r) in enumerate(zip(domain.commands, results)):
        if c.is_text:
            continue
        line = lines[i] if i < len(lines) else None
        if r.error and r.blocked_by is not None:
            out.rows[i] = "blocked"
            continue
        if r.error:
            values = dict(r.values)
            if r.code in ("", "formula"):
                values["text"] = r.error   # a refusal said in English alone (units.CODES' default)
            fix = None
            if r.code == "unknown":
                values["names"] = ", ".join(values.get("names") or ())
                values["declared"] = ", ".join(values.get("declared") or ())
                hit = next((by_key[n] for n in (r.values.get("names") or ()) if n in by_key), None)
                if hit is not None:
                    fix = dict(hit, kind="link")
            elif r.code == "again":
                values["declared"] = ", ".join(values.get("declared") or ())
            out.messages.append(Message("error", r.code or "formula", values, i, line, None, dependents.get(i, 0), fix))
            out.rows[i] = "error"
            continue
        warning = None
        if c.kind == "verify" and r.holds is False:
            (lv, lu), (rv, ru) = r.value
            ratio = _ratio(r.value)
            warning = Message("warning", "fails", {"left": units.shown(lv, lu), "right": units.shown(rv, ru), "op": r.op,
                                                    "ratio": f"{ratio * 100:.1f}" if ratio is not None else "?"}, i, line)
        elif c.kind == "eq" and r.warning:
            code = "as_unit" if r.warning.get("as_unit") else "unit"
            warning = Message("warning", code, {"symbol": c.symbol or c.key, "wanted": r.warning.get("wanted", ""), "natural": r.warning.get("natural", "")}, i, line)
        elif c.kind == "var" and c.source and c.source[0] == "domain" and isinstance(c.source[1], str) and here is not None:
            read = next((d for d in tab_domains if d.id == c.source[1]), None)
            if read is not None and read.id != domain.id:
                missing = formula_order.not_above(here, domain, read, listing)
                if missing:
                    warning = Message("warning", "tabdom", {"key": c.key, "domain": read.name or read.id, "documents": tuple(missing)}, i, line)
        if warning is not None:
            out.messages.append(warning)
            out.rows[i] = "warning"
    if not formula_defaults.is_block(domain):
        out.messages.append(Message("warning", "inline", {}, None, None, None, 0, {"kind": "options"}))
    if domain.state == "misnamed":
        out.messages.append(Message("warning", "misnamed", {"declared": domain.declared, "id": domain.id}))
    for i, st in (unfold_states or {}).items():
        if st in UNFOLD_STATES:
            out.rows[i] = st
    return out


def summary(domain, results, state_=None):
    """What the list on the left says of a domain (UI-002): ("bad", n) for n faults; ("ok"/"fails", percent) after its last check -- its ratio --; ("ok", None) where it holds no check; None for nothing computed."""
    if domain.state == "unreadable":
        return ("bad", 1)
    errors = [r for c, r in zip(domain.commands, results) if not c.is_text and r.error and r.blocked_by is None]
    if errors:
        return ("bad", len(errors))
    for c, r in reversed(list(zip(domain.commands, results))):
        if c.kind == "verify" and not r.error:
            ratio = _ratio(r.value)
            return ("ok" if r.holds else "fails", round(ratio * 100) if ratio is not None else None)
    return ("ok", None)
