# Woodcore reference documentation — index

This folder is the project's reference. It was CLAUDE.md until 2026-10-07 (v0.117), when that file reached 1.5 MB and was split by domain: every section was moved **verbatim**, and keeps its § number as a stable anchor. Code comments cite a section as `docs/<file>.md §<n>`; older texts (CHANGELOG.md, 000-Audits/) cite `CLAUDE.md §<n>` — the table at the bottom resolves either.

**Read only what the task needs.** Start from the file whose purpose matches, and `grep` the large ones (decisions, status notes) rather than reading them whole; `tests/test_docs_coherence.py` holds every file here under 100 KB but `decisions.md`, every `docs/<file>.md §<n>` to a section that exists and every file to a row of this index. Every file opens with one line saying what it covers.

Specifications of work in progress are in [`requirements/`](requirements/README.md).

## Project and conventions

| File | Sections | Covers | Size |
|---|---|---|---|
| [`project/purpose.md`](project/purpose.md) | §1, §1bis | What Woodcore is for, and why Typst + Python + JSON + Excel rather than a web app. | 2 KB |
| [`conventions/writing.md`](conventions/writing.md) | §1ter | Prose is not hard-wrapped: one paragraph is one line, in every file. | 1 KB |
| [`conventions/naming.md`](conventions/naming.md) | — | One thing, one name: what the code calls each thing the window and the report show, the names history left beside it and why they stay. | 3 KB |
| [`conventions/testing.md`](conventions/testing.md) | §11ter | tests/, how to prepare a machine and run them, pinned versions of Python, Typst and packages. | 18 KB |
| [`conventions/testing-catalogue.md`](conventions/testing-catalogue.md) | §11ter | What each test file guards: the engine, the norms, the documents, the build. | 84 KB |
| [`conventions/testing-catalogue-materials.md`](conventions/testing-catalogue-materials.md) | §11ter | What each test file of the materials guards: the library, SIA 265/1, the shipped materials, the design values, the project's copy, the «Matériaux» tab. | 6 KB |
| [`conventions/testing-catalogue-window.md`](conventions/testing-catalogue-window.md) | §11ter | What each test file of the window guards, built off-screen. | 41 KB |
| [`conventions/testing-catalogue-typst.md`](conventions/testing-catalogue-typst.md) | §11ter | What each test file of the report's Typst commands guards: the calculations written by hand and their display, the citations and the bibliography, the summaries, the timber checks, the commands' documentation. | 11 KB |
| [`conventions/testing-catalogue-guards.md`](conventions/testing-catalogue-guards.md) | §11ter | What each test file that guards the repository as a whole guards: the runner and the CI, the docs, the code's size, duplicates and line endings, the figures held to the byte. | 6 KB |
| [`conventions/testing-catalogue-domains.md`](conventions/testing-catalogue-domains.md) | §11ter | What each test file of the calculation domains of the «Domaines» tab guards, without Qt: the model, its rows, its state, what is typed. | 5 KB |
| [`conventions/build-and-release.md`](conventions/build-and-release.md) | §12 | woodcore-cli, the engine copy, archives, new projects, migration, installer, publishing, website. | 53 KB |
| [`conventions/changelog-and-commits.md`](conventions/changelog-and-commits.md) | §15 | Where the journal lives and what every commit must carry. | 2 KB |

## Architecture

| File | Sections | Covers | Size |
|---|---|---|---|
| [`architecture/principles.md`](architecture/principles.md) | §2 | The pipeline Excel -> Python -> JSON -> Typst, and the 16 design rules every change must respect. | 12 KB |
| [`architecture/data-contracts.md`](architecture/data-contracts.md) | §3, §3.0, §3.1, §3.2, §3.4, §3.6, §3.7 | JSON schemas, the position record, validation levels, the three detail levels. | 9 KB |
| [`architecture/layout.md`](architecture/layout.md) | §11 | The folders of the program, of a project, and of calc/. | 48 KB |
| [`architecture/reference-library.md`](architecture/reference-library.md) | §11bis | Norms and literature beside the program; values are read from the norm itself. | 8 KB |
| [`architecture/figure-style.md`](architecture/figure-style.md) | §3.3quaterdecies | The three factors a figure is drawn with, and an entry's own over them. | 5 KB |
| [`architecture/performance.md`](architecture/performance.md) | — | What the start, the window's build, `rebuild()` and the export cost, measured before and after each change (`tests/perf_startup.py`), and the causes found. | 6 KB |

