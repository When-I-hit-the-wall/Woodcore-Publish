"""Which calculation each domain of the «Variables» tab is, and what follows from it (calc/variable_calc.py; spec 2026-10-24-onglet-variables-groupes, REQ-001 to REQ-004, ARCH-011, ARCH-012).

What is held here, and why each is worth a test rather than care:

⚠️ **The tab of a check is read off its record, never off its folder** (D-12): FE-01 and FE-02, checks in the
fire situation, are written under `Timber-checks/Bending/` and `Buckling/`, and a reading by folder would put
them in «Flexion» and «Flambage».

⚠️ **A document's domain is joined to its calculation by a table Woodcore wrote** (Q-001, A): a name found in
two kinds, or renamed in the export, stays without a calculation -- no resemblance of names is ever read.

⚠️ **Every key of the tables is a tab of `tab_registry`**: the one list of tab keys written outside it. When
issue #112 folds «Flambage» and «Déversement» away, the test fails naming the kind whose line to change.
"""

TIER = "fast"  # tests/run_tests.py --fast

import copy
import json
import re
import subprocess
import sys

import conftest
from conftest import ROOT, Skip

import variable_calc as calc
import variable_sources as sources
import variables as model


def _export():
    found = sources.read_export(conftest.PROJECT)
    assert not found.errors, [str(e) for e in found.errors]
    return found


def _var(key, value=1.0, unit="kN", domain=""):
    return model.Variable(key=key, domain=domain, value=value, unit=unit, symbol=key)


def _document(names):
    """A report's registry holding a domain of each name, as `variables.read` gives it -- fabricated, so no compile is paid for."""
    return model.Registry(stamp="pinned", domains={name: [_var(key, domain=name) for key in keys] for name, keys in names.items()})


def _assembled(registry=None, index=None, export=None):
    export = export or _export()
    domains = list(export.domains) + sources.registry_domains("rs", registry)
    return calc.assemble(domains, index if index is not None else export.index, documents_read=registry is not None), domains


def _find(domains, origin, name):
    return next(d for d in domains if d.origin == origin and d.name == name)


REPORT = {"SL": ["s_k", "q_k1"], "H": ["q_k", "Q_k"], "SD-10": ["R_k"], "S10 - 1 kN Mitte": ["M"], "BI-01": ["eta"]}


# ---------------------------------------------------------------- REQ-001: the tab of each domain

def test_every_domain_of_the_export_and_of_the_files_has_its_tab():
    found, domains = _assembled()
    missing = [(d.origin, d.name) for d in domains if d.tab is None]
    assert not missing, f"domains of the example with no tab: {missing}"
    tabs = {(d.origin, d.name): d.tab for d in domains}
    assert tabs[(calc.EXPORT, "snow-load · SL")] == "tab_ac_snow"
    assert tabs[(calc.FILES, "SL")] == "tab_ac_snow"
    assert tabs[(calc.FILES, "ZT-01")] == "tab_mc_tension"
    assert tabs[(calc.FILES, "poutre-p1")] == "tab_formula"
    assert tabs[(calc.EXPORT, "connection · VU-MP-1")] == tabs[(calc.FILES, "VU-MP-1")] == "tab_polar"
    assert tabs[(calc.EXPORT, "script · dreigelenk")] == "tab_python"
    assert tabs[(calc.FILES, "ST-01")] == "tab_st_bending"


def test_a_check_in_the_fire_situation_is_the_fire_tab_s_whatever_its_folder():
    """D-12, ARCH-RISK-001: FE-01 is a bending check written under Bending/, FE-02 a buckling one under Buckling/; both are «Résistance au feu»."""
    found, domains = _assembled()
    index = _export().index
    assert "/Bending/" in index["domain-files"]["check"]["FE-01"] and "/Buckling/" in index["domain-files"]["check"]["FE-02"]
    assert _find(domains, calc.FILES, "FE-01").tab == calc.FIRE_TAB
    assert _find(domains, calc.FILES, "FE-02").tab == calc.FIRE_TAB
    assert _find(domains, calc.FILES, "BI-01").tab == "tab_mc_bending"


