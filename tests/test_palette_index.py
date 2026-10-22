"""What the command palette searches, read where each thing is kept (calc/palette_index.py, issue #83, docs/ui/command-palette.md) -- Qt-free.

What is held: that the module imports no Qt and nothing of calc/tools/; that a query's first character chooses its category and the letters are matched in their order, their places given back to underline them; that the entries are read at their sources each time -- a position added to positions.json found at the next build --, a timber check's η computed as its tab computes it and a steel check's read off steel.json, the tolerance the domain's; that «utilisé par» is the graph's, transitively and through a wildcard; that the Typst call of an object is read off the table of the commands that name one; that the warnings are gathered from the notices, the checks not satisfied or not calculable and the files missing or unreadable, a file that cannot be read said and never swallowed; and that no list of tabs, actions, norms or commands is written in the module.
"""

import ast
import json
import subprocess
import sys

import conftest
from conftest import CALC, ROOT

import project


def _copy(name):
    conftest.exported("checks.json")
    return conftest.project_copy(name)


def test_the_module_imports_no_qt_and_nothing_of_the_window():
    done = subprocess.run([sys.executable, "-c", "import sys; sys.path.insert(0, sys.argv[1]); import palette_index; print(sorted({m.split('.')[0] for m in sys.modules if m.startswith(('PySide6', 'woodcore_gui', 'chrome', 'tab_registry'))}))", str(CALC)],
                          capture_output=True, text=True, encoding="utf-8", cwd=str(ROOT))
    assert done.returncode == 0 and done.stdout.strip() == "[]", done.stdout + done.stderr
    tree = ast.parse((CALC / "palette_index.py").read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            assert not node.value.startswith(("tab_", "SIA ", "#show-", "Exporter")), f"palette_index writes a list of its own: {node.value!r}"


def test_a_prefix_chooses_the_category_and_letters_are_matched_in_their_order():
    import palette_index
    assert [palette_index.parse(q) for q in ("@T001", ">pdf", "#s_k", "§4.2", "!", "flex", "")] == [
        ("objects", "T001"), ("actions", "pdf"), ("variables", "s_k"), ("norms", "4.2"), ("warnings", ""), ("all", "flex"), ("all", "")]
    assert palette_index.match("flex", "Flexion") == [0, 1, 2, 3]
    assert palette_index.match("bi01", "BI-01") == [0, 1, 3, 4]
    assert palette_index.match("xz", "Flexion") is None
    entries = [palette_index.Entry("tab", "tab:a", "Flexion"), palette_index.Entry("check", "check:BI-01", "Biegung", ident="BI-01", node="check:BI-01"),
               palette_index.Entry("action", "action:pdf", "Exporter PDF")]
    assert [e.key for e, _p in palette_index.search(entries, "@bi01")] == ["check:BI-01"], "an object found by its id, in its category alone"
    assert [e.key for e, _p in palette_index.search(entries, "fl")] == ["tab:a"]
    assert [e.key for e, _p in palette_index.search(entries, ">")] == ["action:pdf"]
    assert {key for key, _prefix in palette_index.CATEGORIES} == {"all", "actions", "objects", "variables", "norms", "warnings"}


def test_the_entries_are_read_at_their_sources_each_time():
    import palette_index
    import positions_store
    here = _copy("palette_sources")
    entries, _graph = palette_index.build(here, "fr")
    positions = {e.label for e in entries if e.kind == "position"}
    assert positions == {row["position"] for row in positions_store.read(here)}
    rows = positions_store.read(here)
    positions_store.write(here, rows + [{**rows[0], "position": "T999"}])
    entries, _graph = palette_index.build(here, "fr")
    assert "T999" in {e.label for e in entries if e.kind == "position"}, "a position added was not found at the next opening"
    kinds = {e.kind for e in entries}
    assert {"position", "check", "norm", "variable", "command"} <= kinds, kinds
    commands = {e.label for e in entries if e.kind == "command"}
    assert commands == {"#" + name for name in json.loads((CALC / "i18n" / "commands.json").read_text(encoding="utf-8"))["commands"]}


def test_a_check_s_eta_is_its_tab_s_and_a_steel_check_s_its_file_s():
    import palette_index
    from domains import member_check
    here = _copy("palette_eta")
    data = json.loads((here.data_dir / member_check.EXPORT_FILE).read_text(encoding="utf-8"))
    etas = palette_index.utilisations(here)
    for ident, record in data["checks"].items():
        if record.get("calculable"):
            result = member_check.compute(record)
            assert etas[ident][:2] == (result["eta"], result["ok"]), ident
    steel = json.loads((here.data_dir / "steel.json").read_text(encoding="utf-8"))["checks"]
    for ident, record in steel.items():
        if isinstance(record.get("eta"), (int, float)):
            assert etas[ident][:2] == (record["eta"], record["ok"]), ident
    entries, _graph = palette_index.build(here, "fr")
    checks = {e.label if not e.ident else e.ident: e for e in entries if e.kind == "check"}
    assert all(checks[ident].eta == etas[ident][0] for ident in etas if ident in checks)


def test_used_by_is_the_graph_s_transitively_and_the_summary_counts_the_checks():
    import palette_index
    graph = {"schema_version": "1.0", "nodes": {"position:T001": {}, "position:T002": {}, "check:BI-01": {}, "plan:P01": {}, "section:rs/Sections/a.typ": {}},
             "edges": [{"from": "check:BI-01", "to": "position:T001", "field": "position"}, {"from": "plan:P01", "to": "position:*", "field": "labels"},
                       {"from": "section:rs/Sections/a.typ", "to": "check:BI-01", "field": "domain-file"}]}
    found = palette_index.used_by(graph, "position:T001")
    assert found == ["check:BI-01", "plan:P01", "section:rs/Sections/a.typ"], found
    summary = palette_index.summary(graph, "position:T001", {"BI-01": (0.91, True, [])})
    assert summary["count"] == {"check": 1, "plan": 1, "section": 1} and summary["eta_max"] == 0.91
    assert palette_index.used_by(None, "position:T001") == []


def test_the_typst_call_of_an_object_is_the_command_that_prints_it():
    import palette_index
    assert palette_index.typst_call("position:T001") == '#position("T001")'
    assert palette_index.typst_call("plan:P01") == '#image-positions-plan("P01")'
    assert palette_index.typst_call("check:BI-01") == '#include domain-file("check", "BI-01")'
    assert palette_index.typst_call("profile:X") == ""


def test_the_warnings_gather_their_four_sources_and_an_unreadable_file_is_said():
    import notifications
    import palette_index
    from domains import member_check
    here = _copy("palette_warnings")
    path = here.data_dir / member_check.EXPORT_FILE
    data = json.loads(path.read_text(encoding="utf-8"))
    ident, record = next((k, r) for k, r in data["checks"].items() if r.get("calculable"))
    record["N"] = (record.get("N") or 1) * 1e4 if isinstance(record.get("N"), (int, float)) and record.get("N") else record.get("N")
    record["warnings"] = ["a warning of the check"]
    other, refused = next((k, r) for k, r in data["checks"].items() if k != ident)
    refused["calculable"], refused["reason"] = False, "no section"
    path.write_text(json.dumps(data), encoding="utf-8")
    notifications.STORE.add(notifications.Notice("palette_probe", notifications.WARNING, "a notice of the window"))
    try:
        entries, _graph = palette_index.build(here, "fr")
        warnings = [e for e in entries if e.kind == "warning"]
        sources = {(e.extra or {}).get("source") for e in warnings}
        assert {"notice", "check", "reason"} <= sources, sources
        assert any(e.key == f"check-warning:{ident}:0" and e.node.endswith(ident) for e in warnings)
        assert any(e.key == f"reason:{other}" and e.detail == "no section" for e in warnings)
        etas = palette_index.utilisations(here)
        for name, (eta, ok, _clauses) in etas.items():
            assert ok == (eta <= 1 + palette_index.ETA_TOLERANCE) or name not in data["checks"], name
            assert any(e.key == f"eta:{name}" for e in warnings) == (not ok), name
        path.write_text("{ not json", encoding="utf-8")
        entries, _graph = palette_index.build(here, "fr")
        assert any(e.key.startswith("unreadable:") for e in entries if e.kind == "warning"), "a file that cannot be read was swallowed"
    finally:
        for notice in notifications.STORE.items():
            if notice.code == "palette_probe":
                notifications.STORE.remove(notice.id)


def test_a_check_above_one_is_a_warning_and_used_by_reads_the_project_s_own_graph():
    """REQ-006, REQ-007 on the project's own files: a steel check of η 1.2 is among the warnings, opening its check; and a graph written into data/ gives a position its checks and plans, the summary their count and the largest η."""
    import palette_index
    from domains import dependency_graph
    here = _copy("palette_real")
    path = here.data_dir / "steel.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    ident, record = next(iter(data["checks"].items()))
    record["eta"], record["ok"] = 1.2, False
    path.write_text(json.dumps(data), encoding="utf-8")
    entries, _graph = palette_index.build(here, "fr")
    warning = next((e for e in entries if e.key == f"eta:{ident}"), None)
    assert warning is not None and warning.eta == 1.2 and warning.node == f"steel:{ident}", [e.key for e in entries if e.kind == "warning"]
    checks = json.loads((here.data_dir / "checks.json").read_text(encoding="utf-8"))["checks"]
    position = next(r["position"] for r in checks.values() if r.get("position") and r.get("calculable"))
    users = [k for k, r in checks.items() if r.get("position") == position]
    graph = {"schema_version": "1.0", "nodes": {f"position:{position}": {}, "plan:P01": {}, **{f"check:{k}": {} for k in users}},
             "edges": [{"from": f"check:{k}", "to": f"position:{position}", "field": "position"} for k in users] + [{"from": "plan:P01", "to": "position:*", "field": "labels"}]}
    dependency_graph.write(graph, here.data_dir)
    entries, graph_read = palette_index.build(here, "fr")
    assert graph_read is not None
    found = palette_index.used_by(graph_read, f"position:{position}")
    assert found == sorted(dependency_graph.reachable(dependency_graph.downstream(graph_read), f"position:{position}"), key=found.index)
    assert set(found) == {f"check:{k}" for k in users} | {"plan:P01"}
    etas = palette_index.utilisations(here)
    summary = palette_index.summary(graph_read, f"position:{position}", etas)
    assert summary["count"]["check"] == len(users) and summary["eta_max"] == max(etas[k][0] for k in users if k in etas)
