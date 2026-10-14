# archive/rfem/ — the RFEM import (v0.98 – v0.116, retired in 0.117)

Woodcore read RFEM 6's own table export (*Fichier → Exporter → Tableaux*, one `.xlsx` or a folder of `.csv`): the nodes, members, sections, supports, hinges, load cases and loads, and in each object's comment the `@position`, `@model` and `@load` the engineer typed there. From it, it made **structures** (connected groups of members), **static models** generated at every export into `data/statics.json` (never into `Woodcore-Datei/statics/`), the **`rfem` domain** of `data/rfem.json` carrying the extremes RFEM's own result combinations reach, and an internal-force **diagram** a model's view could ask for. The report printed them with `#rfem-max`, `#show-rfem-forces`, `#show-rfem-combination` and read them with `rfem-ids`, `rfem-bars`, `rfem-situations`; `woodcore-cli import` read the exports from a terminal.

**Retired on the engineer's request of 08.10.2026** («Je ne les utiliserai plus, mais laisse-les dans les archives au cas où on en a besoin»), specification `docs/requirements/…/2026-10-08-onglet-formule-domaines.md` (REQ-001, D-07, D-14). The last commit that carries all of it in the program is **`b462466`** (`git show b462466:calc/tools/rfem_tab.py`); every file here was moved with `git mv`, so `git log --follow archive/rfem/<path>` gives its whole history.

## What is here (each at the path it had)

- `calc/tools/rfem_tab.py` — the tab: models on the left, structures and figures, `rf_` words in three languages.
- `calc/rfem_import/` — the eleven modules of the reader: tables (`csv_tables`, `model_tables`), comments (`metadata_parser`), structures (`structure_detection`), results and extremes (`results`, `envelopes`), diagrams (`diagram_curve`, `diagram_svg`), the import's own JSON (`json_export`, `validation`) and `import_controller`, the entry point `export_all` called.
- `calc/domains/rfem.py` — the `rfem` domain; `calc/domains/statics_view.py` — how an imported model was presented (`Woodcore-Datei/statics/views/<id>.json`).
- `lib/rfem.typ` — the three commands that printed RFEM's results.
- `schemas/rfem.schema.json`, `schemas/rfem-import.schema.json`, `schemas/statics-view.schema.json`.
- `docs/domain/rfem.md` — §3.3duodecies and §3.3quindecies, as they stood.
- `tests/` — `test_rfem_*.py` (8 files), `test_metadata_parser.py`, `test_model_tables.py`, `test_structure_detection.py`, `test_statics_view.py`, and the fixtures `tests/fixtures/rfem_csv.py`, `rfem_model.py`; `tests/projet-exemple/RFEM-Export/Beispiel-Modell.xlsx`, the example project's small export.

## What the removal changed in files that stayed — to undo, to bring it back

- `calc/project.py`: `rfem_export` left `MODE_KEYS` and `LAYOUT_ORDER` (seven keys → six); `RFEM_EXPORT_FOLDER`, `Project.rfem_models`, `rfem_model_paths`, `rfem_export_dir`, `set_rfem_models` and the `ENGINE_FILES` line of `lib/rfem.typ` went; `RETIRED_KEYS` and `Project.retired_keys()` came, which say the two keys are ignored.
- `calc/export_all.py`: the call of `rfem.prepare`, the validation and the writing of `data/rfem.json`, `rfem.write`, and `rfem.json` in `seed()` went; `_sweep_retired` removes `data/rfem*`.
- `calc/domains/statics.py`: `prepare(…, generated=)` and `export(…, generated=)` and the `diagram` of a record went; `schemas/statics.schema.json` and `statics-source.schema.json` lost their `diagram`.
- `lib/calc-engine.typ`: `rfem-domain`, `load-rfem`, `rfem-ids`, `rfem-bars`, `rfem-situations`, the `rfem` branches of `instance-ids`, `find-calculation` and `resolve-source`, and `show-static-model(diagram:)` went; `lib/formula.typ` no longer imports `rfem.typ`.
- `calc/tools/build_reference.py`: `rfem.typ` in `LIB_FILES`, the RFEM commands in `CATEGORIES`, their samples and `REQUIRED_NAMED` went; `calc/i18n/commands.json` lost the six commands' translations and `calc/i18n/strings.json` its seven `rfem.*` words; the 18 examples `examples/*rfem*` and their pictures went.
- `calc/cli.py`: the `import` sub-command and `rfem_import_command`.
- `calc/documents.py`, `calc/project_template.py`, `calc/templates.py`, `calc/tools/archive_export.py`: the `RFEM-Export/` folder is no longer made, archived, shared or left out of a template.
- `calc/project_migrate.py`: `gui.rfem_models` no longer follows its files, `RFEM-Export/` no longer moves up, and the comparison no longer allows a moved path (`path_pairs`, `replace_paths`).
- `calc/tools/woodcore_gui.py`, `chrome.py`, `display_options.py`, `display_view.py`, `statics_tab.py`: the tab, its icon, its words, and the diagram option of `show-static-model`.
- `tests/conftest.py`: `real_rfem_export`; the tests that named the tab, the folder or the keys were changed with it (`git show` the commit of the removal).
