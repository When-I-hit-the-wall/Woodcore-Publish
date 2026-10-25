"""Which calculation each domain of the «Variables» tab is, and what follows from it (spec docs/requirements/completed/2026-10-24-onglet-variables-groupes.md, REQ-001 to REQ-004, ARCH-008, ARCH-011, ARCH-012; docs/ui/tab-variables.md).

The tab lists **one line per source** (D-2): the export (`data/`), the file Woodcore wrote (the domains of
`formulas.json`) and each compiled document's registry. The same calculation -- the snow load `SL` -- is then a
domain three times, and the engineer's rule is that «un calcul n'est porté normalement que par une seule
source, et toutes les autres ne font que la rappeler». This module says, for every domain, which calculation it
carries (`CalcRef`, a pair (kind, id) the same for its three sources), which tab of Woodcore computes it
(`Domain.tab`), which source computes it and which recall it, whether a document prints it, which of its
variables are results, and its node in the graph of dependencies.

⚠️ **Nothing is guessed from a name or a folder.** A domain of the export names its calculation by its address;
a file by the path `domain-files.json` gives for it (Q-001, A); a document's domain by its name looked up in
that table -- an identifier of a file Woodcore wrote, never a resemblance of names (REQ-002) --, a name found in
two kinds or in none staying without a calculation. A check's tab is read off its record (`kind`, `fire`) and
not off the folder of its file: FE-01, a check in the fire situation, is written under `Timber-checks/Bending/`
(D-12, ARCH-RISK-001).

⚠️ **The tables below are the only keys of tabs written outside `tab_registry`** (ARCH-005): they cannot be
read off the tabs without importing them, hence Qt. `tests/test_variable_calc.py` holds every key to a
`TabSpec`, and each domain's tab to the tab whose `lists_object` answers for its node. Issue #112, which folds
«Flambage» and «Déversement» into «Compression» and «Flexion», changes the two lines it names (ARCH-011).

No Qt: the tab shows what this returns.
"""

from dataclasses import dataclass, field

import variable_sources as sources
from domains import dependency_graph, formula_domain, links, member_check, steel_check

EXPORT = sources.EXPORT
FILES = formula_domain.ORIGIN   # the origin of a domain of formulas.json: the file Woodcore wrote

# The three sources, in the order that says which one computes (D-2, REQ-003): the export where it has the value, else the file, else the document.
SOURCE_EXPORT, SOURCE_FILE, SOURCE_DOCUMENT = "export", "file", "document"
SOURCES = (SOURCE_EXPORT, SOURCE_FILE, SOURCE_DOCUMENT)

# A domain of the «Domaines» tab: in formulas.json, absent from domain-files.json (REQ-001).
FORMULA_KIND = "formula"

# The kinds of domain-files.json that are no calculation: the revision journal of each document.
NOT_CALCULATIONS = ("journal",)

# The kind of a calculation -> the key of the tab that computes it (REQ-001).
CALC_TABS = {
    "dead-load": "tab_ac_selfweight",
    "live-load": "tab_ac_imposed",
    "snow-load": "tab_ac_snow",
    "wind-load": "tab_ac_wind",
    "connector": "tab_connections",
    "connection": "tab_polar",
    "script": "tab_python",
    FORMULA_KIND: "tab_formula",
}

# The kind of a check's record (checks.json, steel.json) -> the key of its tab; a timber check in the fire situation (`fire`) is FIRE_TAB's whatever its kind (D-12). Issue #112 changes the lines of `buckling` and `lateral-torsional` (ARCH-011).
CHECK_TABS = {
    "check": {
        "tension": "tab_mc_tension",
        "compression": "tab_mc_compression",
        "bending": "tab_mc_bending",
        "shear": "tab_mc_shear",
        "buckling": "tab_mc_compression",          # the stability is the last accordion of the compression and of the bending (issue #112, REQ-011)
        "lateral-torsional": "tab_mc_bending",
    },
    "steel": {
        "tension": "tab_st_tension",
        "compression": "tab_st_compression",
        "bending": "tab_st_bending",
        "shear": "tab_st_shear",
    },
}
FIRE_TAB = "tab_mc_fire"

# The index of the export each kind of check is recorded in (variable_sources.INDEX_FILES).
CHECK_INDEX = {"check": "checks", "steel": "steel"}

# The result of a check, declared by the modules that write it (ARCH-012).
CHECK_RESULTS = {"check": (member_check.RESULT_KEY,), "steel": (steel_check.RESULT_KEY,)}


@dataclass(frozen=True)
class CalcRef:
    """A calculation, the same for its three sources: its kind as domain-files.json says it (`snow-load`, `check`, `connector`, … or FORMULA_KIND) and its id (`SL`, `BI-01`)."""

    kind: str
    ident: str


def source_of(domain):
    """SOURCE_EXPORT, SOURCE_FILE or SOURCE_DOCUMENT: where `domain` was read."""
    if domain.origin == EXPORT:
        return SOURCE_EXPORT
    if domain.origin == FILES:
        return SOURCE_FILE
    return SOURCE_DOCUMENT


def case_of(domain):
    """The case a domain is of, as the tab names it: `SL` for the export's `snow-load · SL`, the file's `SL` and the report's `SL`."""
    if domain.origin == EXPORT and domain.address:
        return str(domain.address[1])
    return domain.name


def _path(path):
    """A file of domain-files.json or formulas.json, from the Typst root, written one way: `Variable-loads/Snow/SL.typ`."""
    return str(path or "").replace("\\", "/").lstrip("/")


