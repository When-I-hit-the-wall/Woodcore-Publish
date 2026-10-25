"""The menu of the tabs, the filter and the list grouped by domain of the «Variables» tab (spec docs/requirements/completed/2026-10-24-onglet-variables-groupes.md, UI-002, UI-003, UI-005, UI-006, ARCH-001, ARCH-005; docs/ui/tab-variables.md).

The engineer's prototype (version 2, 24.10.2026): on the left a button opening a menu of Woodcore's tabs, «Tous
les onglets» by default, each entry with its number of variables in the source chosen; under it the source
(«Toutes · Export · Fichiers · Rapport») and the domains of the filter under the title of their tab; in the
centre a search bar carrying the filter as tags, and the list **always grouped by domain**, a title line per
domain, its variables under it.

⚠️ **The navigation is given, never written here** (ARCH-005, D-13): `navigation()` receives the groups, the
sections and the titles the window reads from `tab_registry` -- which imports every tab, hence Qt, and cannot be
imported by a model tested without it. The rule of the sections (a `NAV_SECTIONS[key]` opens a section until
the next key that has one, `""` drawing a line only) is the window's own (woodcore_gui.nav_widget) written a
second time: `tests/test_variable_query.py` holds the two equal. The one key of a group written here is that of
the group the documents' own domains are listed in (`DOCUMENT_GROUP`), held to `NAV_GROUPS` by the same test.

No Qt: the tab shows what this returns and decides nothing of it.
"""

from dataclasses import dataclass, field

import variable_calc as calc
import variables as model

# The group of the navigation under which a document's own domains are listed, one entry per document made (UI-002, D-14).
DOCUMENT_GROUP = "nav_document_group"

# The menu's keys that are no tab: a document's own domains (`doc:<mode>`), a domain whose calculation is not found.
DOCUMENT_PREFIX = "doc:"
NO_TAB = "none"
ALL = ""   # the menu's first entry, «Tous les onglets»

# The source chosen in the segment (UI-003): every source, or one.
ALL_SOURCES = "all"
SOURCE_FILTERS = (ALL_SOURCES, calc.SOURCE_EXPORT, calc.SOURCE_FILE, calc.SOURCE_DOCUMENT)

ANY_UNIT = None   # the unit filter's first entry: every unit


@dataclass
class Node:
    """One entry of the menu: a group, a section, a tab, a document or «Sans onglet». `tabs` are the menu keys under it -- itself for a tab --, which is what choosing it takes (UI-002: «choisir un groupe ou une section prend tous ses onglets»)."""

    id: str
    title: str
    kind: str                                   # "group", "section", "tab", "document", "none"
    depth: int = 0
    path: tuple = ()                            # the titles from its group down to it
    tabs: tuple = ()
    children: list = field(default_factory=list)


def navigation(groups, sections, title, documents=(), none_title=None, document_group=DOCUMENT_GROUP):
    """The menu's tree from the window's navigation: `groups` its groups in order, `(group key, (tab keys…))` (tab_registry.NAV_GROUPS); `sections` the sub-titles (NAV_SECTIONS: key -> title key, "" a line only); `title(key)` a key's words. `documents` [(mode, name)] the documents made, an entry each in the document group; `none_title` the words of «Sans onglet», an entry at the end where given. Returns the roots."""
    roots = []
    for group_key, keys in groups:
        group = Node(id="g:" + group_key, title=title(group_key), kind="group", depth=0, path=(title(group_key),))
        section = None
        for key in keys:
            if key in sections:
                section = None
                if sections[key]:
                    words = title(sections[key])
                    section = Node(id=f"s:{group_key}:{key}", title=words, kind="section", depth=1, path=group.path + (words,))
                    group.children.append(section)
            parent = section or group
            parent.children.append(Node(id=key, title=title(key), kind="tab", depth=parent.depth + 1, path=parent.path + (title(key),), tabs=(key,)))
        if group_key == document_group:
            for mode, name in documents:
                group.children.append(Node(id=DOCUMENT_PREFIX + mode, title=name, kind="document", depth=1, path=group.path + (name,), tabs=(DOCUMENT_PREFIX + mode,)))
        roots.append(group)
    if none_title is not None:
        roots.append(Node(id=NO_TAB, title=none_title, kind="none", depth=0, path=(none_title,), tabs=(NO_TAB,)))
    for root in roots:
        _gather(root)
    return roots


