"""The menu of the tabs, the filter and the list grouped by domain of the «Variables» tab (calc/variable_query.py; spec 2026-10-24-onglet-variables-groupes, UI-002, UI-003, UI-005, UI-006, ARCH-001, ARCH-005).

⚠️ **The menu's entries are the ones it is given**: the model reads no list of tabs of its own (ARCH-005). The
navigation is given in argument here, and, in the one Qt test, `tab_registry`'s own -- every `TabSpec` found
in it, the sections the window draws.

⚠️ **The list is always grouped by domain** (UI-006): `q_k`, more than sixty rows on a flat list before, is
found under a title line per domain, and a domain left with nothing has no title.
"""

TIER = "fast"  # tests/run_tests.py --fast

import subprocess
import sys

import conftest
from conftest import ROOT, Skip

import variable_calc as calc
import variable_query as query
import variable_sources as sources
import variables as model
from domains import links

# A navigation of the window's shape (tab_registry.NAV_GROUPS, NAV_SECTIONS), given as the window gives it.
GROUPS = (
    ("nav_document_group", ("tab_project", "tab_structure")),
    ("nav_project", ("tab_python",)),
    ("nav_actions", ("tab_ac_selfweight", "tab_ac_imposed", "tab_ac_snow", "tab_ac_wind", "tab_ac_seismic", "tab_combinations")),
    ("nav_connections", ("tab_connections", "tab_polar")),
    ("nav_safety", ("tab_mc_tension", "tab_mc_compression", "tab_mc_bending", "tab_mc_shear", "tab_mc_torsion", "tab_mc_fire")),
    ("nav_steel", ("tab_st_profiles", "tab_st_class", "tab_st_tension", "tab_st_compression", "tab_st_bending", "tab_st_shear")),
    ("nav_reference", ("tab_formula", "tab_variables")),
)
SECTIONS = {"tab_ac_selfweight": "nav_permanent", "tab_ac_imposed": "nav_variable", "tab_combinations": "",
            "tab_st_profiles": "nav_steel_section", "tab_st_tension": "nav_steel_safety"}
TITLES = {"tab_ac_snow": "Neige", "tab_ac_imposed": "Charge utile", "nav_actions": "Actions", "nav_variable": "Actions variables"}


def _title(key):
    return TITLES.get(key, key)


def _var(key, value=1.0, unit="kN", domain=""):
    return model.Variable(key=key, domain=domain, value=value, unit=unit, symbol=key)


REPORT = {"SL": [("s_k", 1.394, "kN/m²"), ("q_k1", 1.115, "kN/m²")], "H": [("q_k", 3.0, "kN/m²"), ("Q_k", 3.0, "kN")],
          "S10 - 1 kN Mitte": [("M", 0.75, "kNm")]}


def _catalogue(registry=True, documents=(("rs", "Rapport de statique"),)):
    export = sources.read_export(conftest.PROJECT)
    reg = model.Registry(stamp="pinned", domains={name: [_var(k, v, u, name) for k, v, u in rows] for name, rows in REPORT.items()}) if registry else None
    domains = list(export.domains) + sources.registry_domains("rs", reg)
    assembly = calc.assemble(domains, export.index, documents_read=reg is not None)
    roots = query.navigation(GROUPS, SECTIONS, _title, documents=documents, none_title="Sans onglet")
    return query.Catalogue(assembly, roots)


_CACHE = {}


def _cat():
    if "cat" not in _CACHE:
        _CACHE["cat"] = _catalogue()
    return _CACHE["cat"]


# ---------------------------------------------------------------- the menu (UI-002)

def test_the_menu_is_the_navigation_it_is_given_in_its_order_sections_included():
    roots = query.navigation(GROUPS, SECTIONS, _title, documents=(("rs", "RS"), ("bp", "BP")), none_title="Sans onglet")
    assert [r.id for r in roots] == ["g:" + g for g, _k in GROUPS] + [query.NO_TAB]
    actions = roots[2]
    assert [c.kind for c in actions.children] == ["section", "section", "tab"], "permanent, variable, then the combinations after the line"
    assert [t.id for t in actions.children[1].children] == ["tab_ac_imposed", "tab_ac_snow", "tab_ac_wind", "tab_ac_seismic"]
    assert actions.children[1].path == ("Actions", "Actions variables")
    assert actions.children[1].children[1].path == ("Actions", "Actions variables", "Neige")
    assert actions.tabs == GROUPS[2][1], "a group takes every tab under it"
    document = roots[0]
    assert [c.id for c in document.children] == ["tab_project", "tab_structure", "doc:rs", "doc:bp"], "one entry per document made (D-14)"
    flat = [n.id for n in query.walk(roots) if n.kind == "tab"]
    assert flat == [k for _g, keys in GROUPS for k in keys], "every tab given, in its order"
    # a tab added to the navigation appears with no other change
    more = query.navigation(GROUPS + (("nav_others", ("tab_new",)),), SECTIONS, _title)
    assert "tab_new" in [n.id for n in query.walk(more)]


