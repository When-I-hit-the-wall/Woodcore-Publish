# archive/formules-dsl/ — the «Formules» tab of keyword lines (v0.100 – v0.116, retired in 0.117)

v0.100's «Formules» tab let the engineer write a member's checks in keyword lines — a grammar of 26 keywords and 8 checks (`calc/dsl.py`) — and turned them into `#member` and `#verify-*` calls, shown coloured beside the page they compile to, with *Copier le Typst* and *Insérer dans une section…*. The commands it wrote are **not** retired: `#member` and every `#verify-*` stay in `lib/timber.typ`, written by hand and by the member checks saved in Woodcore.

**Retired on the engineer's request of 08.10.2026** («Tu peux supprimer les onglets RFEM ainsi que Formule … laisse-les dans les archives au cas où on en a besoin»). Its place in *Référence* is taken by the new **«Formule»** tab, of a different behaviour altogether: calculation domains written as blocks of `var`, `eq`, `verify`, `val` (specification `docs/requirements/…/2026-10-08-onglet-formule-domaines.md`, REQ-002). The last commit that carries it in the program is **`b462466`**; the files were moved with `git mv`.

## What is here (each at the path it had)

- `calc/dsl.py` — the grammar and the Typst it writes.
- `calc/tools/dsl_tab.py` — the tab, its `dsl_` words in three languages.
- `tests/test_dsl.py` — its nine tests.

## What the removal changed in files that stayed

- `calc/tools/woodcore_gui.py`: the import of `dsl_tab`, the merge of its `dsl_` words, `("tab_dsl", dsl_tab.DslTab)` in `TABS`, and `tab_dsl` in `NAV_GROUPS["nav_reference"]`; `calc/tools/chrome.py`: the icon `tab_dsl`.
- `tests/test_modes_window.py`: `test_the_formulas_are_inserted_into_the_document_s_own_sections`, which held that the tab inserted into the shown document's own `Sections/`.
- `docs/domain/member-checks.md`: §3.3septdecies, now a pointer to this folder.
