# Prototype of the Variables tab, second version (24.10.2026)

The HTML prototype the engineer reviewed on 24.10.2026 and validated in its second version (proposal A: the tabs' menu on the left, the filter as tags in the search bar, the list always grouped by domain, the choice «comme dans Windows», the card that opens the tab where the value is computed), the reference of issue #114 and of the spec `docs/requirements/completed/2026-10-24-onglet-variables-groupes.md`. Copied from the artifact «Onglet Variables» (https://claude.ai/artifact/UttxP9bbAfnSNesFHVTMEj, version 1792846581-121c) on 25.10.2026. Nothing in Woodcore reads this folder: what was decided lives in `calc/variable_calc.py`, `calc/variable_query.py`, `calc/variable_select.py`, `calc/variable_card.py` and the tab's modules under `calc/tools/` (`variables_*.py`, `tag_search_bar.py`, `tree_menu.py`).

Open `index.html` in a browser, from this folder: it needs the images beside it and nothing else. Its script (`inScope`, `match`, `ordered`, `printed`, `siblings`, `origin`, `cmdOf`, `pick`) was the model of the behaviour, not code delivered; its navigation (`NAV`, `TABNAME`) is written by hand there and is read from `tab_registry` in Woodcore.

| File | What it is |
|---|---|
| `index.html` | The page: the tab's mock-up in French with the example project's domains (`DATA.doms`), its script, and the reading column that compares it with the tab of Woodcore 0.125. |
| `img/03-variable.jpg`, `img/04-all-search.jpg`, `img/05-display.jpg` | The tab of Woodcore 0.125 as it was before the issue: a variable chosen, a search over every domain, the «Affichage» view. |
| `img/res-1.png` … `img/res-4.png` | The four ways a result was marked in the list that the engineer compared; the second (a thin frame in the accent colour) is the one kept (D-6). |

## Measures (25.10.2026, master `209b965`, `tests/projet-exemple`)

Read with the three documents compiled (`variables.best`, cu, bp, rs) and the export (`variable_sources.read_export`):

| | Variables | Domains |
|---|---|---|
| Everything, the documents' root domains included (the issue's 935/78) | 935 | 78 |
| Without the three root domains (`variables.REPORT_DOMAIN`, REQ-005) | 918 | 75 |
| The export and the files alone (`data/`) | 723 | 61 |

The report's registry declares 14 named domains; four of them (`S10 - 0.55 kN Ende`, `S10 - 1 kN Mitte`, `S10 Duo - 0.55 kN Ende`, `S10 Duo - 1 kN Mitte`) are declared by the report itself and have no calculation in `domain-files.json`; the ten others (`SL`, `H`, `SD-10`, `VU-MP-1`, the three `EL+AL-…`, the three `WL-…`) do.
