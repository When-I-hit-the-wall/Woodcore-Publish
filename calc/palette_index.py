"""What the command palette searches (Ctrl+K, issue #83; docs/ui/command-palette.md), read where each thing is kept, and how a query is matched -- Qt-free, the window's calc/tools/command_palette.py showing it.

The engineer, 07.10.2026: «il y a pour l'instant trop d'informations dans les onglets. On se perd un peu». The palette finds a tab, an action, an object of the project, a variable, a norm, a Typst command or a warning in a few letters.

**Nothing is copied** (the project's first rule). Each kind of entry is read at its source every time the palette opens, and kept nowhere between two openings:

- the **tabs** and the **actions** are the window's own -- the registry's tabs of the document shown, the actions of its menus and of the PDF button, the views of the tab in front, the languages -- handed in by the window as `Entry`s, this module importing nothing of calc/tools/;
- the **objects**: the positions as positions_store reads them, and every node of the graph of dependencies of the last export (data/dependencies.json, dependency_graph.read), what uses each read off its edges (`used_by`, dependency_graph.reachable);
- the **η of a check**: a timber check's computed by member_check.compute, as its tab computes it (`member_check.utilisations`); a steel check's read off data/steel.json, which holds it;
- the **variables**: the export's, variable_sources.read_export -- no Typst compiled;
- the **norms**: calc/norms/norms.json's documents (norms.references) and the clauses the export's checks cite;
- the **Typst commands**: calc/i18n/commands.json, which holds every public command (tests/test_commands.py);
- the **warnings**: what the window's notices hold (notifications.STORE), each check's own warnings and the reason a check cannot be calculated, and the files of the export that are missing or cannot be read. Nothing new gathers them.

A file that cannot be read is said by an entry of its own, never swallowed.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path

import notifications
import positions_store
import project
import variable_sources
from domains import dependency_graph
from domains import member_check
from norms import norms

# The categories under the search field, each with the character that chooses it when typed first («>» actions, «@» objects…): the one table of both, the window reading it.
CATEGORIES = (("all", ""), ("actions", ">"), ("objects", "@"), ("variables", "#"), ("norms", "§"), ("warnings", "!"))
PREFIXES = {prefix: key for key, prefix in CATEGORIES if prefix}
# Which category each kind of entry belongs to, besides «all»; and the order the kinds are grouped in on the list
CATEGORY_OF = {"tab": "all", "action": "actions", "view": "actions", "language": "actions", "position": "objects", "object": "objects", "check": "objects",
               "variable": "variables", "norm": "norms", "command": "all", "warning": "warnings"}
GENRES = ("tab", "action", "view", "language", "position", "check", "object", "norm", "variable", "command", "warning")
COMMANDS_FILE = project.APP_ROOT / "calc" / "i18n" / "commands.json"
# A check whose η is above 1 by more than this is not satisfied: the tolerance member_check and steel_check decide a verdict with
ETA_TOLERANCE = 1e-9


@dataclass
class Entry:
    """One thing the palette offers. `kind` one of GENRES; `key` unique among the entries (`tab:tab_mc_bending`, `check:BI-01`); `label` what the list shows and the query is matched against, with `ident` beside it; `detail` the panel's line under it; `node` the graph's node it opens (`check:BI-01`), where it is one; `eta` and `ok` a check's utilisation; `data` what the window needs to act on it (an action's own object, a tab's index, a notice)."""

    kind: str
    key: str
    label: str
    ident: str = ""
    detail: str = ""
    node: str = ""
    eta: float = None
    ok: bool = None
    data: object = None
    extra: dict = field(default_factory=dict)

    @property
    def category(self):
        return CATEGORY_OF.get(self.kind, "all")


def parse(query):
    """(category, the letters searched) of what is typed: a first character of PREFIXES chooses its category -- «@T001» is the object T001 --, else «all»."""
    text = query or ""
    if text[:1] in PREFIXES:
        return PREFIXES[text[0]], text[1:].strip()
    return "all", text.strip()