def test_a_calculation_not_found_keeps_no_tab_and_is_never_left_out():
    export = _export()
    index = copy.deepcopy(export.index)
    index["checks"].pop("ZT-01")
    _found, domains = _assembled(index=index, export=export)
    zt = _find(domains, calc.FILES, "ZT-01")
    assert zt.tab is None and zt.calc == calc.CalcRef("check", "ZT-01"), "a check whose record is gone: no tab, still listed"
    assert zt in domains


# ---------------------------------------------------------------- REQ-002: a document's domain, by domain-files.json

def test_a_document_s_domain_is_joined_by_the_table_woodcore_wrote():
    found, domains = _assembled(_document(REPORT))
    sl = _find(domains, "rs", "SL")
    assert sl.calc == calc.CalcRef("snow-load", "SL") and sl.tab == "tab_ac_snow"
    assert _find(domains, "rs", "SD-10").tab == "tab_connections"
    assert _find(domains, "rs", "BI-01").tab == "tab_mc_bending"
    declared = _find(domains, "rs", "S10 - 1 kN Mitte")
    assert declared.calc is None and declared.tab is None, "a domain the report declares itself has no calculation"
    assert found.siblings(declared) == []


def test_a_name_held_by_two_kinds_stays_without_a_calculation_and_is_named():
    export = _export()
    index = copy.deepcopy(export.index)
    index["domain-files"]["connector"]["SL"] = "/Connectors/SL.typ"
    found, domains = _assembled(_document(REPORT), index=index, export=export)
    assert _find(domains, "rs", "SL").calc is None
    assert found.ambiguous == {"SL": ("snow-load", "connector")}, found.ambiguous


def test_a_case_renamed_in_the_export_no_longer_joins_the_document():
    """No resemblance of names: `SL` renamed `SL-2` in the table, the report's `SL` has no calculation any more."""
    export = _export()
    index = copy.deepcopy(export.index)
    index["domain-files"]["snow-load"] = {"SL-2": index["domain-files"]["snow-load"].pop("SL")}
    index["formulas"].pop("SL", None)
    _found, domains = _assembled(_document(REPORT), index=index, export=export)
    assert _find(domains, "rs", "SL").calc is None


# ---------------------------------------------------------------- REQ-003: the source that computes, the siblings, printed

def test_the_export_computes_the_others_recall_and_a_document_prints():
    found, domains = _assembled(_document(REPORT))
    export_sl = _find(domains, calc.EXPORT, "snow-load · SL")
    file_sl = _find(domains, calc.FILES, "SL")
    report_sl = _find(domains, "rs", "SL")
    for domain in (export_sl, file_sl, report_sl):
        assert found.computing(domain) is export_sl, domain.name
    assert found.siblings(export_sl) == [file_sl, report_sl]
    assert found.printed(export_sl) is True and found.printed(file_sl) is True
    # a calculation no document holds: not printed, once a document is read
    a1 = _find(domains, calc.EXPORT, "live-load · A1")
    assert found.printed(a1) is False
    assert found.node(export_sl) == found.node(report_sl) == "load:snow-load/SL"
    assert found.node(_find(domains, calc.FILES, "poutre-p1")) == "formula:poutre-p1"
    assert found.node(_find(domains, calc.FILES, "BI-01")) == "check:BI-01"
    assert found.path(file_sl) == "/Variable-loads/Snow/SL.typ"


def test_while_no_document_is_read_the_impression_is_unknown():
    found, domains = _assembled(None)
    assert found.printed(_find(domains, calc.EXPORT, "live-load · A1")) is None
    assert found.printed(_find(domains, calc.EXPORT, "snow-load · SL")) is None


def test_the_file_computes_where_the_export_has_no_domain():
    found, domains = _assembled(_document(REPORT))
    bi = _find(domains, calc.FILES, "BI-01")
    assert found.computing(_find(domains, "rs", "BI-01")) is bi


# ---------------------------------------------------------------- REQ-004, ARCH-012: the results, in every source

