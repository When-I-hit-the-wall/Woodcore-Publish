"""The graph of dependencies of a project (spec docs/requirements/completed/2026-10-21-graphe-dependances.md, issue #71; calc/domains/dependency_graph.py).

What is held, on a copy of the example project with its documents, its domains and its plans' documents, exported as the window's «Import données» exports it:

* **the graph**: every reference the example holds is an edge -- a check's and a steel check's position, a schema's elements, a plan's labels, a polar moment's and a connector's schema, a fire plan's plan, a section's plans and loads --; an unfolded check is no domain of «Formules» and makes no circle (ARCH-RISK-1101); the renumbering's stores are edges of the graph;
* **the file**: `data/dependencies.json` valid against its contract, the same bytes from one export to the next, seeded empty in a new project;
* **what changed**: nothing said on an export with no change, nor without a previous graph or with an unreadable one; a position changed is said with what depends on it, the checks it moves too not said as roots of their own;
* **the reading of a section**: a call in a comment names nothing, an argument the section computes is the wildcard, a name Python cannot place is counted;
* **circles** through objects of different kinds -- a load, a domain of «Formules» and the load again; a script reading a connector that follows it, in the last export -- said, a circle of one kind left to its owner;
* **the table of commands**: every public command of lib/ either names objects (`COMMAND_REFERENCES`) or names none (`NO_REFERENCE`).
"""

import json
import shutil

import conftest
from conftest import ROOT

import project
from domains import dependency_graph as dg

_STATE = {}


def _copy(name):
    """A copy of the example project an export runs on whole: its documents, its domains, its configuration and its plans' documents, which project_copy leaves out."""
    here = conftest.project_copy(name)
    real = project.current()
    folders = [real.formulas_dir, real.config_dir] + [real.document_dir(mode) for mode in real.modes]
    if real.has_folders:
        folders += [real.domain_dir(kind) for kind in project.DOMAIN_FOLDERS]
    for folder in folders:
        if folder is not None and folder.is_dir() and folder.resolve() != real.root.resolve():
            shutil.copytree(folder, here.root / folder.relative_to(real.root), dirs_exist_ok=True)
    for folder in real.root.iterdir():
        if folder.is_dir() and folder.name.startswith("01_"):
            shutil.copytree(folder, here.root / folder.name, dirs_exist_ok=True)
    return here


def _export(here, notes=None):
    import export_all
    real = export_all._warn
    if notes is not None:
        export_all._warn = notes.append
    try:
        with project.using(here):
            export_all.run()
    finally:
        export_all._warn = real
    return json.loads((here.data_dir / dg.EXPORT_FILE).read_text(encoding="utf-8"))


def _exported():
    if "here" not in _STATE:
        here = _copy("dependency_graph")
        _STATE["first"] = _export(here)
        _STATE["bytes"] = (here.data_dir / dg.EXPORT_FILE).read_bytes()
        _STATE["here"] = here
    return _STATE["here"], _STATE["first"]


def _edges(graph):
    return {(e["from"], e["to"]) for e in graph["edges"]}


def test_the_example_project_s_references_are_edges_of_its_graph():
    here, graph = _exported()
    edges = _edges(graph)
    checks = json.loads((here.data_dir / "checks.json").read_text(encoding="utf-8"))["checks"]
    for cid, record in checks.items():
        if record.get("position") and f"position:{record['position']}" in graph["nodes"]:
            assert (f"check:{cid}", f"position:{record['position']}") in edges, cid
    plans = json.loads((here.data_dir / "plans.json").read_text(encoding="utf-8"))["plans"]
    for pid, record in plans.items():
        for label in record.get("labels") or ():
            assert (f"plan:{pid}", f"position:{label}") in edges, (pid, label)
    for kind, file, field in (("connection", "connections.json", "connections"), ("connector", "connectors.json", "connectors")):
        for cid, record in json.loads((here.data_dir / file).read_text(encoding="utf-8"))[field].items():
            if record.get("schema"):
                assert (f"{kind}:{cid}", f"schema:{record['schema']}") in edges, cid
    for fid, record in json.loads((here.data_dir / "fire.json").read_text(encoding="utf-8"))["plans"].items():
        if record.get("plan"):
            assert (f"fire:{fid}", f"plan:{record['plan']}") in edges
    assert ("section:rs/Sections/002-grundlagen.typ", "plan:Velo-Unterstand") in edges, "a section's show-plan is an edge"
    assert any(e["from"].startswith("section:") and e["to"].startswith("load:") for e in graph["edges"]), "a section's show-calc is an edge"
    # an unfolded check is its own file, never a domain of «Formules», and makes no circle (ARCH-RISK-1101)
    unfolded = [cid for cid, record in checks.items() if record.get("file")]
    assert unfolded and not any(f"formula:{cid}" in graph["nodes"] for cid in unfolded), unfolded
    assert dg.cycles(graph) == []
    # every target is an object of the project, or every one of a kind
    assert all(e["to"] in graph["nodes"] or e["to"].endswith(":*") for e in graph["edges"])