def test_an_entry_counts_its_variables_in_the_source_and_a_group_is_the_sum_of_its_tabs():
    cat = _cat()
    for source in query.SOURCE_FILTERS:
        for node in query.walk(cat.roots):
            if node.children:
                assert cat.count(node.id, source) == sum(cat.count(c.id, source) for c in node.children), (node.id, source)
    snow = cat.count("tab_ac_snow", query.ALL_SOURCES)
    assert snow == cat.count("tab_ac_snow", calc.SOURCE_EXPORT) + cat.count("tab_ac_snow", calc.SOURCE_FILE) + cat.count("tab_ac_snow", calc.SOURCE_DOCUMENT)
    assert cat.count("tab_ac_snow", calc.SOURCE_DOCUMENT) == 2
    rows = dict((n.id, c) for n, c in cat.menu_rows(query.ALL_SOURCES))
    assert rows["tab_ac_seismic"] == 0 and rows["tab_st_profiles"] == 0, "a reserved tab and a tab of no variable are at zero (greyed)"
    assert rows["doc:rs"] == 1, "the report's own domain, under its document"
    assert rows[query.NO_TAB] == 0
    assert cat.count(query.ALL, query.ALL_SOURCES) == sum(len(d.variables) for d in cat.domains)


def test_while_a_field_is_linked_only_the_values_it_takes_are_counted():
    cat = _cat()
    accept = lambda var, domain: sources.linkable(var, domain, "kN", links.ANY)   # noqa: E731
    assert cat.count("doc:rs", query.ALL_SOURCES, accept) == 0, "a document's value is never offered to a field"
    assert cat.count("tab_ac_snow", calc.SOURCE_DOCUMENT, accept) == 0
    for node, n in cat.menu_rows(query.ALL_SOURCES, accept):
        expected = sum(1 for d in cat.domains if cat.in_menu(d, node.id) for v in d.variables if accept(v, d))
        assert n == expected, node.id
    side = [d for _t, rows in cat.side(query.Filter(), accept) for d, _n in rows]
    assert side and all(calc.source_of(d) != calc.SOURCE_DOCUMENT for d in side)
    assert all(any(accept(v, d) for v in d.variables) for d in side), "a domain with nothing the field takes is not offered"


# ---------------------------------------------------------------- the source and the domains (UI-003)

def test_the_domains_are_under_their_tab_in_the_order_of_the_navigation():
    cat = _cat()
    side = cat.side(query.Filter())
    titles = [t for t, _rows in side]
    assert len(titles) == len(set(titles)), "a tab's title once"
    order = [n.title for n in query.walk(cat.roots) if n.kind in ("tab", "document", "none")]
    assert titles == [t for t in order if t in titles], titles
    snow = dict(side)["Neige"]
    assert [(calc.source_of(d), calc.case_of(d)) for d, _n in snow] == [("export", "SL"), ("file", "SL"), ("document", "SL")]
    export_only = cat.side(query.Filter(source=calc.SOURCE_EXPORT))
    assert all(calc.source_of(d) == calc.SOURCE_EXPORT for _t, rows in export_only for d, _n in rows)


def test_a_domain_no_document_prints_is_said_and_never_while_the_impression_is_unknown():
    cat = _cat()
    a1 = cat.by_key[("export", "live-load · A1")]
    assert cat.assembly.printed(a1) is False
    unread = _catalogue(registry=False)
    assert unread.assembly.printed(unread.by_key[("export", "live-load · A1")]) is None


def test_a_second_click_on_a_domain_lets_it_go():
    f = query.Filter(domain=("export", "snow-load · SL"))
    assert query.last_tag(f) == "domain"
    query.without(f, "domain")
    assert f.domain is None


# ---------------------------------------------------------------- the search, the unit, the results, the count (UI-005)

def test_every_word_typed_is_found_in_the_filter():
    cat = _cat()
    groups = cat.groups(query.Filter(text="kn neige"))
    assert groups
    for domain, kept in groups:
        for var in kept:
            assert "kn" in var.unit.lower(), (domain.name, var.key, var.unit)
        assert "neige" in (calc.case_of(domain) + " " + cat.tab_title(domain)).lower() or all("neige" in cat.haystack(v, domain) for v in kept)
    assert {cat.tab_title(d) for d, _k in groups} == {"Neige"}