def _gather(node):
    if node.children:
        node.tabs = tuple(key for child in node.children for key in _gather(child))
    return node.tabs


def walk(roots):
    """Every node, depth first, in the menu's order."""
    out = []
    for node in roots:
        out.append(node)
        out.extend(walk(node.children))
    return out


def sections_of(roots):
    """[(group id, [(tab key, the title of its section or None)])]: the rule of the sections as the menu applied it -- what the test compares with the window's own navigation."""
    out = []
    for group in roots:
        if group.kind != "group":
            continue
        rows = []
        for child in group.children:
            if child.kind == "section":
                rows += [(tab.id, child.title) for tab in child.children]
            elif child.kind == "tab":
                rows.append((child.id, None))
        out.append((group.id, rows))
    return out


def menu_key(domain):
    """Where `domain` is listed in the menu: the tab that computes it, else, for a domain a document declares itself, that document's entry, else «Sans onglet» (REQ-001: never left out)."""
    if domain.tab:
        return domain.tab
    if calc.source_of(domain) == calc.SOURCE_DOCUMENT and domain.calc is None:
        return DOCUMENT_PREFIX + domain.origin
    return NO_TAB


@dataclass
class Filter:
    """What the engineer has chosen: the menu's entry, the source, a domain, the words typed, a unit, «Résultats seulement»."""

    menu: str = ALL
    source: str = ALL_SOURCES
    domain: tuple = None                        # (origin, name)
    text: str = ""
    unit: object = ANY_UNIT
    results_only: bool = False


def accepted(accept, var, domain):
    return accept is None or accept(var, domain)


