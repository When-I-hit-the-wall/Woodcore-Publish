# Prototype of the wind tab — calculation and display (23.10.2026)

The HTML prototype the engineer reviewed in five rounds, on 22 and 23.10.2026, before the wind tab is rebuilt on the base of issue #95. It is the reference of the GitHub issue that asks for the work: what it shows was decided, version after version; what the issue says outranks it where the two differ. Nothing in Woodcore reads this folder.

Open `index.html` in a browser, from this folder: it needs the files beside it and nothing else, no server, no network. It is a single page with two views, «Calcul» and «Affichage», switched at the top of the tab, then the reasoning below it (decisions, defects found in Woodcore 0.122, questions answered).

| File | What it is |
|---|---|
| `index.html` | The page: the tab's mock-up in de/fr/en and its script — the wind computation (q_p, c_red, the global forces Q_k, the local pressures q_k per surface and per φ with c_d and the openings), the 3D model of the six buildings drawn so far (`DRAWN`, `model3d`, `view3d`), the 3D results, the hover bubbles (`N`, `FIELD_NORM`), the modules of the right pane and the «Affichage» mode. |
| `figs/` | The figure of each building of SIA 261:2020 annex C (tables 31 to 64), FR and DE, cut out of the engineer's PDFs. |
| `tabs/` | The tables 31 to 64 themselves, FR and DE, shown in the bubbles. |
| `norm/` | The excerpts of chapter 6 (6.2.1.1 to 6.3.5, table 4, figures 9 and 22) and the map of annex E, FR and DE. The page box of each, in PDF points, is in the script's `N` table. |
| `pages/` | The pages of chapter 6 (FR p. 30–35, DE p. 29–34) and of annex C (p. 81–114), which Ctrl+click opens. |
| `prev/` | Real Typst renders by Woodcore 0.122's engine: every line of `WL-01.typ` at levels 1 to 3 with each value of each display argument, one sprite per line (`line-<key>.png`), the two tables with and without their title and note, the norm's figure of table 36 at five widths, and the whole file at levels 1 to 3 (`file-L*.png`). |
| `WL-01.typ` | The domain file the renders were made from: written by `unfold._generate_load` for the storage hall of table 36, with the engineer's decisions applied — the global forces as Q_k in kN, the local forces of the chosen openings only and transposed, the norm's 2D figure of the table at the head (written at level 3 only), the German words of the French file left as they are (they are defects). |

The earlier versions are claude.ai artifacts of the engineer's account, linked from the issue.
