"""Every variable of a project and where it comes from (calc/variable_sources.py, calc/variables.py; spec 2026-10-08-onglet-variables-trois-colonnes, the engineer's issue 13).

What is held here, and why each is worth a test rather than care:

⚠️ **No variable of the loads tab is missing** (REQ-008). The engineer: «Supprimer l'onglet Charges une fois
vérifié qu'aucune de ses variables ne manque dans Variables». This is that check, and it outlives the tab: every
var of every instance of data/calculations.json is in the reading, with the name, symbol, value, unit and label
the loads tab printed.

⚠️ **A `source` prefix nobody named fails the suite.** `source` is free text in every schema, so a module that
writes a fifth kind would otherwise be shown as «unknown» provenance without anyone deciding it -- the
`woodcore:` prefix of the connectors' inputs was found that way, by the architecture review.

⚠️ **A registry's variable is Typst's whatever its `source` says**: `#var` copies an export's var, `excel:` and
all, into a document's registry.
"""

TIER = "fast"  # tests/run_tests.py --fast

import json
import subprocess
import sys

import conftest
import line_levels
from conftest import ROOT

import variable_sources as sources
import variables as model

# the cache sits in the user's cache folder, which calc/usersettings.py names (as tests/test_variables.py does)
sys.path.insert(0, str(ROOT / "calc" / "tools")) if str(ROOT / "calc" / "tools") not in sys.path else None


def _export(here=None):
    return sources.read_export(here or conftest.PROJECT)


def _by_address(found):
    return {domain.address: domain for domain in found.domains}


# ---------------------------------------------------------------- provenance

def test_a_source_prefix_means_one_provenance():
    assert model.provenance_of("excel:Belastungsannahmen.xlsm!SL!H10") == model.EXCEL
    assert model.provenance_of("python:domains/dead_load.py") == model.WOODCORE
    assert model.provenance_of("norm:SIA 261:2020, Tabelle 8") == model.WOODCORE
    assert model.provenance_of("woodcore:connectors/SD-10.json") == model.WOODCORE
    assert model.provenance_of("") == model.UNKNOWN
    assert model.provenance_of("Python") == model.UNKNOWN, "no prefix: never guessed from a word"
    assert model.provenance_of("rfem:model.xlsx") == model.UNKNOWN


def test_parse_source_reads_a_cell_and_leaves_the_rest_whole():
    assert model.parse_source("excel:Belastungsannahmen.xlsm!WL-Velo!J6") == ("excel", "Belastungsannahmen.xlsm", "WL-Velo", "J6")
    assert model.parse_source("excel:B.xlsm!Sheet!With!Bang!A1") == ("excel", "B.xlsm", "Sheet!With!Bang", "A1")
    assert model.parse_source("norm:SIA 261:2020, Tabelle 8") == ("norm", "", "", "SIA 261:2020, Tabelle 8")
    assert model.parse_source(None) == ("", "", "", "")


def test_a_registry_variable_is_typst_whatever_its_source_says():
    copied = model.Variable(key="s_k", domain="", value=1.2, unit="kN/m²", symbol="s_k", source="excel:B.xlsm!SL!H40")
    assert sources.provenance(copied, "rs") == model.TYPST
    assert sources.provenance(copied, "cu") == model.TYPST
    assert sources.provenance(copied, sources.EXPORT) == model.EXCEL


def test_every_source_of_the_example_has_a_known_provenance():
    """A sweep of every var of the four files: a prefix this table does not know fails here, by name, rather than reaching the window as «unknown»."""
    found = _export()
    assert not found.errors, [str(e) for e in found.errors]
    unknown = [(domain.name, var.key, var.source) for domain in found.domains for var in domain.variables
               if model.parse_source(var.source)[0] not in model.PROVENANCE]
    assert not unknown, f"a source prefix variables.PROVENANCE does not name: {unknown[:5]}"
    seen = {model.parse_source(var.source)[0] for domain in found.domains for var in domain.variables}
    assert {"excel", "python", "norm", "woodcore"} <= seen, seen


# ---------------------------------------------------------------- what is read

def test_no_variable_of_the_loads_tab_is_missing():
    """REQ-008: every var of every instance of calculations.json, as the loads tab listed it -- name, symbol, value, unit, label."""
    here = conftest.PROJECT
    data = json.loads((here.data_dir / sources.CALCULATIONS_FILE).read_text(encoding="utf-8"))
    found = _by_address(_export(here))
    checked = 0
    for calc_id, calc in data["domains"].items():
        for instance_id, instance in calc["instances"].items():
            domain = found.get((calc_id, instance_id))
            assert domain is not None, f"the domain {calc_id} · {instance_id} is missing"
            assert domain.name == f"{calc_id} · {instance_id}"
            for key, v in instance["vars"].items():
                var = domain.variable(key)
                assert var is not None, f"{calc_id} · {instance_id} · {key} is missing"
                assert var.symbol == (v.get("symbol") or key), (key, var.symbol)
                assert var.value == v["value"], (key, var.value)
                assert var.unit == (v.get("unit") or ""), (key, var.unit)
                assert var.label == (v.get("label") or ""), (key, var.label)
                assert var.level == line_levels.level(calc_id, key, own=v.get("level")), (key, var.level)   # the table's since v0.120 (UI-002)
                checked += 1
            assert domain.results == tuple(instance.get("results") or ()), domain.name
    assert checked > 100, f"only {checked} variables checked: the example should carry its loads"


def test_the_order_is_the_export_own():
    here = conftest.PROJECT
    data = json.loads((here.data_dir / sources.CALCULATIONS_FILE).read_text(encoding="utf-8"))
    expected = [(c, i) for c, calc in data["domains"].items() for i in calc["instances"]]
    read = [d.address for d in _export(here).domains if d.address and d.address[0] in data["domains"]]
    assert read == expected


