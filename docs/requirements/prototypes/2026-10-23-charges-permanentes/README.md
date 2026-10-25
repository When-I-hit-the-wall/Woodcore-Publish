# Prototype of the dead-load tab «Poids propre et surcharge» (23.10.2026)

The HTML prototype the engineer reviewed in three rounds on 21 and 23.10.2026 and validated whole in its third version («Je valide entièrement l'artifact de charge permanente V3», 24.10.2026). It is the reference of the GitHub issue that asks for the work: what it shows was decided, version after version; what the issue says outranks it where the two differ. Nothing in Woodcore reads this folder.

Open `index.html` in a browser, from this folder: it needs nothing else, no server, no network. It is a single page: the tab's mock-up in de/fr/en with its two views, «Calcul» and «Affichage», switched above the window, then the reasoning below it (the engineer's remarks and what the version does with them, the poses, the section at its true proportion, the display, the Lignum templates, what changes in Woodcore, the questions).

| File | What it is |
|---|---|
| `index.html` | The page and its script: the calculation of a layer (`calcLoad`, `isFiller`, `fillerWidth`, `sums`, `autoRet`), the warnings (`warnings`), the material search by name and category in three languages (`SYN`, `search`, `rank`), the keyboard path through the cells (`nextCell`), the section at its true proportion (`sectionSVG`, legend mode under 560 px), the contributions (`contribHTML`), the right pane's modules, the «Affichage» page by level and the sketch of the Typst file (`renderPage`, `renderDispRight`, `typFile`), the templates (`renderTpl`). |
| `lib.json` | The 183 materials of the prototype's library: 81 «SIA 261» (SIA 261:2020 Tables 28, 29, 30 as `calc/norms/` holds them, plus the workbook rows that cite the norm with its value), 99 «Externe» (the rest of `calc/libraries/materials-library.json`, merged by name and weight), 3 «Personnel» examples. Each with its names in fr/de/en, its family, its value and unit and its reference. |
| `lib.py` | The script that wrote `lib.json` from the repository's own files: it holds the French and English names of every row of SIA 261 Tables 28 to 30 (read on the French edition, p. 77–78) and the family of each material. Run it from this folder: `python lib.py`. |
| `comps.json`, `comps.py` | The eight templates drawn from Lignum «Holzbau mit System» (2023), with their reference in the book, the spacings the prototype assumes and the book's total weight where it gives one; and the three build-ups of the example project (AU-01 roof, PL-01 floor, PA-01 wall). |

The earlier versions are claude.ai artifacts of the engineer's account, linked from the issue.