def test_results_only_keeps_results_and_the_count_is_the_list_s():
    cat = _cat()
    f = query.Filter(results_only=True)
    groups = cat.groups(f)
    assert all(v.key in d.results for d, kept in groups for v in kept)
    count, domains = cat.totals(groups)
    assert count == len(cat.shown_keys(groups)) and domains == len(groups)
    # the results of A1 in its two sources (REQ-004)
    keys = cat.shown_keys(groups)
    assert ("export", "live-load · A1", "q_k") in keys and ("formulas", "A1", "q_k") in keys


def test_the_unit_filter_keeps_one_unit_and_offers_the_commonest_first():
    cat = _cat()
    units = cat.units()
    counts = [sum(1 for d in cat.domains for v in d.variables if v.unit == u) for u in units]
    assert counts == sorted(counts, reverse=True)
    groups = cat.groups(query.Filter(unit="kN"))
    assert groups and all(v.unit == "kN" for _d, kept in groups for v in kept)


# ---------------------------------------------------------------- the list, grouped (UI-006)

def test_the_list_is_grouped_by_domain_and_no_title_is_without_a_variable():
    cat = _cat()
    groups = cat.groups(query.Filter(text="q_k"))
    domains = [d for d, _k in groups]
    assert len(domains) == len(set(id(d) for d in domains)), "a domain's variables are contiguous under one title"
    assert len(groups) > 10 and all(kept for _d, kept in groups)
    keys = cat.shown_keys(groups)
    assert sum(1 for k in keys if k[2] == "q_k") >= 20
    # the order of the navigation: every group's tab comes no earlier than the one before it
    positions = [cat.order[query.menu_key(d)] for d in domains]
    assert positions == sorted(positions)


def test_the_menu_and_the_domain_narrow_the_list():
    cat = _cat()
    actions = "g:nav_actions"
    groups = cat.groups(query.Filter(menu=actions))
    assert groups and all(query.menu_key(d) in cat.nodes[actions].tabs for d, _k in groups)
    one = cat.groups(query.Filter(domain=("formulas", "SL")))
    assert [(d.origin, d.name) for d, _k in one] == [("formulas", "SL")]


def test_the_tags_say_the_menu_the_source_and_the_domain_in_that_order():
    cat = _cat()
    words = {"vr_tag_source": "source : {source}", "vr_source_export": "Export"}
    f = query.Filter(menu="s:nav_actions:tab_ac_imposed", source=calc.SOURCE_EXPORT, domain=("export", "live-load · A1"))
    tags = cat.tags(f, lambda key, **v: words[key].format(**v), lambda d: "export")
    assert tags == [("menu", "Actions › Actions variables"), ("source", "source : export"), ("domain", "Charge utile · A1 [export]")]
    assert query.last_tag(f) == "domain"
    query.without(f, "domain")
    assert query.last_tag(f) == "source"
    query.without(f, "source")
    assert query.last_tag(f) == "menu"
    query.without(f, "menu")
    assert query.last_tag(f) is None


def test_the_module_imports_without_qt():
    code = ("import sys; sys.path.insert(0, r'%s'); sys.modules['PySide6'] = None; "
            "import variable_calc, variable_query, variable_select, variable_card") % (ROOT / "calc")
    done = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=str(ROOT))
    assert done.returncode == 0, done.stderr


# ---------------------------------------------------------------- the navigation of the window itself (Qt)

def test_the_menu_of_the_registry_holds_every_tab_and_the_window_s_sections():
    """UI-002, ARCH-RISK-002: the model given tab_registry's navigation finds every TabSpec in it, and applies the sections as the window's own navigation draws them; the document group is one of NAV_GROUPS."""
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:
        raise Skip(f"PySide6 is not installed ({exc})")
    sys.path.insert(0, str(ROOT / "calc" / "tools")) if str(ROOT / "calc" / "tools") not in sys.path else None
    import tab_registry
    import woodcore_gui
    from chrome import ICON_KEY
    QApplication.instance() or QApplication([])
    window = woodcore_gui.MainWindow()
    try:
        roots = query.navigation(tab_registry.NAV_GROUPS, tab_registry.NAV_SECTIONS, window.t)   # in the window's own words
        tabs = [n.id for n in query.walk(roots) if n.kind == "tab"]
        assert sorted(tabs) == sorted(spec.key for spec in tab_registry.SPECS)
        assert query.DOCUMENT_GROUP in dict(tab_registry.NAV_GROUPS)
        drawn = {}
        for row, entries, _head in window.nav.sections:
            for item in entries:
                drawn[item.data(ICON_KEY)] = row.text() or None
        ours = {key: title for _g, rows in query.sections_of(roots) for key, title in rows}
        assert {k: drawn.get(k) for k in ours} == ours, ("the menu's sections are not the navigation's", {k: (drawn.get(k), v) for k, v in ours.items() if drawn.get(k) != v})
        assert [n.title for n in roots if n.kind == "group"] == [head.text() for head, _rows in window.nav.groups], "the groups' words are the window's"
    finally:
        conftest.dispose(window)