def test_the_renumbering_s_stores_are_edges_of_the_graph():
    """ARCH-RISK-1103: what the renumbering rewrites when a position is renamed -- a plan's labels, a check's position, a schema element's -- the graph knows as an edge to that position."""
    here, graph = _exported()
    position_edges = {e["from"].split(":", 1)[0] for e in graph["edges"] if e["to"].startswith("position:")}
    assert {"plan", "check", "schema"} <= position_edges, position_edges


def test_the_file_is_valid_the_same_bytes_from_one_export_to_the_next_and_seeded_empty():
    import validation
    here, graph = _exported()
    validation.validate_structure(graph, dg.EXPORT_SCHEMA)
    notes = []
    second = _export(here, notes)
    assert (here.data_dir / dg.EXPORT_FILE).read_bytes() == _STATE["bytes"], "an export with no change wrote another graph"
    assert second == graph
    assert not [n for n in notes if getattr(n, "code", "").startswith("dep_")], "an export with no change said something changed"
    assert dg.empty() == {"schema_version": "1.0", "nodes": {}, "edges": []}
    validation.validate_structure(dg.empty(), dg.EXPORT_SCHEMA)


def test_without_a_previous_graph_or_with_an_unreadable_one_nothing_is_said_changed():
    _here, graph = _exported()
    assert dg.changes(None, graph) == [] and dg.notes(None, graph) == []
    path = conftest.tmpdir("dep_unreadable") / dg.EXPORT_FILE
    path.write_text("{not json", encoding="utf-8")
    assert dg.read(path) is None
    path.write_text(json.dumps({"schema_version": "9.0", "nodes": {}, "edges": []}), encoding="utf-8")
    assert dg.read(path) is None, "a graph of another version is not compared"


def test_a_position_changed_is_said_with_what_depends_on_it_and_the_cascade_is_not():
    """D-04: the position is the root; the checks its change moves are listed under it, never as roots of their own."""
    import positions_store
    here, graph = _exported()
    with project.using(here):
        rows = positions_store.read(here)
        target = next(row for row in rows if any(e["to"] == "position:" + row["position"] and e["from"].startswith("check:") for e in graph["edges"]))
        target["strength_class"] = "C30" if target.get("strength_class") != "C30" else "C24"   # a value its checks follow: they move too (the cascade)
        positions_store.write(here, rows)
    notes = []
    after = _export(here, notes)
    changed = [n for n in notes if getattr(n, "code", "") == "dep_changed"]
    roots = {n.args["node"] for n in changed}
    assert roots == {"position:" + target["position"]}, roots
    assert any(n.args["kind"].code == "dep_kind_check" and any(e["from"].split(":", 1)[1] in n.args["ids"] for e in graph["edges"] if e["to"] == "position:" + target["position"] and e["from"].startswith("check:")) for n in changed), changed
    assert dg.changes(graph, after)[0][0] == "position:" + target["position"]
    _STATE.pop("here")   # the copy changed: the next test exports a fresh one


def test_a_section_s_calls_are_read_outside_its_comments():
    graph = dg._Graph({"snow-load"})
    graph.node("section:rs/x.typ")
    text = ('// #include domain-file("snow-load", "OLD")\n'
            '#include domain-file("snow-load", "SL")\n'
            '#for id in ids("position") [ #position(id) ]\n'
            '#var("x", domain: "S10 - 0.55 kN Ende")\n'
            '#include domain-file("check", "ZT-01")\n'
            '/* #image-positions-plan("Gone") */ #image-positions-plan("P1")\n')
    dg._section_calls(graph, "section:rs/x.typ", text, set(), set(), None)
    edges = {(e["to"], e["field"]) for e in graph.edges}
    assert ("load:snow-load/SL", "domain-file") in edges and not any("OLD" in to or "Gone" in to for to, _f in edges), edges
    assert ("check:ZT-01", "domain-file") in edges, "a domain's file included is the object it prints (spec 2026-10-21-commandes-typst-refonte, REQ-017)"
    assert ("position:*", "ids") in edges and ("position:*", "position") in edges, edges
    assert ("plan:P1", "image-positions-plan") in edges
    assert graph.nodes["section:rs/x.typ"]["unresolved"] == 1, "a document's own registry name is counted, not dropped"