def match(needle, haystack):
    """Where the letters of `needle` stand in `haystack`, in their order and case left aside -- the positions found, to underline them --, or None where they are not all there. Not a word search: «flex» finds «Flexion», «bi01» finds «BI-01»."""
    needle = "".join((needle or "").lower().split())
    if not needle:
        return []
    found, start, low = [], 0, haystack.lower()
    for letter in needle:
        at = low.find(letter, start)
        if at < 0:
            return None
        found.append(at)
        start = at + 1
    return found


def _score(positions, text):
    """A smaller score for a better match: the letters together, and early, and at the start of a word."""
    if not positions:
        return 0
    gaps = sum(b - a - 1 for a, b in zip(positions, positions[1:]))
    starts = sum(1 for p in positions if p == 0 or not text[p - 1].isalnum())
    return gaps * 3 + positions[0] - starts * 2


def search(entries, query):
    """The entries `query` finds, each with the positions of its letters in its text (`label` then `ident` -- an id typed finds its object), best first within each kind, the kinds in GENRES' order. An empty query finds every entry of the category."""
    category, text = parse(query)
    out = []
    for entry in entries:
        if category != "all" and entry.category != category:
            continue
        shown = f"{entry.label}  {entry.ident}".strip() if entry.ident and entry.ident not in entry.label else entry.label
        positions = match(text, shown)
        if positions is None:
            continue
        out.append((entry, positions, _score(positions, shown)))
    order = {kind: i for i, kind in enumerate(GENRES)}
    out.sort(key=lambda item: (order.get(item[0].kind, len(GENRES)), item[2], item[0].label.lower()))
    return [(entry, positions) for entry, positions, _score_ in out]


# --- reading the sources -----------------------------------------------------------------------------------------

def _json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def utilisations(here, records=None):
    """{check id: (η, ok, [clauses cited])} of every check of the last export that can be calculated: a timber check's computed by member_check.utilisations, a steel check's as data/steel.json holds it, with the clauses its steps cite. A file missing gives none; one that cannot be read raises, for the caller to say."""
    out = {}
    checks = here.data_dir / member_check.EXPORT_FILE
    if checks.is_file():
        for ident, found in member_check.utilisations(_json(checks)).items():
            out[ident] = (found["eta"], found["ok"], [found["clause"]] if found["clause"] else [])
    steel = here.data_dir / "steel.json"
    if steel.is_file():
        for ident, record in (_json(steel).get("checks") or {}).items():
            if isinstance(record.get("eta"), (int, float)):
                cited = [" ".join(str(step.get(k) or "") for k in ("norm", "norm_ref")).strip() for step in record.get("steps") or [] if isinstance(step, dict) and step.get("norm_ref")]
                out[ident] = (float(record["eta"]), bool(record.get("ok", record["eta"] <= 1 + ETA_TOLERANCE)), list(dict.fromkeys(cited)))
    return out


def graph(here):
    """The graph of dependencies of the last export, or None where there is none (dependency_graph.read)."""
    return dependency_graph.read(here.data_dir / dependency_graph.EXPORT_FILE)


def used_by(graph_data, node):
    """Every node that depends on `node`, transitively, in the graph's order of kinds (dependency_graph.reachable): what the panel says uses a position."""
    if graph_data is None:
        return []
    return dependency_graph.reachable(dependency_graph.downstream(graph_data), node)


def summary(graph_data, node, etas):
    """What the panel says of `node` beyond itself: {"count": {kind: n}, "eta_max": the largest η of the checks that use it, or None}."""
    found = used_by(graph_data, node)
    count = {}
    for other in found:
        kind = dependency_graph.kind_of(other)
        count[kind] = count.get(kind, 0) + 1
    values = [etas[other.split(":", 1)[1]][0] for other in found if dependency_graph.kind_of(other) in ("check", "steel") and other.split(":", 1)[1] in etas]
    return {"count": count, "eta_max": max(values) if values else None, "used_by": found}


