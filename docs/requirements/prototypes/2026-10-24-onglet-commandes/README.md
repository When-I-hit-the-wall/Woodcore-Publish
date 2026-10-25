# Prototype of the commands tab, second version (24.10.2026)

The HTML prototype the engineer reviewed on 23 and 24.10.2026 and validated in its last version («Bulle des valeurs avec rendus»), the reference of issue #115 and of the spec `docs/requirements/completed/2026-10-24-onglet-commandes-pages.md`. Copied from the artifact «Commandes, deuxième version» (https://claude.ai/artifact/53bQzucT1kFNszSNoJQTaF, version 1792850975-e660) on 25.10.2026; the first version, which compared proposals and had an «Affichage» view, is the artifact https://claude.ai/artifact/EFiWSDrmygWoEVAQxS4Khg and is not copied. Nothing in Woodcore reads this folder: what was decided lives in `calc/i18n/command-pages.json`, `calc/tools/command_page.py` and the tab.

Open `index.html` in a browser, from this folder: it needs the files beside it and nothing else. Only the category «Calculer dans le rapport» is worked out there (eight commands; `from-level` came after); the other categories are listed greyed.

| File | What it is |
|---|---|
| `index.html` | The page: the tab's mock-up in fr/de/en and its script -- `V` (the values shared by several arguments), `A` (the arguments several commands share), `CMDS` (each command's lead, key points, line, arguments with their sentences, examples and values), `GROUPS`, `CATS`, the bubbles (`argTip`, `valTip`, `preview`, `laterHide`), and two JSON blocks: `oldData` (the examples, their pages and the calls of the example project, from Woodcore 0.122) and `valsData` (each value's call, set-up, place in its sheet, `same`, `blank`). The first draft of `command-pages.json`. |
| `vals/` | The prints of the 203 values, one sheet a command and a language (24 files, 4.6 MB, 32 colours), compiled by Woodcore 0.122's engine in the examples' setting by the issue's `gen_vals.py`. |
| `ex/` | The pages of the examples, one sprite a command, as the prototype showed them. |
