"""Every domain of calc/domains/ is held to the shape it promises (spec 2026-10-19-base-saine-nettoyage, ARCH-003: C3, C5, C7).

* C5 -- a source domain and an export domain are the two protocols of calc/domains/contracts.py; the tables below name every domain that is one, and a module that reads sources or writes an export without a row here fails, so a new domain is written to the contract from its first day.
* C3 -- a source is checked against its contract in schemas/ before anything else: the steel checks and the profiles, the two that were not, refuse what their schema refuses.
* C7 -- what an export can stop on is a ValidationError, which `export_all` reports as a defect of the input, «export failed: …», and not as a traceback.
"""

TIER = "fast"  # tests/run_tests.py --fast

import ast
import contextlib
import importlib
import io

from conftest import ROOT

import validation
from domains import contracts

SOURCE_DOMAINS = ("annex", "connection", "connector", "dead_load_source", "fire", "member_check", "plan", "profile", "schema",
                  "snow_source", "statics", "steel_check", "wind_source")
EXPORT_DOMAINS = ("domains.annex", "domains.connection", "domains.connector", "domains.fire", "domains.formula_domain", "domains.member_check",
                  "domains.plan", "domains.schema", "domains.script", "domains.statics", "domains.steel_check", "journal")


def _defines(path, names):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    defined = {n.name for n in tree.body if isinstance(n, ast.FunctionDef)}
    defined |= {a.asname or a.name for n in tree.body if isinstance(n, ast.ImportFrom) for a in n.names}
    return all(name in defined for name in names)


def test_every_source_domain_is_one():
    for name in SOURCE_DOMAINS:
        module = importlib.import_module("domains." + name)
        assert isinstance(module, contracts.SourceDomain), f"domains.{name} lacks read_source, check_source or SOURCE_SCHEMA_VERSION"
        assert isinstance(module.SOURCE_SCHEMA_VERSION, str)


def test_every_export_domain_is_one():
    for name in EXPORT_DOMAINS:
        module = importlib.import_module(name)
        assert isinstance(module, contracts.ExportDomain), f"{name} lacks prepare, write, export or EXPORT_SCHEMA_VERSION"
        assert isinstance(module.EXPORT_SCHEMA_VERSION, str)


def test_a_domain_that_reads_sources_or_writes_an_export_has_its_row():
    """A module of calc/domains/ defining read_source and check_source is in SOURCE_DOMAINS; one defining prepare, write and export is in EXPORT_DOMAINS."""
    for path in sorted((ROOT / "calc" / "domains").glob("*.py")):
        name = path.stem
        if _defines(path, ("read_source", "check_source")) and name != "script":   # a script's source is Python, read by its runner: no schema_version of its own
            assert name in SOURCE_DOMAINS, f"domains.{name} reads sources -- give it a row of SOURCE_DOMAINS"
        if _defines(path, ("prepare", "write", "export")):
            assert "domains." + name in EXPORT_DOMAINS, f"domains.{name} writes an export -- give it a row of EXPORT_DOMAINS"


def test_steel_and_profile_sources_are_checked_against_their_schema_first():
    """C3: a field of the wrong type that the checks written by hand do not look at is refused by the contract, naming the file."""
    from domains import profile, steel_check
    steel = steel_check.new_source("ST-01")
    steel["label"] = 12   # a string in schemas/steel-source.schema.json
    try:
        steel_check.check_source(steel, "ST-01.json")
    except validation.ValidationError as exc:
        assert str(exc) == "ST-01.json.label: expected string, got int", exc   # the schema's words, rooted at the file
    else:
        raise AssertionError("a steel check whose label is a number was read")
    prof = profile.new_source("P-01")
    prof["name"] = ["not", "a", "string"]
    try:
        profile.check_source(prof, "P-01.json")
    except validation.ValidationError as exc:
        assert str(exc) == "P-01.json.name: expected string, got list", exc
    else:
        raise AssertionError("a profile whose name is a list was read")