def typst_call(node):
    """The Typst call that prints `node` in a section -- `#position("T001")`, `#image-schema("S1")`, `#include domain-file("check", "BI-01")` -- read off the table of the commands that name an object (dependency_graph.COMMAND_REFERENCES), "" where none does."""
    kind, ident = node.split(":", 1)
    naming = [command for command, spec in dependency_graph.COMMAND_REFERENCES.items() if spec[0] == "id" and spec[1] == kind and spec[2] == 0]
    # the command that prints the object itself first -- `#position`, an `#image-…` -- before one that only names it (`#plans-of`)
    naming = [command for _n, command in sorted(enumerate(naming), key=lambda item: (item[1] != kind and not item[1].startswith("image-"), item[0]))]
    if naming:
        return f'#{naming[0]}("{ident}")'
    for word, node_kind in dependency_graph.FILE_KINDS.items():
        if node_kind == kind:
            return f'#include domain-file("{word}", "{ident}")'
    return ""


def _positions(here, notes):
    try:
        rows = positions_store.read(here)
    except Exception as exc:  # broad: a file that cannot be read is said by an entry of its own, never swallowed
        notes.append(("positions", str(exc)))
        return []
    out = []
    for row in rows:
        ident = str(row.get("position") or "")
        if ident:
            words = " · ".join(str(row.get(key) or "") for key in ("description", "type", "material", "strength_class", "dimension") if row.get(key))
            out.append(Entry("position", f"position:{ident}", ident, detail=words, node=f"position:{ident}"))
    return out


def _objects(here, graph_data, etas, records):
    """Every check of the export with its η -- from its own file, a graph or not -- then every other node of the graph but the positions (listed from their own file), the sections and the documents."""
    out = []
    for ident, record in records.items():
        kind = "steel" if record.get("profile") is not None else "check"
        eta, ok = etas.get(ident, (None, None, []))[:2]
        label = str(record.get("name") or record.get("label") or ident)
        out.append(Entry("check", f"{kind}:{ident}", label, ident=ident, detail=kind, node=f"{kind}:{ident}", eta=eta, ok=ok,
                         extra={"kind": kind, "position": record.get("position") or ""}))
    if graph_data is None:
        return out
    for node in graph_data["nodes"]:
        kind, ident = node.split(":", 1)
        if kind in ("position", "section", "document", "check", "steel"):
            continue
        out.append(Entry("object", node, ident, ident="", detail=kind, node=node, extra={"kind": kind}))
    return out


def _check_records(here, notes):
    records = {}
    for name in (member_check.EXPORT_FILE, "steel.json"):
        path = here.data_dir / name
        if not path.is_file():
            continue
        try:
            records.update(_json(path).get("checks") or {})
        except (OSError, ValueError) as exc:
            notes.append((name, str(exc)))
    return records


def _variables(here, notes):
    found = variable_sources.read_export(here)
    for error in found.errors:
        notes.append((error.detail.get("file", "variables"), str(error)))
    out = []
    for domain in found.domains:
        where = " · ".join(str(part) for part in (domain.address or (domain.name,)))
        for var in domain.variables:
            shown = f"{var.value:.4g}" if isinstance(var.value, float) else str(var.value) if var.value is not None else ""
            value = f"{shown} {var.unit}".strip() if shown else ""
            out.append(Entry("variable", f"variable:{where}/{var.key}", var.key, ident=var.symbol if var.symbol != var.key else "", detail=f"{where} — {value}" if value else where,
                             extra={"address": domain.address, "domain": domain.name, "key": var.key}))
    return out, found.missing