def tab_of(ref, index):
    """The key of the tab that computes `ref`, None where none does or the calculation is not found: a check's tab read off its record (`kind`, `fire`), every other calculation's off its kind."""
    if ref is None:
        return None
    if ref.kind in CHECK_TABS:
        record = (index.get(CHECK_INDEX[ref.kind]) or {}).get(ref.ident)
        if not isinstance(record, dict):
            return None
        if ref.kind == "check" and record.get("fire") is not None:
            return FIRE_TAB
        return CHECK_TABS[ref.kind].get(record.get("kind"))
    return CALC_TABS.get(ref.kind)


@dataclass
class Assembly:
    """What the tab lists, assembled: every domain with its `tab` and `calc` set, and what joins them -- the families of one calculation, the names of documents that two kinds claim, whether any document was read."""

    domains: list = field(default_factory=list)
    families: dict = field(default_factory=dict)      # CalcRef -> [Domain], the export's first, then the file's, then the documents'
    ambiguous: dict = field(default_factory=dict)     # a document's domain name -> the kinds of domain-files.json that hold it (REQ-002: left without a calculation)
    documents_read: bool = False                      # a document's registry was given: whether a domain is printed can be said
    paths: dict = field(default_factory=dict)         # CalcRef -> its file from the Typst root (`/Variable-loads/Snow/SL.typ`)
    load_kinds: frozenset = frozenset()               # the calculations of calculations.json, which name a case `load:<kind>/<id>` in the graph

    def family(self, domain):
        """Every domain of `domain`'s calculation, itself included, in the order of SOURCES; itself alone where it has none."""
        return self.families.get(domain.calc, [domain]) if domain.calc is not None else [domain]

    def siblings(self, domain):
        """The other sources of the same calculation (REQ-003): «Le même calcul ailleurs»."""
        return [other for other in self.family(domain) if other is not domain]

    def computing(self, domain):
        """The source that computes `domain`'s calculation -- the export where it has it, else the file, else the document --, the others recalling it (D-2)."""
        return self.family(domain)[0]

    def printed(self, domain):
        """True where a compiled document holds a domain of its calculation, False where none does, None while no document is read -- an impression unknown is never said absent (REQ-003)."""
        if source_of(domain) == SOURCE_DOCUMENT:
            return True
        if any(source_of(other) == SOURCE_DOCUMENT for other in self.family(domain)):
            return True
        return False if self.documents_read else None

    def node(self, domain):
        """The node of the graph of dependencies `domain`'s calculation is (dependency_graph.target, no second table of nodes), None where it has no calculation or the graph names none."""
        ref = domain.calc
        if ref is None:
            return None
        if ref.kind == FORMULA_KIND:
            return dependency_graph.target(None, ref.ident, (), origin=links.FORMULAS)
        return dependency_graph.target(ref.kind, ref.ident, self.load_kinds)

    def path(self, domain):
        """The file of `domain`'s calculation from the Typst root, "" where there is none."""
        return self.paths.get(domain.calc, "") if domain.calc is not None else ""


def assemble(domains, index, documents_read=False):
    """`domains` -- the export's, then the documents' (variable_sources.read_export, registry_domains) -- each given its `tab`, its `calc` and the results of its calculation, and joined into families. `index` is `Export.index`. Read again at every assembly, in one pass: nothing is cached (ARCH-RISK-014)."""
    domains = list(domains)
    files = index.get("domain-files") or {}
    formulas = index.get(sources.FORMULAS_INDEX) or {}
    found = Assembly(domains=domains, documents_read=bool(documents_read))
    by_path, kinds_of = {}, {}
    for kind, ids in files.items():
        if kind in NOT_CALCULATIONS or not isinstance(ids, dict):
            continue
        for ident, path in ids.items():
            ref = CalcRef(kind, ident)
            by_path[_path(path)] = ref
            found.paths[ref] = "/" + _path(path)
            kinds_of.setdefault(ident, []).append(kind)
    for ident, record in formulas.items():
        file = _path((record or {}).get("file"))
        if file and file not in by_path:
            found.paths.setdefault(CalcRef(FORMULA_KIND, ident), "/" + file)
    found.load_kinds = frozenset(d.address[0] for d in domains if d.origin == EXPORT and d.address and d.file == sources.CALCULATIONS_FILE)

    for domain in domains:
        domain.calc = _calculation(domain, by_path, kinds_of, formulas, found.ambiguous)
        domain.tab = tab_of(domain.calc, index)
    families = {}
    for domain in domains:
        if domain.calc is not None:
            families.setdefault(domain.calc, []).append(domain)
    for ref, members in families.items():
        members.sort(key=lambda d: SOURCES.index(source_of(d)))
        export = next((d for d in members if source_of(d) == SOURCE_EXPORT and d.results), None)
        declared = tuple(export.results) if export is not None else CHECK_RESULTS.get(ref.kind, ())
        for member in members:
            member.results = tuple(dict.fromkeys(tuple(member.results) + declared))
    found.families = families
    return found


def _calculation(domain, by_path, kinds_of, formulas, ambiguous):
    """The CalcRef `domain` carries (REQ-001, REQ-002), None where it is not found."""
    source = source_of(domain)
    if source == SOURCE_EXPORT:
        return CalcRef(*domain.address) if domain.address else None
    if source == SOURCE_FILE:
        record = formulas.get(domain.name)
        if not isinstance(record, dict):
            return None
        return by_path.get(_path(record.get("file"))) or CalcRef(FORMULA_KIND, domain.name)
    kinds = kinds_of.get(domain.name, [])
    if len(kinds) == 1:
        return CalcRef(kinds[0], domain.name)
    if len(kinds) > 1:
        ambiguous[domain.name] = tuple(kinds)
        return None
    record = formulas.get(domain.name)
    if isinstance(record, dict) and _path(record.get("file")) not in by_path:
        return CalcRef(FORMULA_KIND, domain.name)
    return None   # a domain the document declares itself (`S10 - 1 kN Mitte`)