def test_a_circle_through_objects_of_different_kinds_is_said():
    graph = {"schema_version": "1.0", "nodes": {k: {} for k in ("load:snow-load/A", "formula:f", "script:s", "connector:c", "load:snow-load/B")},
             "edges": [{"from": "load:snow-load/A", "to": "formula:f", "field": "/links/h_0"},
                       {"from": "formula:f", "to": "load:snow-load/A", "field": "var"},
                       {"from": "script:s", "to": "connector:c", "field": "value", "previous": True},
                       {"from": "connector:c", "to": "script:s", "field": "/links/d"},
                       {"from": "load:snow-load/B", "to": "load:snow-load/B", "field": "/links/h_0"}]}
    found = dg.cycles(graph)
    assert found == [["connector:c", "script:s", "connector:c"], ["formula:f", "load:snow-load/A", "formula:f"]], found
    assert [n.code for n in dg.notes(None, graph)] == ["dep_cycle", "dep_cycle"]


def test_every_public_command_of_lib_is_classified():
    """ARCH-RISK-1104: a command that names an object of the project is in COMMAND_REFERENCES, one that names none in NO_REFERENCE -- a new command is classified, or this fails naming it."""
    import build_reference_lib
    public = {r["name"] for r in build_reference_lib.lib_bindings(ROOT) if r["kind"] == "function" and r["category"] != "internal" and r["doc_lines"]}
    unclassified = sorted(public - set(dg.COMMAND_REFERENCES) - dg.NO_REFERENCE)
    stale = sorted((set(dg.COMMAND_REFERENCES) | dg.NO_REFERENCE) - public)
    assert not unclassified, "public commands neither in COMMAND_REFERENCES nor in NO_REFERENCE: %s" % unclassified
    assert not stale, "classified, and no public command of lib/: %s" % stale
    assert not set(dg.COMMAND_REFERENCES) & dg.NO_REFERENCE


# --- every kind of reference, on objects the example project does not hold (REQ-001) --------------------------

def _synthetic(here):
    """A project of one of each reference the example does not carry: a check following a load's variable, a static model whose load is a load's value, a plan on a document with a section plan, a domain of «Formules» reading a load, a script that read a connector, a load following that domain, an excerpt -- built by `build` as the export builds it."""
    import engine
    from domains import formula_domain
    for folder in (here.checks_dir, here.statics_dir):
        folder.mkdir(parents=True, exist_ok=True)
    engine.write_json(here.checks_dir / "ZZ-01.json", {"id": "ZZ-01", "links": {"N": {"domain": "snow-load", "instance": "SL", "var": "q_k1", "factor": 1.5}}})
    engine.write_json(here.statics_dir / "M1.json", {"id": "M1", "loads": [{"id": "q1", "magnitude": {"domain": "wind-load", "instance": "WL", "var": "qk_max_cf1"}}],
                                                     "texts": [{"id": "t1", "text": "{1}", "vars": {"1": {"domain": "snow-load", "instance": "SL", "var": "s_k", "show": "value"}}}]})
    here.formulas_dir.mkdir(parents=True, exist_ok=True)
    (here.formulas_dir / "F1.typ").write_text('#import "/000-Typst-Config/commands.typ": *\n#var-domain("F1", title: "F1")[\n  #var("s_k", var-of("snow-load", "SL", "s_k"))\n  #var("x", 2, "m")\n]\n', encoding="utf-8", newline="\n")
    formulas = [d for d in formula_domain.list_domains(here) if d.id == "F1"]
    calculations = {"domains": {"snow-load": {"instances": {"SL": {"vars": {"s_k": {"value": 1.0}}, "links": {"h_0": {"variable": {"domain": "F1", "instance": "F1", "var": "x", "origin": "formulas"}}}}}},
                                "wind-load": {"instances": {"WL": {"vars": {}}}}}}
    return dict(
        calculations=calculations, positions={"T001": {"position": "T001"}}, scripts={"S1": {"id": "S1", "vars": {"r": {"value": 1}}}},
        reads={"S1": [["connector", "C1", "R_d"], ["snow-load", "SL", "s_k"]]}, formulas=formulas,
        checks={"checks": {"ZZ-01": {"position": "T001", "kind": "tension"}}}, steel={"checks": {}},
        connectors={"connectors": {"C1": {"position": "C1", "schema": "D1", "members": [{"position_id": "T001"}]}}},
        connections={"connections": {}}, schemas={"schemas": {"D1": {"elements": [{"id": "E1", "position": "T001"}]}}},
        plans={"plans": {"P1": {"labels": ["T001"], "section_plan": "P2", "background": {"document": "DOC1"}}, "P2": {"labels": []}}},
        fire_plans={"plans": {"B1": {"plan": "P1"}}}, models={"models": {"M1": {}}}, annexes={"excerpts": {"X1": {"page": 1}}})


