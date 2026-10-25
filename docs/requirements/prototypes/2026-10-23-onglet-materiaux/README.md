# Prototype of the «Matériaux» tab (23.10.2026)

The HTML prototype of a new tab, the materials library of all of Woodcore, which the engineer reviewed in two rounds on 23.10.2026 and validated in its second version (24.10.2026). It is the reference of the GitHub issue that asks for the work: what it shows was decided; what the issue says outranks it where the two differ. Nothing in Woodcore reads this folder.

Open `index.html` in a browser, from this folder: it needs the images beside it and nothing else, no server, no network. A PDF chosen with «Importer un PDF…» is shown in the page and sent nowhere. The page is the tab's mock-up in de/fr/en, then the engineer's answers and what each changes, how a design value is deduced, what the prototype shows and what changes in Woodcore.

| File | What it is |
|---|---|
| `index.html` | The page and its script: the list by category with its search and filters, the sheet of a material (identity, weight, strengths of a member or of a panel, comment, source), the deduction of the design values (`barD`, `panD`, the tables `FAM` and `PK`), the state (`states`, `missing`, `deduced`), «Disponible dans» (`avail`), the source in the right pane and large (`sourceView`, `popHTML`), the PDF import. |
| `libdata.json` | The 193 materials of the prototype: the 11 grades of SIA 265:2021 Tables 8 and 9 read from `calc/norms/`, the OSB/3 panel of SIA 265/1:2018 Tables 19a and 19b (transcribed for the prototype, checked on the French edition, p. 42), the weights of the dead-load prototype, and four «Personnel» examples. |
| `data.py` | The script that wrote `libdata.json` from the repository's files and from `../2026-10-23-charges-permanentes/lib.json`. Run it from this folder: `python data.py`. |
| `tab08.jpg`, `tab09.jpg` | SIA 265:2021 Tables 8 and 9 (French edition, p. 25 and 27), the source shown for a grade. |
| `tab19a.jpg`, `tab19b.jpg` | SIA 265/1:2018 Tables 19a and 19b (French edition, p. 42), the source shown for OSB/3. |

Both versions are one claude.ai artifact of the engineer's account, linked from the issue: its version 1 compared three layouts, its version 2 is the one validated and copied here.