## Domain (what Woodcore calculates and draws)

| File | Sections | Covers | Size |
|---|---|---|---|
| [`domain/calculation-domains.md`](domain/calculation-domains.md) | §3.3 | How a load is a domain whose instances are Excel sheets; tables, results, groups, headings. | 23 KB |
| [`domain/loads.md`](domain/loads.md) | §3.3bis, §3.3ter, §3.3quater, §3.3septies, §3.5, §8 | The four load domains, load combinations and why no load is linked to a position. | 28 KB |
| [`domain/positions.md`](domain/positions.md) | §7 | Positions are Woodcore's own data: type, material, section, moisture class. | 12 KB |
| [`domain/connectors.md`](domain/connectors.md) | §3.3nonies, §7bis | A connector file and its SIA 265 6.2.1 shear resistance; the descriptive keys. | 29 KB |
| [`domain/connections.md`](domain/connections.md) | §3.3quinquies | A connection drawn on a schema; geometry in Python, forces distributed in Typst. | 24 KB |
| [`domain/detail-schemas.md`](domain/detail-schemas.md) | §3.3decies | The one drawing of a connection detail, modified and consumed by connectors and polar moments. | 25 KB |
| [`domain/member-checks.md`](domain/member-checks.md) | §3.3undecies, §3.3septdecies, §3.3unvicies, §3.3unvicies-bis | #member and the verify-* commands, and checks saved in Woodcore (the keyword lines of §3.3septdecies were retired in 0.117: archive/formules-dsl/); the material of the library, a panel's resistance, the options of «Affichage» in the source (issue #112). | 49 KB |
| [`domain/position-plans.md`](domain/position-plans.md) | §3.3sexies | Plans drawn over the architect's plan: source, export, Typst, types, load symbols, superposition, sheets, the stiffness centre and the mass centre. | 36 KB |
| [`domain/fire-plans.md`](domain/fire-plans.md) | §3.3vicies | A second kind of plan on the same documents and engine. | 12 KB |
| [`domain/static-models.md`](domain/static-models.md) | §3.3octies | Static systems drawn in Woodcore and exported as figures; nothing solved. | 23 KB |
| [`domain/documents.md`](domain/documents.md) | §3.3octodecies | Structure, tags and objects, sharing and sync, imports, previews, content and layout templates. | 46 KB |
| [`domain/annexes.md`](domain/annexes.md) | §3.3undevicies | External PDFs, excerpts anchored on bookmarks, and the annexes that close a document. | 10 KB |
| [`domain/journal.md`](domain/journal.md) | §3.3terdecies | One journal per document, written by hand in Woodcore, printed by show-journal. | 12 KB |
| [`domain/scripts.md`](domain/scripts.md) | §3.3sexdecies | Python the engineer writes, run by Woodcore, whose named results the report reads. | 6 KB |
| [`domain/fire-resistance.md`](domain/fire-resistance.md) | §3.3tervicies | Member checks in the design situation fire (SIA 265 4.5.2), the fire resistance VKF 15-15 requires, and the comparison with the reference workbooks and the AEAI directives. | 10 KB |
| [`domain/steel.md`](domain/steel.md) | §3.3quatervicies | Steel profiles (SZS C5 tables, free profiles), the section class and the member checks of SIA 263:2013, computed once in Python. | 7 KB |
| [`domain/dependencies.md`](domain/dependencies.md) | §3.3quinvicies | The graph of dependencies: which object reads which, data/dependencies.json, what a change touches at the export. | 6 KB |
| [`domain/materials.md`](domain/materials.md) | §3.3sexvicies | The engineer's library of materials and the ones Woodcore ships (SIA 265, SIA 265/1, SIA 261, the workbook's), the design values deduced, the copy a project keeps, the 1.0 file poured into the library. | 9 KB |
| [`domain/variable-links.md`](domain/variable-links.md) | §3.3duovicies, §3.3duovicies-bis | A field of the window that follows a variable of the export: its shape, units, resolution, versions and what it may name; a text placed on a drawing and the variables it prints. | 14 KB |