def test_every_kind_of_reference_is_an_edge():
    """REQ-001: each reader -- a record's references, a source's links, a static model's magnitude and text, a domain's var-of, a script's reads, a load's links -- gives its edge."""
    here = conftest.project_copy("dependency_kinds")
    with project.using(here):
        graph = dg.build(here, **_synthetic(here))
    edges = {(e["from"], e["to"], e.get("variable")) for e in graph["edges"]}
    expected = {
        ("check:ZZ-01", "position:T001", None), ("check:ZZ-01", "load:snow-load/SL", "snow-load/SL/q_k1"),
        ("statics:M1", "load:wind-load/WL", "wind-load/WL/qk_max_cf1"), ("statics:M1", "load:snow-load/SL", "snow-load/SL/s_k"),
        ("formula:F1", "load:snow-load/SL", "snow-load/SL/s_k"), ("load:snow-load/SL", "formula:F1", "F1/F1/x"),
        ("script:S1", "connector:C1", "connector/C1/R_d"), ("script:S1", "load:snow-load/SL", "snow-load/SL/s_k"),
        ("connector:C1", "schema:D1", None), ("connector:C1", "position:T001", None), ("schema:D1", "position:T001", None),
        ("plan:P1", "position:T001", None), ("plan:P1", "plan:P2", None), ("plan:P1", "document:DOC1", None), ("fire:B1", "plan:P1", None),
    }
    assert expected <= edges, sorted(expected - edges)
    assert next(e for e in graph["edges"] if e["from"] == "script:S1" and e["to"] == "connector:C1").get("previous") is True
    assert "extract:X1" in graph["nodes"] and "document:DOC1" in graph["nodes"]
    # an object added that names another adds an edge
    with project.using(here):
        more = _synthetic(here)
        more["checks"]["checks"]["ZZ-02"] = {"position": "T001"}
        again = dg.build(here, **more)
    assert ("check:ZZ-02", "position:T001") in {(e["from"], e["to"]) for e in again["edges"]}
    # the load → «Formules» → load circle, said by the notes the export prints, naming the chain
    said = [n for n in dg.notes(None, graph) if n.code == "dep_cycle"]
    assert [n.args["chain"] for n in said] == ["formula:F1 → load:snow-load/SL → formula:F1"], [n.args for n in said]


def test_a_script_s_reads_are_recorded_as_it_runs():
    """ARCH-RISK-1105: what a script's value() reads is handed to the graph, and data/scripts.json does not carry it."""
    from domains import script as script_domain
    here = conftest.project_copy("dependency_reads")
    with project.using(here):
        folder = script_domain.sources_dir(here)
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "lit.py").write_text('# @name lit\ntry:\n    q = value("snow-load", "SL", "q_k1")\nexcept KeyError:\n    q = 0\nresult("q", q, "kN/m²")\n', encoding="utf-8", newline="\n")
        reads = {}
        records, _notes = script_domain.prepare(reads=reads)
    assert reads.get("lit") == [["snow-load", "SL", "q_k1"]], reads
    assert "reads" not in json.dumps(records["lit"])


def test_the_module_imports_no_qt():
    source = (ROOT / "calc" / "domains" / "dependency_graph.py").read_text(encoding="utf-8")
    assert "PySide" not in source and "Qt" not in source.replace("Qt-free", "")