def test_a_loads_variable_carries_its_traceability():
    found = _by_address(_export())
    snow = found[("snow-load", "SL")]
    assert snow.workbook and snow.sheet == "SL", (snow.workbook, snow.sheet)
    assert snow.label == "Schneelast"
    assert snow.formulas.get("h_ref") == 'h_"ref" = h_0 + Delta h'
    live = found[("live-load", "A1")]
    assert live.variable("kategorie").source.startswith("norm:")
    chosen = [var for domain in found.values() for var in domain.variables if var.choices]
    assert chosen, "a var chosen from a list keeps its choices"


def test_the_polar_moments_the_connectors_and_the_scripts_are_listed():
    """What the Variables tab did not list before issue 13: Woodcore's own calculations."""
    found = _export()
    words = {domain.calculation for domain in found.domains}
    assert {"connection", "connector", "script"} <= words, words
    connection = next(d for d in found.domains if d.calculation == "connection")
    assert connection.name == f"connection · {connection.address[1]}"
    assert connection.variable("I_p") is not None and connection.variable("I_p").unit == "mm²"
    connector = next(d for d in found.domains if d.calculation == "connector" and d.variables)
    assert any(var.source.startswith("woodcore:") for var in connector.variables)
    script = next(d for d in found.domains if d.address == ("script", "dreigelenk"))
    assert sources.provenance(script.variable("H_d"), sources.EXPORT) == model.WOODCORE


def test_a_registry_becomes_domains_marked_with_its_document():
    registry = model.Registry(domains={
        "": [model.Variable(key="a", domain="", value=1, unit="", symbol="a")],
        "S001-verify-bending": [model.Variable(key="eta", domain="S001-verify-bending", value=0.5, unit="", symbol="eta")],
    })
    domains = sources.registry_domains("bp", registry)
    assert [(d.name, d.origin, d.kind, d.address) for d in domains] == [("", "bp", "report", None), ("S001-verify-bending", "bp", "check", None)]
    assert sources.registry_domains("rs", None) == []


# ---------------------------------------------------------------- what is not there, what is broken

def test_a_project_not_exported_is_missing_and_never_an_error():
    here = conftest.project_copy("vs_not_exported", data=False)
    found = sources.read_export(here)
    assert found.domains == [] and found.errors == []
    assert sorted(found.missing) == sorted(name for name, _schema, _reader in sources.FILE_SOURCES)


def test_a_broken_file_is_named_and_the_others_are_read_all_the_same():
    here = conftest.project_copy("vs_broken")
    path = here.data_dir / "connections.json"
    path.write_text(path.read_text(encoding="utf-8")[:200], encoding="utf-8")
    found = sources.read_export(here)
    assert len(found.errors) == 1, [str(e) for e in found.errors]
    error = found.errors[0]
    assert error.code == "bad_file" and error.detail["file"] == "connections.json", error.detail
    assert any(d.address and d.address[0] == "snow-load" for d in found.domains), "the loads are still read"


def test_a_file_against_its_schema_names_the_field():
    here = conftest.project_copy("vs_schema")
    path = here.data_dir / "scripts.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["scripts"]["dreigelenk"]["vars"]["H_d"]["value"] = {"not": "a value"}
    path.write_text(json.dumps(data), encoding="utf-8")
    found = sources.read_export(here)
    assert [e.detail["file"] for e in found.errors] == ["scripts.json"]
    assert "H_d" in found.errors[0].detail["field"], found.errors[0].detail


# ---------------------------------------------------------------- what it does not do

def _tree(root):
    return {str(p.relative_to(root)): (p.stat().st_size, p.stat().st_mtime_ns) for p in root.rglob("*") if p.is_file()}


def test_reading_writes_nothing_into_the_project():
    here = conftest.project_copy("vs_readonly")
    before = _tree(here.root)
    sources.read_export(here)
    assert _tree(here.root) == before


def test_the_module_is_qt_free():
    code = ("import sys; sys.path.insert(0, r'%s'); import variable_sources, variables; "
            "assert not any(m.startswith('PySide6') for m in sys.modules), 'Qt imported'") % (ROOT / "calc")
    done = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=str(ROOT))
    assert done.returncode == 0, done.stderr


def test_the_new_fields_do_not_reach_the_cache():
    """ARCH-004: `level` and `choices` are the export's, never written into a registry's cache, so CACHE_VERSION did not move and a cache written before reads the same."""
    here = conftest.project_copy("vs_cache")
    registry = model.Registry(domains={"": [model.Variable(key="a", domain="", value=1, unit="m", symbol="a", level=2, choices=({"value": 1},))]}, stamp="s")
    path = model.save(registry, here)
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["cache_version"] == 1
    assert set(payload["domains"][""]["a"]) == {"value", "unit", "symbol", "label", "description", "norm", "norm_ref", "source"}
    back = model.cached(here)
    assert back.domains[""][0].level is None and back.domains[""][0].choices == ()


def test_the_export_file_names_are_the_modules_own():
    from domains import connection, connector, script
    names = [name for name, _schema, _reader in sources.FILE_SOURCES]
    # the four of issue 13 first; a source added since (the Formule tab's domains) comes after them
    assert names[:4] == ["calculations.json", connection.EXPORT_FILE, connector.EXPORT_FILE, script.EXPORT_FILE], names
    assert (connection.EXPORT_FILE, connector.EXPORT_FILE, script.EXPORT_FILE) == ("connections.json", "connectors.json", "scripts.json")
