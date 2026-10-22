# The dependencies tab

> *Dépendances*: written on 2026-10-21 (issue #71, spec [`requirements/completed/2026-10-21-graphe-dependances.md`](../requirements/completed/2026-10-21-graphe-dependances.md), UI-001). The graph it shows is [`domain/dependencies.md`](../domain/dependencies.md) §3.3quinvicies; the window's frame is [`window.md`](window.md) §10quater.

## 10quater (suite) — dependencies tab

**The dependencies tab (v0.120, issue #71).** *Dépendances* is in group *Référence*, after *Variables*. Its module is `calc/tools/dependencies_tab.py`, with its words under `dg_` and the kinds said with the export's own words, `warn_dep_kind_<kind>`.

It shows the graph of the last export, read from `data/dependencies.json` each time the tab is shown (`on_shown`):
- **On the left**, the objects by kind (positions, loads, scripts, domains, checks…), each kind with its count, and a filter above them.
- **On the right**, for the one chosen:
  - **«Dépend de»**: the objects it reads, each with the field or the variable it reads it through, and a section's line;
  - **«Utilisé par»**: every object that depends on it, transitively, as the export's warnings count it.
  - A section whose calls name what Woodcore cannot place says how many.

The engineer chose a list over a drawing (D-05).

**Opening an object.** A double click opens the object where it is edited, through `MainWindow.open_object(node, file)`:
- A section opens in VS Code (`open_in_editor`).
- Any other object opens in the tab whose `GRAPH_KIND` is its kind and which lists it (`SourceEditorTab.lists_object`, `graph_id`). The draft open there is left as choosing another row leaves it (`open_object`, `confirm_leave`). The plans open by `open_plan`.
- A case read from a workbook has no tab, and the status bar says so.

**A browser, like «Variables».** It writes nothing and has no `dirty`, so it defines no method `tab_guard.WRITERS` names (`tests/test_dependency_tab.py`). A banner says:
- when the graph has not been exported yet (`dg_not_exported`);
- when it is older than the last change of one of its objects' sources (`dependency_graph.newer_sources`, by the time of the files the nodes name). The next export draws it again.
