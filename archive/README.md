# archive/ — features retired from Woodcore

What is here was part of Woodcore and was taken out of it on the engineer's request, kept so that it can be read or brought back if it is ever needed again. **Nothing here is part of the program**: no module of `calc/`, `lib/`, `schemas/` or `tests/` imports it, `tests/run_tests.py` does not collect it (it globs `tests/test_*.py` only, and `conftest.py` here tells a `pytest` run from the repository's root to skip the whole folder), the installer does not carry it (`packaging/woodcore.spec` takes `calc/`, `lib/`, `schemas/`, `examples/`, `templates/`, `legal/` by name) and the website does not read it (`.github/workflows/site.yml` ignores a push that changes only this folder).

Each feature has a folder of its own, and inside it **every file keeps the path it had in the repository** (`archive/rfem/calc/rfem_import/csv_tables.py` was `calc/rfem_import/csv_tables.py`), so that bringing a feature back is a `git mv` of each file to the path it shows, followed by the edits its own README lists — the lines the removal took out of files that stayed. The files were moved with `git mv`, so `git log --follow` gives each one's whole history.

| Folder | What it was | Retired in | Why |
|---|---|---|---|
| [`rfem/`](rfem/README.md) | The RFEM tab and everything only it used: the reader of RFEM's table export, the `rfem` domain, `#rfem-max`, `#show-rfem-forces`, `#show-rfem-combination`, `woodcore-cli import`, the static models generated from RFEM | 0.117 | The engineer, 08.10.2026: «Je ne les utiliserai plus, mais laisse-les dans les archives au cas où on en a besoin.» |
| [`formules-dsl/`](formules-dsl/README.md) | The «Formules» tab of v0.100: a member's checks written in keyword lines, translated into `#member` and `#verify-*` calls | 0.117 | The same request; its place in *Référence* is taken by the new *Formule* tab, which writes calculation domains |

The specification of the removal is `docs/requirements/completed/2026-10-08-onglet-formule-domaines.md`, and the decision with its price is in `docs/decisions.md` (grep «Retrait de RFEM»).