class Catalogue:
    """Every domain the tab lists, assembled (variable_calc.Assembly), with the menu it is listed by: what the panes ask -- the numbers of the menu, the domains of the filter under their tab, the list grouped by domain, the units, the count, the tags. `accept(var, domain)` is the field's while one is being linked (REQ-008), None otherwise."""

    def __init__(self, assembly, roots):
        self.assembly = assembly
        self.domains = list(assembly.domains)
        self.roots = roots
        self.nodes = {node.id: node for node in walk(roots)}
        self.order = {key: i for i, key in enumerate(key for node in walk(roots) if node.kind in ("tab", "document", "none") for key in node.tabs)}
        self.position = {id(domain): i for i, domain in enumerate(self.domains)}
        self.by_key = {(domain.origin, domain.name): domain for domain in self.domains}

    # -- what a domain is in the menu --

    def tab_title(self, domain):
        node = self.nodes.get(menu_key(domain))
        return node.title if node is not None else ""

    def menu_path(self, domain):
        node = self.nodes.get(menu_key(domain))
        return node.path if node is not None else ()

    def ordered(self, domains=None):
        """The domains in the order of the navigation, then in the order they were read (the export's, the files', the documents')."""
        return sorted(self.domains if domains is None else domains,
                      key=lambda d: (self.order.get(menu_key(d), len(self.order)), self.position.get(id(d), 0)))

    # -- the filter --

    def in_menu(self, domain, menu):
        if not menu:
            return True
        node = self.nodes.get(menu)
        return node is not None and menu_key(domain) in node.tabs

    @staticmethod
    def in_source(domain, source):
        return source in (None, ALL_SOURCES) or calc.source_of(domain) == source

    def in_scope(self, domain, f):
        return self.in_menu(domain, f.menu) and self.in_source(domain, f.source)

    def haystack(self, var, domain):
        return " ".join((var.key, var.symbol, var.label, var.description, var.unit, var.norm, var.norm_ref,
                         model.fmt_value(var.value), calc.case_of(domain), self.tab_title(domain), domain.label)).lower()

    def matches(self, var, domain, f, accept=None):
        """Whether `var` passes the filter's words, unit and «Résultats seulement» -- every word typed found, in any order («kn neige», UI-005) -- and is one the field being linked takes."""
        if not accepted(accept, var, domain):
            return False
        if f.results_only and var.key not in domain.results:
            return False
        if f.unit is not ANY_UNIT and var.unit != f.unit:
            return False
        words = f.text.lower().split()
        if not words:
            return True
        haystack = self.haystack(var, domain)
        return all(word in haystack for word in words)

    # -- the menu's numbers (UI-002) --

    def count(self, node_id, source, accept=None):
        """The variables under the menu's entry `node_id` (ALL: every one) in `source`, those the field takes where one is linked."""
        return sum(sum(1 for var in domain.variables if accepted(accept, var, domain))
                   for domain in self.domains if self.in_menu(domain, node_id) and self.in_source(domain, source))

    def menu_rows(self, source, accept=None):
        """[(node, count)] of every entry, in the menu's order: what the tree menu shows, an entry at zero greyed (UI-002)."""
        return [(node, self.count(node.id, source, accept)) for node in walk(self.roots)]

    # -- the domains of the filter on the left (UI-003) --

    def side(self, f, accept=None):
        """[(the tab's title, [(domain, count)])]: the domains of the menu's entry and the source, under the title of their tab in the order of the navigation, each with its number of variables -- while a field is linked, the ones it takes only, a domain with none left out."""
        out = []
        for domain in self.ordered():
            if not self.in_scope(domain, f):
                continue
            n = sum(1 for var in domain.variables if accepted(accept, var, domain))
            if accept is not None and n == 0:
                continue
            title = self.tab_title(domain)
            if not out or out[-1][0] != title:
                out.append((title, []))
            out[-1][1].append((domain, n))
        return out

    # -- the list (UI-006) --

    def groups(self, f, accept=None):
        """[(domain, [variables])]: the list, always grouped by domain -- the domains of the scope (and the one chosen, where one is) in the order of the navigation, each with the variables the filter keeps in the order it declares them; a domain left with none has no line."""
        out = []
        for domain in self.ordered():
            if not self.in_scope(domain, f):
                continue
            if f.domain is not None and (domain.origin, domain.name) != tuple(f.domain):
                continue
            kept = [var for var in domain.variables if self.matches(var, domain, f, accept)]
            if kept:
                out.append((domain, kept))
        return out

    @staticmethod
    def shown_keys(groups):
        """The keys (origin, domain, name) of the list, in its order: the order of a range, of a copy and of `selected_keys()`."""
        return [(domain.origin, domain.name, var.key) for domain, kept in groups for var in kept]

    def all_keys(self, accept=None):
        """Every variable's key, in the order of the whole list with no filter: where a choice hidden by a filter is copied from (UI-009)."""
        return [(d.origin, d.name, v.key) for d in self.ordered() for v in d.variables if accepted(accept, v, d)]

    @staticmethod
    def totals(groups):
        """(variables, domains) of the list: «49 variable(s) dans 26 domaine(s)»."""
        return sum(len(kept) for _d, kept in groups), len(groups)

    def units(self, accept=None):
        """The units of the project, the commonest first, then by name (UI-005) -- "" for a variable with none."""
        counted = {}
        for domain in self.domains:
            for var in domain.variables:
                if accepted(accept, var, domain):
                    counted[var.unit] = counted.get(var.unit, 0) + 1
        return [unit for unit, _n in sorted(counted.items(), key=lambda kv: (-kv[1], kv[0]))]

    # -- the tags of the search bar (UI-004) --

    def tags(self, f, words, badge):
        """[(kind, text)] of the filter, in the order the bar shows them -- the menu's entry («Actions › Actions variables»), the source («source : export»), the domain («Charge utile · A1 [export]») --; `words(key, **values)` the window's words, `badge(domain)` a domain's source as a tag says it."""
        out = []
        if f.menu and f.menu in self.nodes:
            out.append(("menu", " › ".join(self.nodes[f.menu].path)))
        if f.source not in (None, ALL_SOURCES):
            out.append(("source", words("vr_tag_source", source=words("vr_source_" + f.source).lower())))
        domain = self.by_key.get(tuple(f.domain)) if f.domain is not None else None
        if domain is not None:
            out.append(("domain", f"{self.tab_title(domain)} · {calc.case_of(domain)} [{badge(domain)}]"))
        return out


def without(f, kind):
    """The filter with the tag `kind` taken off (UI-004): the domain chosen, the source, the menu's entry."""
    if kind == "domain":
        f.domain = None
    elif kind == "source":
        f.source = ALL_SOURCES
    elif kind == "menu":
        f.menu = ALL
    return f


def last_tag(f):
    """The tag ⌫ in an empty bar takes off: the domain, then the source, then the menu's entry (UI-004); None where there is none."""
    if f.domain is not None:
        return "domain"
    if f.source not in (None, ALL_SOURCES):
        return "source"
    if f.menu:
        return "menu"
    return None
