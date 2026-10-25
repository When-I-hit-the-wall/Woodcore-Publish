"""The card of a variable or of a domain in the «Variables» tab, and the command to copy (spec docs/requirements/completed/2026-10-24-onglet-variables-groupes.md, REQ-006, UI-010, UI-011, UI-012, ARCH-RISK-010; docs/ui/tab-variables.md).

The card says, at its head, symbol = **value** unit -- the value framed for a result --, its label and where it
is in the window («Actions › Actions variables › Neige · SL [export]»); then the tab to open, the command to
copy with what to include before it, the fields of the variable, «Vient de» in words, and «Le même calcul
ailleurs»: which source computes it and a button for each source that recalls it.

⚠️ **The command is spelled by `build_reference`'s `call_*` and `formula_domain.include_call`, never here**
(ARCH-001, D-18): `#var(key, domain: (calculation, case))` for the export, read live, nothing to include;
`#var(key, domain: "id")` for a file, its `#include domain-file(kind, id)` -- or `#include "/Domains/<id>.typ"`
for a domain of the «Domaines» tab -- above it; `#var(key, domain: "name")` for a document's, the line below
the domain. A variable of no named domain has no command (`build_reference.call_var_registry` refuses it).

No Qt: the tab's card (calc/tools/variables_detail.py) shows what this returns, in the window's words, whose
keys this names.
"""

from dataclasses import dataclass, field
from types import SimpleNamespace

import build_reference as ref   # the one place a Typst call is spelled (docs/typst/reference-workbook.md §10ter)
import variable_calc as calc
import variables as model
from domains import formula_domain


@dataclass
class Command:
    """The line to copy for a variable or a domain, and the sentence of what to include before it: `note` a key of the window's words, `values` what it names."""

    call: str
    note: str
    values: dict = field(default_factory=dict)


def include(domain, assembly, here=None):
    """The line that includes the file of `domain`'s calculation, "" where it has none: `#include domain-file("snow-load", "SL")`, or the «Domaines» tab's `#include "/Domains/poutre-p1.typ"` (formula_domain.include_call)."""
    found = domain.calc
    if found is None:
        return ""
    if found.kind == calc.FORMULA_KIND:
        path = assembly.paths.get(found)
        if not path:
            return ""
        import project
        here = here or project.current()
        return formula_domain.include_call(SimpleNamespace(id=found.ident, path=here.typst_root / path.lstrip("/")), here)
    return ref.call_include_domain(found.kind, found.ident)


def command(key, domain, assembly, here=None, document_name=str):
    """The command of the variable `key` of `domain` and what to include before it (REQ-006), None where there is none -- a variable of no named domain."""
    source = calc.source_of(domain)
    if source == calc.SOURCE_EXPORT:
        if not domain.address:
            return None
        return Command(ref.call_var_domain(domain.address[0], domain.address[1], key), "vr_inc_export")
    if not domain.name:
        return None
    call = ref.call_var_registry(key, domain.name)
    if source == calc.SOURCE_FILE:
        line = include(domain, assembly, here)
        return Command(call, "vr_inc_file", {"include": line}) if line else Command(call, "vr_inc_file_none")
    return Command(call, "vr_inc_document", {"document": document_name(domain.origin)})


def domain_command(domain, assembly, here=None):
    """The whole domain chosen alone (UI-012): its file included where there is one, else None."""
    line = include(domain, assembly, here)
    return Command(line, "vr_inc_whole") if line else None


def copy_lines(keys, domains, assembly, here=None):
    """The lines «Copier les n commandes» puts in the clipboard (UI-010): one `#var` a variable, in the order of `keys` -- which the selection gave (variable_select.Selection.copy_order) --, no line to include, a variable with no command left out. `domains` maps (origin, name) to the domain."""
    out = []
    for origin, name, key in keys:
        domain = domains.get((origin, name))
        if domain is None or key is None or domain.variable(key) is None:
            continue
        found = command(key, domain, assembly, here)
        if found is not None:
            out.append(found.call)
    return out


# --- «Vient de» (UI-011): where the value comes from, in words -------------------------------------

