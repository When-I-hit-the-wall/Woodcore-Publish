# Prototype of the snow tab — calculation and display (22.10.2026)

The HTML prototype the engineer reviewed in four rounds before the snow tab is rebuilt. It is the reference of the GitHub issue that asks for the work: what it shows was decided, version after version; what the issue says outranks it where the two differ (the issue carries the decisions taken after this copy). Nothing in Woodcore reads this folder.

Open `index.html` in a browser, from this folder: it needs the files beside it and nothing else, no server, no network. It is a single page with two views, «Calcul» and «Affichage», switched at the top of the tab, then the reasoning below it.

| File | What it is |
|---|---|
| `index.html` | The page: the tab's mock-up in de/fr/en, its script (the snow computation, the drawings of SIA 261 figure 3, the hover bubbles, the modules of the right pane, the «Affichage» mode) and the sections that explain it. |
| `norm/` | The excerpts of SIA 261:2020 cut out of `SIA261-2020-FR.pdf` and `-DE.pdf` (the engineer's `norms` repository): one PNG per clause or figure per edition. The page box of each, in PDF points, is in the script's `N` table. |
| `pages/` | The pages of chapter 5 in each edition, which Ctrl+click opens. |
| `prev/` | Real Typst renders by Woodcore 0.122's engine: every line of `SN-01.typ` at levels 1 to 3 with each value of each display argument, packed one sprite per line (`line-<key>.png`, offsets in the script's `D5` table), the domain's heading, the figure at five widths, and the whole file at levels 1 to 3 (`file-L*.png`). `SN-01-fig3.svg` is the drawing of the roof's column of figure 3. |
| `SN-01.typ` | The domain file the renders were made from: written by `unfold._generate_load` for a duo-pitch roof at 850 m, the cornice line taken out and the figure added at its head, as the engineer decided. |

The earlier versions are claude.ai artifacts of the engineer's account, linked from the issue.