def _norms(lang, etas):
    out = []
    for ref in norms.references():
        title = norms.text(ref, "title", lang) if isinstance(ref.get("title"), dict) else str(ref.get("title") or "")
        designation = norms.text(ref, "designation", lang) if isinstance(ref.get("designation"), dict) else str(ref.get("designation") or ref["key"])
        out.append(Entry("norm", f"norm:{ref['key']}", designation, detail=f"{title} ({ref.get('edition', '')})".strip(), extra={"key": ref["key"]}))
    cited = {}
    for ident, (_eta, _ok, clauses) in etas.items():
        for clause in clauses:
            cited.setdefault(clause, []).append(ident)
    for clause, checks in sorted(cited.items()):
        out.append(Entry("norm", f"clause:{clause}", clause, detail=", ".join(sorted(set(checks))), extra={"checks": sorted(set(checks))}))
    return out


def _commands(lang):
    try:
        commands = _json(COMMANDS_FILE).get("commands") or {}
    except (OSError, ValueError):
        return []
    out = []
    for name in sorted(commands):
        paragraphs = commands[name].get("paragraphs") or []
        first = paragraphs[0] if paragraphs else {}
        text = (first.get(lang) or first.get("en") or "").split(". ")[0] if isinstance(first, dict) else ""
        out.append(Entry("command", f"command:{name}", f"#{name}", detail=text, extra={"name": name}))
    return out


def _warnings(here, lang, records, etas, missing, notes):
    out = []
    for notice in notifications.STORE.items():
        if notice.severity in (notifications.CRITICAL, notifications.WARNING):   # an information is no warning
            out.append(Entry("warning", f"notice:{notice.id}", notifications.title(notice, lang), detail=notifications.message(notice, lang),
                             data=notice, extra={"file": notice.file, "line": notice.line, "source": "notice"}))
    for ident, (eta, ok, _clauses) in sorted(etas.items()):
        if not ok:
            kind = "steel" if records.get(ident, {}).get("profile") is not None else "check"
            out.append(Entry("warning", f"eta:{ident}", ident, detail=f"η = {eta:.2f}", node=f"{kind}:{ident}", eta=eta, ok=False, extra={"source": "eta"}))
    for ident, record in sorted(records.items()):
        kind = "steel" if record.get("profile") is not None else "check"
        if record.get("calculable") is False and record.get("reason"):
            out.append(Entry("warning", f"reason:{ident}", ident, detail=str(record["reason"]), node=f"{kind}:{ident}", extra={"source": "reason"}))
        for n, text in enumerate(record.get("warnings") or []):
            out.append(Entry("warning", f"check-warning:{ident}:{n}", ident, detail=str(text), node=f"{kind}:{ident}", extra={"source": "check"}))
    for name in missing:
        out.append(Entry("warning", f"missing:{name}", name, detail="", extra={"source": "missing", "file": name}))
    for name, text in notes:
        out.append(Entry("warning", f"unreadable:{name}", name, detail=text, extra={"source": "unreadable", "file": name}))
    return out


def build(here, lang="fr", window_entries=()):
    """Every entry the palette offers for project `here`, read now: `window_entries` (the tabs, the actions, the views and the languages the window hands in, already `Entry`s) first, then the objects, the checks with their η, the norms, the variables, the Typst commands and the warnings. Returns (entries, graph): the graph of dependencies is what the panel reads «utilisé par» from, None where the export has none yet."""
    notes = []
    records = _check_records(here, notes)
    try:
        etas = utilisations(here)
    except (OSError, ValueError) as exc:
        notes.append(("checks", str(exc)))
        etas = {}
    graph_data = graph(here)
    entries = list(window_entries)
    entries += _positions(here, notes)
    entries += _objects(here, graph_data, etas, records)
    entries += _norms(lang, etas)
    variables, missing = _variables(here, notes)
    entries += variables
    entries += _commands(lang)
    entries += _warnings(here, lang, records, etas, missing, notes)
    return entries, graph_data