def came_from(var, domain, document_name=str):
    """(key of the window's words, its values): Woodcore, the norm, a document -- in place of the raw `source` (UI-011, T35); a value read in a document's registry is the document's whatever its `source` says (variable_sources.provenance)."""
    if calc.source_of(domain) == calc.SOURCE_DOCUMENT:
        return "vr_from_document", {"document": document_name(domain.origin)}
    kind, rest = model.parse_source(var.source)
    if kind == "norm":
        return "vr_from_norm", {"norm": rest}
    if kind in ("python", "woodcore", "entered"):
        return "vr_from_woodcore", {}
    return "vr_from_unknown", {}


# --- the card ---------------------------------------------------------------------------------------

@dataclass
class Sibling:
    """Another source of the same calculation (UI-011): its domain, the same variable in it (None where it has none), its value as printed, and whether it computes or recalls."""

    domain: object
    key: str
    value: str
    computes: bool


@dataclass
class Card:
    """What the card of one variable shows, in order."""

    var: object
    domain: object
    result: bool
    path: tuple                                   # the menu's titles, then the case
    tab: str                                      # the key of the tab «Ouvrir l'onglet» brings forward: the computing source's
    node: str                                     # the case it opens there, None where none
    command: object                               # Command or None
    fields: list = field(default_factory=list)    # [(key of the caption, text)] -- an empty one left out
    came_from: tuple = ("vr_from_unknown", {})
    computed_in: tuple = None                     # (key, values) of «Calculé dans …», None where the calculation has no other source
    siblings: list = field(default_factory=list)  # [Sibling]


def _choices(var):
    """The choices offered, the one taken marked: [(value, its description, whether it is the one taken)]."""
    return [(choice.get("value"), choice.get("desc", ""), choice.get("value") == var.value) for choice in var.choices if isinstance(choice, dict)]


def variable_card(var, domain, assembly, path=(), here=None, document_name=str):
    """The card of `var` of `domain` (UI-011): its head, the path, the tab of the source that computes it (REQ-009), the command, the fields, «Vient de», the other sources."""
    computing = assembly.computing(domain)
    fields = [
        ("vr_key", var.key),
        ("vr_description", var.description),
        ("vr_citation", var.citation),
        ("vr_formula", domain.formulas.get(var.key, "")),
        ("vr_level", "" if var.level is None else str(var.level)),
    ]
    fields = [(k, v) for k, v in fields if v]
    siblings = []
    for other in assembly.siblings(domain):
        same = other.variable(var.key)
        siblings.append(Sibling(other, same.key if same is not None else None, model.fmt_value(same.value) if same is not None else "", other is computing))
    computed_in = None
    if siblings:
        computed_in = ("vr_computed_here", {}) if computing is domain else ("vr_computed_in", {"source": computing})
    return Card(var=var, domain=domain, result=var.key in domain.results, path=tuple(path) + (calc.case_of(domain),),
                tab=computing.tab, node=assembly.node(computing), command=command(var.key, domain, assembly, here, document_name),
                fields=fields, came_from=came_from(var, domain, document_name), computed_in=computed_in, siblings=siblings)


def choices(var):
    """The choices of a variable, for the card's row «Choix»: [(text, the one taken)] -- empty where it offers none."""
    return [(f"{value}" + (f" — {desc}" if desc else ""), taken) for value, desc, taken in _choices(var)]


@dataclass
class DomainCard:
    """What the card of a domain chosen alone shows (UI-012): no «Valeur», no «Désignation»."""

    domain: object
    path: tuple
    tab: str
    node: str
    command: object
    variables: int
    results: int
    siblings: list = field(default_factory=list)  # [Sibling], their key None


def domain_card(domain, assembly, path=(), here=None):
    computing = assembly.computing(domain)
    return DomainCard(domain=domain, path=tuple(path) + (calc.case_of(domain),), tab=computing.tab, node=assembly.node(computing),
                      command=domain_command(domain, assembly, here), variables=len(domain.variables),
                      results=sum(1 for var in domain.variables if var.key in domain.results),
                      siblings=[Sibling(other, None, "", other is computing) for other in assembly.siblings(domain)])