def test_what_an_export_stops_on_is_reported_as_a_defect_of_the_input():
    """C7: UnfoldError, DomainError and FormulaError are ValidationErrors (DomainError and FormulaError still ValueErrors for the callers that catch one), so `export_all` says «export failed: …» and exits 1 -- before v0.120 they left a traceback."""
    import export_all
    import units
    from domains import formula_domain, unfold
    stops = (unfold.UnfoldError("a check that cannot be unfolded", "probe"), formula_domain.DomainError("probe", "a key used twice"), units.FormulaError("a sum of two dimensions"))
    assert all(isinstance(exc, validation.ValidationError) for exc in stops)
    assert isinstance(stops[1], ValueError) and isinstance(stops[2], ValueError)
    real_run, real_take = export_all.run, export_all.project.take_argument
    for exc in stops:
        def raising(**_kwargs):
            raise exc
        export_all.run = raising
        export_all.project.take_argument = lambda argv: (None, [])
        err = io.StringIO()
        try:
            with contextlib.redirect_stderr(err):
                export_all.main()
        except SystemExit as stop:
            assert stop.code == 1, (type(exc).__name__, stop.code)
        else:
            raise AssertionError(f"{type(exc).__name__} did not stop the export")
        finally:
            export_all.run, export_all.project.take_argument = real_run, real_take
        assert err.getvalue().startswith("export failed: "), (type(exc).__name__, err.getvalue())


def test_every_row_and_var_of_a_check_cites_its_norm():
    """C1, C2, Q-011: a row of a member check passes engine._check_citation, a row with a clause names its norm, a fire row its clause of SIA 265 4.5.2; every var of a steel check names its norm, and a value the engineer entered cites the clause of the verdict it serves."""
    import conftest
    import engine
    from domains import member_check, steel_check
    try:
        member_check._row("x", "x", 1.0, "", clause="4.2.1", norm="")   # timber_calc.line, which engine.var checks (REQ-003)
    except engine.EngineError:
        pass
    else:
        raise AssertionError("a row without a norm was built")
    checks = conftest.exported(member_check.EXPORT_FILE)["checks"]
    rows = [row for record in checks.values() if record.get("calculable") for row in (member_check.compute(record) or {"rows": []})["rows"]]
    assert rows and all(row.get("norm") for row in rows if row.get("clause")), [row["key"] for row in rows if row.get("clause") and not row.get("norm")]
    fire_rows = {row["key"]: row for record in checks.values() if record.get("calculable") and record.get("fire") for row in member_check.compute(record)["rows"]}
    assert fire_rows and all(fire_rows[k].get("clause", "").startswith(("4.5.2", "Tabelle 13")) for k in ("t_fi", "beta_n", "d_red", "d_ef", "k_fi")), {k: fire_rows[k].get("clause") for k in fire_rows}
    steel = conftest.exported(steel_check.EXPORT_FILE)
    entered = False
    assert steel["schema_version"] == steel_check.EXPORT_SCHEMA_VERSION
    for cid, record in steel["checks"].items():
        if not record.get("calculable"):
            continue
        for key, var in record["vars"].items():
            assert var["norm"], (cid, key)
        for key in ("N_Ed", "M_y_Ed", "M_z_Ed", "V_z_Ed", "V_y_Ed"):
            var = record["vars"].get(key)
            if var is not None:   # a force entered: the clause of its verdict, never the norm as a whole
                assert var["norm"] == "SIA 263" and var["norm_ref"].startswith("5."), (cid, key, var["norm"], var["norm_ref"])
                entered = True
    assert entered, "no steel check of the example carries a force -- the test would hold nothing"