def test_a_result_of_the_export_is_one_in_every_source_that_recalls_it():
    found, domains = _assembled(_document(REPORT))
    for origin, name in ((calc.EXPORT, "live-load · A1"), (calc.FILES, "A1"), (calc.EXPORT, "live-load · H"), (calc.FILES, "H"), ("rs", "H")):
        assert "q_k" in _find(domains, origin, name).results, (origin, name)
    assert "q_k1" in _find(domains, "rs", "SL").results


def test_eta_is_the_last_eq_of_every_check_file_of_the_example():
    """ARCH-012: the constant the tab reads is the key every check's file prints its result with."""
    from domains import member_check, steel_check
    assert member_check.RESULT_KEY == steel_check.RESULT_KEY == "eta"
    files = _export().index["domain-files"]
    checked = 0
    for kind in ("check", "steel"):
        for ident, path in files[kind].items():
            text = (conftest.PROJECT.typst_root / path.lstrip("/")).read_text(encoding="utf-8")
            keys = re.findall(r'#eq\("([^"]+)"', text)
            assert keys and keys[-1] == calc.CHECK_RESULTS[kind][0], (kind, ident, keys[-3:])
            checked += 1
    assert checked >= 15, checked


def test_eta_is_a_result_of_each_check_in_its_file_and_in_its_document():
    found, domains = _assembled(_document(REPORT))
    for domain in domains:
        if domain.calc is not None and domain.calc.kind in ("check", "steel"):
            assert "eta" in domain.results, (domain.origin, domain.name)
    assert "eta" in _find(domains, "rs", "BI-01").results


def test_assembling_twice_changes_nothing():
    export = _export()
    first, _ = _assembled(_document(REPORT), export=export)
    before = {(d.origin, d.name): (d.tab, d.calc, d.results) for d in export.domains}
    _assembled(_document(REPORT), export=export)
    assert {(d.origin, d.name): (d.tab, d.calc, d.results) for d in export.domains} == before


# ---------------------------------------------------------------- the module and the tables

def test_the_module_imports_without_qt():
    code = ("import sys; sys.path.insert(0, r'%s'); sys.modules['PySide6'] = None; import variable_calc; "
            "assert not any(m.startswith('PySide6') and sys.modules[m] is not None for m in sys.modules)") % (ROOT / "calc")
    done = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=str(ROOT))
    assert done.returncode == 0, done.stderr


def test_every_key_of_the_tables_is_a_tab_of_the_registry():
    """ARCH-011: the tables are the one list of tab keys outside tab_registry; a key that is no TabSpec fails here, naming the kind whose line to change (issue #112 will, for buckling and lateral-torsional)."""
    try:
        import PySide6  # noqa: F401
    except ImportError as exc:
        raise Skip(f"PySide6 is not installed ({exc})")
    sys.path.insert(0, str(ROOT / "calc" / "tools")) if str(ROOT / "calc" / "tools") not in sys.path else None
    import tab_registry
    keys = {spec.key for spec in tab_registry.SPECS}
    wrong = [("calculation", kind, tab) for kind, tab in calc.CALC_TABS.items() if tab not in keys]
    wrong += [(table, kind, tab) for table, tabs in calc.CHECK_TABS.items() for kind, tab in tabs.items() if tab not in keys]
    if calc.FIRE_TAB not in keys:
        wrong.append(("fire", "fire", calc.FIRE_TAB))
    assert not wrong, "kinds whose tab is no TabSpec of tab_registry (change their line in calc/variable_calc.py): " + ", ".join(f"{t} {k!r} -> {v!r}" for t, k, v in wrong)


def test_the_kinds_of_the_tables_are_the_kinds_the_export_writes():
    """A kind of domain-files.json with no line here would be a calculation listed «Sans onglet»: each kind of the example has its line."""
    files = _export().index["domain-files"]
    for kind in files:
        if kind in calc.NOT_CALCULATIONS:
            continue
        assert kind in calc.CALC_TABS or kind in calc.CHECK_TABS, kind
    checks = json.loads((conftest.PROJECT.data_dir / "checks.json").read_text(encoding="utf-8"))["checks"]
    assert {r["kind"] for r in checks.values()} <= set(calc.CHECK_TABS["check"])