## Typst report engine

| File | Sections | Covers | Size |
|---|---|---|---|
| [`typst/report-engine.md`](typst/report-engine.md) | §4, §5, §6, §6bis, §9 | Global level with local override, a position and the calculation that concerns it, the `get` abstraction, input descriptions. | 10 KB |
| [`typst/formulas.md`](typst/formulas.md) | §10quinquies | The registry, var-domain, val, var-line, units, verify, levels, stacked formulas. | 45 KB |
| [`typst/language.md`](typst/language.md) | §4bis | Document language vs engine language, the glossary, figures per language. | 18 KB |
| [`typst/citations.md`](typst/citations.md) | §10 | Systematic norm citations, registration and show-bibliography. | 6 KB |
| [`typst/api-conventions.md`](typst/api-conventions.md) | §10bis | /// doc comments, call shapes, one import, and the reference table of every command. | 77 KB |
| [`typst/command-docs.md`](typst/command-docs.md) | §10sexies | Every command documented and exemplified; examples frozen and pre-rendered. | 22 KB |
| [`typst/reference-workbook.md`](typst/reference-workbook.md) | §10ter | docs/typst-reference.xlsx and the call_* functions that spell every Typst call. | 8 KB |

## User interface

| File | Sections | Covers | Size |
|---|---|---|---|
| [`ui/window.md`](ui/window.md) | §10quater | The frame: the start page, the theme, the navigation, folders, panes, saving, the settings — and the index of the tabs below. | 73 KB |
| [`ui/tab-polar-moments.md`](ui/tab-polar-moments.md) | §10quater | The polar moments tab. | 7 KB |
| [`ui/tab-plans.md`](ui/tab-plans.md) | §10quater | The plan tabs: the position plan, and what it shares with the fire-protection plan. | 33 KB |
| [`ui/tab-fire-plan.md`](ui/tab-fire-plan.md) | §10quater | The fire-protection plan tab. | 4 KB |
| [`ui/tab-static-models.md`](ui/tab-static-models.md) | §10quater | The static models tab. | 18 KB |
| [`ui/tab-schemas.md`](ui/tab-schemas.md) | §10quater | The schemas tab. | 14 KB |
| [`ui/tab-structure.md`](ui/tab-structure.md) | §10quater | The «Structure du document» tab. | 14 KB |
| [`ui/tab-commands.md`](ui/tab-commands.md) | §10quater | The commands tab. | 1 KB |
| [`ui/tab-connectors.md`](ui/tab-connectors.md) | §10quater | The connectors tab. | 16 KB |
| [`ui/tab-positions.md`](ui/tab-positions.md) | §10quater | The positions tab, and the list of the positions. | 9 KB |
| [`ui/tab-journal.md`](ui/tab-journal.md) | §10quater | The journal tab. | 2 KB |
| [`ui/tab-annexes.md`](ui/tab-annexes.md) | §10quater | The annexes tab. | 3 KB |
| [`ui/tab-member-checks.md`](ui/tab-member-checks.md) | §10quater | The member checks tabs: Traction, Compression, Flexion, Cisaillement on the type «Calcul» (issue #112). | 9 KB |
| [`ui/tab-fire-resistance.md`](ui/tab-fire-resistance.md) | §10quater | The «Résistance au feu» tab. | 4 KB |
| [`ui/tab-steel.md`](ui/tab-steel.md) | §10quater | The «Acier» tabs: profiles, section class, tension, compression, bending, shear. | 4 KB |
| [`ui/tab-python.md`](ui/tab-python.md) | §10quater | The Python tab. | 2 KB |
| [`ui/tab-formulas.md`](ui/tab-formulas.md) | §10quater | The «Domaines» tab (formerly «Formules»): Formulaire, Code, Affichage on a domain's file, its modules (issue #113). | 15 KB |
| [`ui/tab-variables.md`](ui/tab-variables.md) | §10quater | The variables tab. | 16 KB |
| [`ui/tab-dependencies.md`](ui/tab-dependencies.md) | §10quater | The dependencies tab: the graph of the project's objects, «dépend de» and «utilisé par». | 2 KB |
| [`ui/tab-project.md`](ui/tab-project.md) | §10quater | The «Projet» tab: the title page, the language, the form, the documents made one by one and their content templates, the preview of the templates. | 8 KB |
| [`ui/command-palette.md`](ui/command-palette.md) | §10quater | The command palette, Ctrl+K: what it finds, where it reads it, and how it is used with the mouse. | 6 KB |
| [`ui/building-a-tab.md`](ui/building-a-tab.md) | §10quater | Building a tab from a type and its services, never copied: the host, the context, the service's contract, the five types, a complete example (issue #95). | 9 KB |
| [`ui/calc-tab.md`](ui/calc-tab.md) | §10quater | Building a tab of calculation on the common base: what the base does once, what a domain declares, the snow as the complete example, what the wind, the permanent loads, the seismic action and the member checks will bring. | 8 KB |
| [`ui/tab-dead-load.md`](ui/tab-dead-load.md) | §10quater | The «Poids propre et surcharge» tab: the table of layers at the keyboard, «Couche n», the section and the contributions, the overview, the templates, «Affichage». | 5 KB |
| [`ui/tab-snow.md`](ui/tab-snow.md) | §10quater | The «Neige» tab: the building, the site, the roof among five tiles, the norm under each datum, the modules of the right pane, «Affichage» of the case's file. | 4 KB |
| [`ui/tab-materials.md`](ui/tab-materials.md) | §10quater | The «Matériaux» tab on the type «Bibliothèque»: the list, the sheet in folds, the source on the right, the first tab that is not the project's. | 6 KB |
| [`ui/tab-wind.md`](ui/tab-wind.md) | §10quater | The «Vent» tab: four sections, the building in 3D, the coloured tables of the norm, hovers by keys, the results in 3D, «Affichage» with the norm's figure at level 3. | 5 KB |

## Decisions and open questions

| File | Sections | Covers | Size |
|---|---|---|---|
| [`decisions.md`](decisions.md) | §13 | Every settled decision with its reason and accepted price, each with its status. Large: grep it, do not read it whole. | 394 KB |
| [`decisions-index.md`](decisions-index.md) | §13 | The decisions by theme, each by its status and the beginning of its bold sentence: the way into `decisions.md`. | 44 KB |
| [`open-questions.md`](open-questions.md) | §14 | What is not done or not decided yet, each point dated by its version. Grep it for the topic at hand. | 84 KB |

## History

| File | Sections | Covers | Size |
|---|---|---|---|
| [`history/status-notes.md`](history/status-notes.md) | status line | The per-version status paragraphs that headed CLAUDE.md until v0.117, newest first. The journal of every version is CHANGELOG.md. | 179 KB |
| [`history/changelog-v0.1-to-v0.100.md`](history/changelog-v0.1-to-v0.100.md) | — | The versions of `CHANGELOG.md` before v0.110, moved verbatim on 2026-10-10. | 484 KB |
| [`test-report-2026-10-10.md`](test-report-2026-10-10.md) | — | The test suite's report of 10.10.2026 (issue #24): a dated snapshot, not kept up to date. | 17 KB |
| [`history/2026-10-21-commandes-typst-refonte-journal-lots-0-12.md`](history/2026-10-21-commandes-typst-refonte-journal-lots-0-12.md) | — | The progress journal of lots 0 to 12 of the Typst commands' overhaul (spec 2026-10-21-commandes-typst-refonte, §16), moved verbatim so that the spec stays under 100 KB. | 15 KB |
| [`history/2026-10-21-commandes-typst-refonte-journal-lots-13-18.md`](history/2026-10-21-commandes-typst-refonte-journal-lots-13-18.md) | — | The progress journal of lots 13 to 18 of the Typst commands' overhaul (spec 2026-10-21-commandes-typst-refonte), moved verbatim on 2026-10-22 to keep the spec under 100 KB. | 11 KB |
| [`history/load-workbook-sheets.md`](history/load-workbook-sheets.md) | §3.3, §3.3bis, §3.3ter, §3.3quater, §3.3sexies-bis | How Woodcore read the `SL-*`, `WL-*` and `EL+AL-*` sheets of the Belastungsannahmen workbooks (v0.18 to v0.124), moved verbatim from `domain/loads.md` and `domain/calculation-domains.md` on 2026-10-25 when issue #109 retired the reading. | 40 KB |
| [`history/2026-10-25-tab-member-checks-before-112.md`](history/2026-10-25-tab-member-checks-before-112.md) | — | The member checks tabs before issue #112 (MemberCheckTab's three panes, «Flambage», «Déversement», the shear's list), moved verbatim from `ui/tab-member-checks.md` on 2026-10-25. | 12 KB |
| [`history/typst-retired-commands.md`](history/typst-retired-commands.md) | §10bis | The reference rows of the commands the Typst commands' overhaul retired (spec 2026-10-21-commandes-typst-refonte, lot 19), moved verbatim from `typst/api-conventions.md` on 2026-10-22; what each becomes is `calc/renamed-commands.json`. | 42 KB |
| [`history/formulas-retired-commands.md`](history/formulas-retired-commands.md) | §10quinquies | The sections of `typst/formulas.md` on `#val`, `#var-line`, `#var-unit`, `#var-domain` and the arguments `note:`, `sep:`, `summary:`, retired by the Typst commands' overhaul (spec 2026-10-21-commandes-typst-refonte, lot 19), moved verbatim on 2026-10-22. | 16 KB |
| [`history/report-engine-retired-commands.md`](history/report-engine-retired-commands.md) | §5, §9 | The sections of `typst/report-engine.md` on `#calc-block`, `#show-input` and the levels the retired commands printed their lines at, retired by the Typst commands' overhaul (spec 2026-10-21-commandes-typst-refonte, lot 19), moved verbatim on 2026-10-22. | 7 KB |
| [`history/2026-10-25-tab-formulas-pills.md`](history/2026-10-25-tab-formulas-pills.md) | §10quater | The «Formules» tab of v0.117 to v0.124 -- one text, a pill a command (issues #15, #40) --, moved verbatim from `ui/tab-formulas.md` when issue #113 rebuilt it. | 11 KB |
| [`history/2026-10-22-niveau-manuel.md`](history/2026-10-22-niveau-manuel.md) | §10quater, §4 | The paragraphs that described the level of detail -1 «Sélection manuelle» as current -- the window, the member checks, report-engine §4, the data contracts --, moved verbatim when the spec 2026-10-22-retrait-niveau-manuel took it out of the window (issue #93). | 7 KB |
| [`history/2026-10-22-onglet-neige-type-journal-lots-1-8.md`](history/2026-10-22-onglet-neige-type-journal-lots-1-8.md) | — | The progress journal of lots 1 to 8 of the snow tab rebuilt as the first tab of calculation (spec 2026-10-22-onglet-neige-type, §16), moved verbatim on 2026-10-22 to keep the spec under 100 KB. | 6 KB |
| [`history/2026-10-22-onglet-neige-type-risques-revue.md`](history/2026-10-22-onglet-neige-type-risques-revue.md) | — | The risks of the three architecture reviews of the snow tab rebuilt as the first tab of calculation and what the spec made of each (spec 2026-10-22-onglet-neige-type, §13.3), moved verbatim on 2026-10-22 to keep the spec under 100 KB. | 10 KB |
| [`history/2026-10-24-onglet-commandes-pages-source.md`](history/2026-10-24-onglet-commandes-pages-source.md) | — | The source (§2, issue #115 cut into points T) of the spec 2026-10-24-onglet-commandes-pages, moved verbatim on 2026-10-24 to keep the spec under 100 KB. | 18 KB |
| [`history/2026-10-24-onglet-domaines-formulaire-code-source.md`](history/2026-10-24-onglet-domaines-formulaire-code-source.md) | — | The source (§2, issue #113 cut into points T) of the spec 2026-10-24-onglet-domaines-formulaire-code, moved verbatim on 2026-10-24 to keep the spec under 100 KB. | 26 KB |
| [`history/2026-10-24-onglet-domaines-formulaire-code-tracabilite.md`](history/2026-10-24-onglet-domaines-formulaire-code-tracabilite.md) | — | The traceability table (§12) of the spec 2026-10-24-onglet-domaines-formulaire-code, moved verbatim on 2026-10-24 to keep the spec under 100 KB. | 4 KB |
| [`history/2026-10-24-onglet-domaines-formulaire-code-revue.md`](history/2026-10-24-onglet-domaines-formulaire-code-revue.md) | — | The architecture review (§13) of the spec 2026-10-24-onglet-domaines-formulaire-code, moved verbatim on 2026-10-24 to keep the spec under 100 KB. | 25 KB |
| [`history/2026-10-24-onglet-variables-groupes-source.md`](history/2026-10-24-onglet-variables-groupes-source.md) | — | The source (§2, issue #114 cut into points T) of the spec 2026-10-24-onglet-variables-groupes, moved verbatim on 2026-10-24 to keep the spec under 100 KB. | 22 KB |
| [`history/2026-10-25-tab-variables-before-114.md`](history/2026-10-25-tab-variables-before-114.md) | §10quater | The variables tab as it was from v0.100 to v0.124 -- «Affichage», the provenance in a column, the ★, «Tous les domaines» --, moved verbatim from `ui/tab-variables.md` on 2026-10-25 when issue #114 rebuilt the tab. | 17 KB |
| [`history/2026-10-24-onglet-variables-groupes-revue.md`](history/2026-10-24-onglet-variables-groupes-revue.md) | — | The architecture review (§13) of the spec 2026-10-24-onglet-variables-groupes, moved verbatim on 2026-10-25 to keep the spec under 100 KB. | 16 KB |
| [`history/2026-10-24-verifications-elements-v3-source.md`](history/2026-10-24-verifications-elements-v3-source.md) | — | The source (§2, issue #112 cut into points T) of the spec 2026-10-24-verifications-elements-v3, moved verbatim on 2026-10-25 to keep the spec under 100 KB. | 22 KB |
| [`history/open-questions-closed.md`](history/open-questions-closed.md) | §14 | The open points that were closed or settled, moved verbatim from `open-questions.md`. | 3 KB |

## Section → file

| § | File |
|---|---|
| §1 | [`project/purpose.md`](project/purpose.md) |
| §1bis | [`project/purpose.md`](project/purpose.md) |
| §1ter | [`conventions/writing.md`](conventions/writing.md) |
| §2 | [`architecture/principles.md`](architecture/principles.md) |
| §3 | [`architecture/data-contracts.md`](architecture/data-contracts.md) |
| §3.0 | [`architecture/data-contracts.md`](architecture/data-contracts.md) |
| §3.1 | [`architecture/data-contracts.md`](architecture/data-contracts.md) |
| §3.2 | [`architecture/data-contracts.md`](architecture/data-contracts.md) |
| §3.4 | [`architecture/data-contracts.md`](architecture/data-contracts.md) |
| §3.6 | [`architecture/data-contracts.md`](architecture/data-contracts.md) |
| §3.7 | [`architecture/data-contracts.md`](architecture/data-contracts.md) |
| §3.3 | [`domain/calculation-domains.md`](domain/calculation-domains.md) |
| §3.3bis | [`domain/loads.md`](domain/loads.md) |
| §3.3ter | [`domain/loads.md`](domain/loads.md) |
| §3.3quater | [`domain/loads.md`](domain/loads.md) |
| §3.3septies | [`domain/loads.md`](domain/loads.md) |
| §3.5 | [`domain/loads.md`](domain/loads.md) |
| §8 | [`domain/loads.md`](domain/loads.md) |
| §3.3quinquies | [`domain/connections.md`](domain/connections.md) |
| §3.3sexies | [`domain/position-plans.md`](domain/position-plans.md) |
| §3.3octies | [`domain/static-models.md`](domain/static-models.md) |
| §3.3nonies | [`domain/connectors.md`](domain/connectors.md) |
| §7bis | [`domain/connectors.md`](domain/connectors.md) |
| §3.3decies | [`domain/detail-schemas.md`](domain/detail-schemas.md) |
| §3.3undecies | [`domain/member-checks.md`](domain/member-checks.md) |
| §3.3septdecies | [`domain/member-checks.md`](domain/member-checks.md) |
| §3.3unvicies | [`domain/member-checks.md`](domain/member-checks.md) |
| §3.3unvicies-bis | [`domain/member-checks.md`](domain/member-checks.md) |
| §3.3duodecies | retired in 0.117: [`archive/rfem/docs/domain/rfem.md`](../archive/rfem/docs/domain/rfem.md) |
| §3.3quindecies | retired in 0.117: [`archive/rfem/docs/domain/rfem.md`](../archive/rfem/docs/domain/rfem.md) |
| §3.3terdecies | [`domain/journal.md`](domain/journal.md) |
| §3.3quaterdecies | [`architecture/figure-style.md`](architecture/figure-style.md) |
| §3.3sexdecies | [`domain/scripts.md`](domain/scripts.md) |
| §3.3octodecies | [`domain/documents.md`](domain/documents.md) |
| §3.3undevicies | [`domain/annexes.md`](domain/annexes.md) |
| §3.3vicies | [`domain/fire-plans.md`](domain/fire-plans.md) |
| §3.3duovicies | [`domain/variable-links.md`](domain/variable-links.md) |
| §3.3duovicies-bis | [`domain/variable-links.md`](domain/variable-links.md) |
| §3.3tervicies | [`domain/fire-resistance.md`](domain/fire-resistance.md) |
| §3.3quatervicies | [`domain/steel.md`](domain/steel.md) |
| §3.3quinvicies | [`domain/dependencies.md`](domain/dependencies.md) |
| §3.3sexvicies | [`domain/materials.md`](domain/materials.md) |
| §4 | [`typst/report-engine.md`](typst/report-engine.md) |
| §5 | [`typst/report-engine.md`](typst/report-engine.md) |
| §6 | [`typst/report-engine.md`](typst/report-engine.md) |
| §6bis | [`typst/report-engine.md`](typst/report-engine.md) |
| §9 | [`typst/report-engine.md`](typst/report-engine.md) |
| §4bis | [`typst/language.md`](typst/language.md) |
| §7 | [`domain/positions.md`](domain/positions.md) |
| §10 | [`typst/citations.md`](typst/citations.md) |
| §10bis | [`typst/api-conventions.md`](typst/api-conventions.md) |
| §10ter | [`typst/reference-workbook.md`](typst/reference-workbook.md) |
| §10quater | [`ui/window.md`](ui/window.md) |
| §10quinquies | [`typst/formulas.md`](typst/formulas.md) |
| §10sexies | [`typst/command-docs.md`](typst/command-docs.md) |
| §11 | [`architecture/layout.md`](architecture/layout.md) |
| §11bis | [`architecture/reference-library.md`](architecture/reference-library.md) |
| §11ter | [`conventions/testing.md`](conventions/testing.md) |
| §12 | [`conventions/build-and-release.md`](conventions/build-and-release.md) |
| §13 | [`decisions.md`](decisions.md) |
| §14 | [`open-questions.md`](open-questions.md) |
| §15 | [`conventions/changelog-and-commits.md`](conventions/changelog-and-commits.md) |