def test_no_domain_prints_what_it_has_to_say():
    """C4: a warning of a domain goes into the export's list as an engine.Note, said in the window's language -- never to the console, where nobody reads it (registry's sheetless domain and wind's unchecked surfaces did until v0.120); every code a domain gives a Note is worded in the three languages."""
    found = []
    for path in sorted((ROOT / "calc" / "domains").glob("*.py")) + [ROOT / "calc" / "registry.py"]:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        found += [f"{path.name}:{n.lineno}" for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "print"]
    assert not found, found
    # each said in the window's three languages (woodcore_gui.note_text reads `"warn_" + code`)
    # the window's words: woodcore_gui_words.py and the tabs' own STRINGS it merges (CLAUDE.md)
    words = "".join(path.read_text(encoding="utf-8") for path in sorted((ROOT / "calc" / "tools").glob("*.py")))
    # the codes a domain gives a Note, read off the code itself: every one of them worded (spec 2026-10-21-restes-issue-69 added the sheets' and the sources' own)
    import re
    codes = set()
    for path in sorted((ROOT / "calc" / "domains").glob("*.py")) + [ROOT / "calc" / "registry.py"]:
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Call) and getattr(node.func, "attr", getattr(node.func, "id", "")) == "Note" and node.args:
                first = node.args[0]
                if isinstance(first, ast.Constant) and isinstance(first.value, str):
                    codes.add(first.value)
                elif isinstance(first, ast.BinOp) and isinstance(first.left, ast.Constant) and "def notes_of(" in path.read_text(encoding="utf-8"):
                    # "snow_" + code: a source's notes_of, the codes its warnings() gives
                    source = path.read_text(encoding="utf-8")
                    codes.update(first.left.value + c for pair in re.findall(r'out\.append\(\("(\w+)"|return \[\("(\w+)"', source) for c in pair if c)
    assert {"registry_no_sheet", "sheet_value_differs", "snow_above_limit", "wind_c_red_outside"} <= codes, codes
    for code in sorted(codes):
        assert words.count('"warn_%s":' % code) == 3, code


def test_a_formula_composes_its_constants_from_the_values_it_computes_with():
    """UI-004: a constant a domain's formula shows is composed from the value the calculation uses (`%s` filled from calc/norms/), never typed into the string -- outside steel_resistance.py, which N1 leaves aside. Geometry's own numbers are no norm values and stay: a half, a square, a quarter circle."""
    import re
    allowed = {"2", "3", "4", "6", "12", "32", "90", "180", "100", "1000"}
    found = []
    for path in sorted((ROOT / "calc" / "domains").glob("*.py")):
        if path.name == "steel_resistance.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.keyword) and node.arg == "formula" and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                text = re.sub(r'"[^"]*"', "", node.value.value)
                text = re.sub(r"_\([^)]*\)|_\w+", "", text)   # a subscript names, it does not compute: q_(p 0)
                numbers = [m for m in re.findall(r"(?<![\w.,(])\d+(?:\.\d+)?(?![\w.])", text) if m not in allowed]
                if numbers:
                    found.append(f"{path.name}:{node.value.lineno} {numbers}")
    assert not found, found


def test_every_domain_the_graph_reads_by_its_record_says_what_it_references():
    """ARCH-RISK-1103 (issue #71): each domain whose exported record names other objects says so in one place, `references(record)` -> [(kind, id, field)] -- what the graph of dependencies reads, never a second reader of its fields -- and every kind it gives is one of the graph's."""
    from domains import connection, connector, dependency_graph, fire, member_check, plan, schema, steel_check
    samples = {member_check: {"position": "T001"}, steel_check: {"position": "T001", "profile": "IPE 200"},
               connector: {"position": "C1", "schema": "D1", "members": [{"position_id": "T001"}]}, connection: {"schema": "D1", "members": [{"position": "T001"}]},
               schema: {"elements": [{"id": "E1", "position": "T001"}]}, plan: {"labels": ["T001"], "section_plan": "P2", "background": {"document": "DOC"}}, fire: {"plan": "P1"}}
    for module, record in samples.items():
        found = module.references(record)
        assert found and all(kind in dependency_graph.KINDS for kind, _id, _field in found), (module.__name__, found)
        assert module.references({}) == [], module.__name__
    assert ("position", "C1", "position") not in connector.references(samples[connector]), "a connector's own position is its id, no reference"
