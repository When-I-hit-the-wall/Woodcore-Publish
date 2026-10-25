# The reference library (ExternalFiles/)

> Norms and literature beside the program; values are read from the norm itself.
>
> Moved verbatim from CLAUDE.md (§11bis) on 2026-10-07. The § numbers are kept as stable anchors: `docs/README.md` maps every § to its file.

## 11bis. The reference library — `ExternalFiles/` (v0.53; beside the program since v0.82)

**Since v0.124 the norms are shipped with Woodcore** (issue #94, spec `docs/requirements/completed/2026-10-22-onglet-neige-type.md`, D-21, D-22, D-24; `docs/decisions.md`). The engineer, 22.10.2026: «change la règle 11bis. Il est tout à fait acceptable d'avoir des extraits de norme ou des normes complètes livrées avec woodcore», and before it: «l'ingénieur autorise sans limite à découper la norme, à l'afficher dans Woodcore et à l'imprimer dans les rapports». Every PDF at the root of his `When-I-hit-the-wall/norms` repository -- not its `Litteratur/`, and not `SZS-C4-2021.pdf` and `SZS-C5-2018.pdf`, 353 and 245 MB, which GitHub refuses outside Git LFS -- is copied into **`norm-library/`** at the top of the program's repository (78 files, ~164 MB, `*.pdf binary`) and frozen into the installer beside `calc/` (`packaging/woodcore.spec`); nothing of it goes into a project. `calc/norms/library.py` finds a file there through `project.APP_ROOT` (`WOODCORE_NORMS_LIBRARY` naming another folder), `calc/norms/excerpts.py` reads where an excerpt lies and its words in the norm file that cites it (`editions`, `excerpts`), and the window cuts the excerpt out of the page and opens the chapter (`calc/tools/excerpt_image.py`, `norm_reader.py`). **What changes in the two rules below**: the norms are no longer read by the engineer and the assistant alone -- `calc/` opens them --, and the excerpts' words are copied, once, into the norm files (`sia261-2020-5.2-schnee.json` `excerpts`; the wind's in a file of excerpts alone, `sia261-2020-wind-excerpts.json` -- chapter 6, Annexe E with its map, each of Annexe C's 37 buildings twice, its table and its figure, an excerpt of an annex naming the pages Ctrl+click opens, `chapter` (spec 2026-10-23-onglet-vent-briques, ARCH-012)), held to the shipped PDF by `tests/test_norm_excerpts.py` so that the copy cannot age unseen. The rest stands: a value is still read off a named edition and never from memory, and a `_source` names the edition and its file, never a machine's folder. ⚠️ The installer is published on a public repository (`woodcore-releases`), so the shipped norms go out with it: the engineer's decision, said to him on 22.10.2026. ⚠️ The PDFs carry their licensee's stamp on every page.

`ExternalFiles/`, beside `Woodcore/` and the projects, holds the documents the projects are calculated against: the norms, the literature behind them, the course documents of the topics the report covers, and a set of third-party tools. It is **read by the engineer and by the assistant, and by nothing else** (⚠️ not the norms since v0.124: shipped in `norm-library/`, see above) — no module of `calc/` opens a file in it, no schema mentions it, `export_all.py` does not know it is there, and the report does not read it either. It is documentation, and the one place the engine meets it is where a norm's numbers are transcribed by hand into `calc/norms/*.json` (§11).

**No path of a machine is written in the repository** (19.10.2026, spec 2026-10-19-base-saine-nettoyage, REQ-004; the engineer: «retire ce chemin du poste»). The library was named `ExternalFiles/000-Normes/` in every `_source` of `calc/norms/*.json`, in docstrings and in messages -- a folder that is not where the PDFs lie on the engineer's machine. Since then a `_source` names the **edition and its file** (`SIA265-2021-DE.pdf`, p. 25) and never its folder; an edition the library lacks says «Not in the reference library» and gives the publisher's address. A test that turns a page of the PDF finds the folder in the environment variable **`WOODCORE_NORMS_LIBRARY`** (`tests/conftest.norms_library`) and skips, naming it, on a machine that has none.

### What is in it

| Folder | What it holds |
|---|---|
| `000-Normes/` | **59 norm PDFs.** The structural core: **SIA 260:2013** in German, French and English, **SIA 261:2020** in German and French with SIA 261/1:2020 and the withdrawn SIA 261.007 (EN 1991-1-7, accidental actions), **SIA 265:2021** in German and French with SIA 265/1:2018 (supplementary specifications), SIA 265.131 (EN 335, use classes) and SIA 265.230 (EN 350, durability). The steel norms: **SIA 263:2013** and SIA 263/1:2020, each in German and French. The **Eurocodes**: EN 1993-1-1:2022, EN 1993-1-8:2005 (joints, in German and French), EN 1995-1-1:2004, EN 1995-1-2:2004 (fire), SIA 260.001 (EN 1990) and the **FprEN 1995-1-1:2025** draft. The EN test and product standards behind them: EN 338 (strength classes), EN 408, EN 1380 and EN 26891 (joint testing), EN 13049, EN ISO 898-1 (bolt grades). The **VKF/AEAI fire-protection directives** 10-15 to 28-15, in French. The **STE Compact** booklets, 01 (the timber engineer's services) and 02 (*Plans dans la construction en bois*, the symbology §3.3sexies draws). And the envelope and contract norms a project needs beside them: SIA 103, 112, 112/1, 180, 232/1, 331, 343, 343/1 and 380/1. |
| `000-Normes/Litteratur/` | **5 handbooks.** Lignum's Holzbautabellen in both editions (`HBT-FR-2012`, `Lignum-HBT-DE-2021`), its **Bemessungsbeispiele zur SIA 265**, *Erdbebengerechte Holzbauten* and *Holzbau mit System*. Handbooks, not norms: read to understand a clause, never cited as its source. |
| `101-` … `111-` | **One folder per calculation topic**, each with the course document that sets the method out and, where the engineer took them, screenshots of the worked example: 101 reinforcement against transverse compression, 102 dovetails and transverse tension, 103 glued-in threaded rods, **104 the polar moment** (§3.3quinquies), 105 glued hardwood products, 106 the γ-method, 107 bracing walls, 108 non-rectangular beams, 109 curved beams, 110 trussed beams, 111 fire resistance REI and compartmentation. |
| `000-contreventement/`, `000-positionsPlan/`, `111-…/` | **Three single-file HTML calculators**: a *Wandscheibe — Schubfluss-Tool*, the **Positionsplan-Editor** whose STE symbology §3.3sexies reimplemented, and a *Résistance au feu EI* calculator after Lignum 3.1. |
| `107-Contreventement/` | Beside its course document, `002-BerechnungenFunction.py` and `003-Rapport.md`: a shear check of stapled OSB and gypsum-fibre sheathing, and the scenarios it was run on. |
| `000-decompiled_CLTdesigner/` | **2 681 decompiled `.java` files** of the CLTdesigner (holz.bau forschungs gmbh). Read for the shape of a CLT calculation; decompiled bytecode is not a citable source and its identifiers are not the norm's. |
| `000-JonasHalter/` | A fellow student's *Statik-Rechner*, a React/TypeScript application from `github.com/jonashalter-a11y/Statik-Rechner`, with its own `data/chapters/` transcriptions of SIA 261, SIA 265, Baustatik and Lignum's fire and earthquake documents. It is here with its `node_modules/` and its `dist/`; nothing in this project builds, runs or imports it. |
| `201-excelTools/` | **The office's own Excel templates**, 27 `.xltx`/`.xltm` files and one shortcut: timber connections (Stabdübel and screws, nails, notches, dovetails), beams and slabs, column stability, cross-laminated panels, fire and earthquake checks, and the `Belastungsannahmen` template the project's load workbook comes from. They are the workbooks the periodic audit checks the calculations against (`prompt-audit.md`, phase 2); nothing in `calc/` opens one. |

### The two rules

**1. A value taken from a norm is read from the norm itself** (§2 rule 13). Every number in `calc/norms/*.json`, every `norm`/`norm_ref` a step cites (§2 rule 7), and every word §4bis's glossary quotes from an edition is taken from a named PDF in `000-Normes/`, at a page that can be turned to — not from memory, not from a handbook's restatement of it, and not from one of the tools beside it. That is what makes §1bis's normative traceability real: the edition is named in the data (`SIA 261:2020`, `norm:SIA 261:2020, Tabelle 8`) *and* the edition is a file of the library, at a page that can be turned to. Until v0.82 that file was versioned in the same repository as the report; since then the library is kept beside the program and outside every repository, the norms being licensed copies and the code's repository being shared with developers (§13) — so what ties a report to the editions it was written against is their name in the data and the library the office keeps, and a report built before v0.82 is traced through the old repository's bundle.

The documents the engine already quotes, and where they now are:

| Quoted by | Document |
|---|---|
| `calc/norms/sia261-2020-tab08-nutzlasten.json`, Tabelle 8 (§3.3septies) | `000-Normes/SIA261-2020-DE.pdf`; its French wording, §4bis's, is `SIA261-2020-FR.pdf` p. 38 |
| `calc/i18n/strings.json`'s French and English (§4bis) | `SIA261-2020-FR.pdf` (1.2, chapters 5 and 6, annex H's Tabelle 80), `SIA265-2021-FR.pdf`, `SIA260-2013-FR.pdf` and `SIA260-2013-EN.pdf`, `STE-Compact02-FR.pdf`, `EN-1995-1-1-2004.pdf` |
| a connection's `DEFAULT_NORM` (§3.3quinquies) | `104-MomentPolaire/001-Artikel-ArbeitshilfePolaresFlachentragheitsmoment-…pdf`, the bauforumstahl Arbeitshilfe whose Bild 3 v0.50's green arrow follows |
| the 3 × 5 dowel group §3.3quinquies is verified against | `104-MomentPolaire/Fiche_methode_assemblage_effort_tranchant_1.pdf`, the HB2 method sheet |
| the plan symbology and its legend (§3.3sexies, §4bis) | `STE-Compact02-FR.pdf` |

**2. The tools are unverified.** The engineer said so when adding them, and it is the safer assumption for every one of them. They are read for their **method** — which clause, which factors, in which order — and never for a number. Nothing in `calc/` may import, copy or depend on one; a figure taken from one is re-derived against the norm before it reaches the report; and where a tool and the norm disagree, the norm decides, without further discussion. The position-plan editor is the standing precedent (§13): its STE symbology was taken, its code was not, its loads contradict §8, and its own copy of each element's description would have been a second source beside `Positionen.xlsx` (§2 rule 1). ⚠️ `107-Contreventement/003-Rapport.md` is the reminder that this is not a formality: it prints its `f_v0d` in kN/mm where the quantity is a shear flow in kN/m.

### Reading one

**Sixty-three of the sixty-four norm and literature PDFs carry extractable text**, so a clause is read and quoted exactly rather than recalled — page by page, with the `pypdf` the pipeline already depends on (§13):

```python
from pypdf import PdfReader
p = "SIA261-2020-FR.pdf"
print(PdfReader(p).pages[37].extract_text())        # p. 38: Tableau 8
```

⚠️ `SIA-343-2014-FR.pdf` is the one scan, and three of the course documents are scans too (`101-…/002-Querdruckverstarkung`, `103-…/008-BIROD`, `104-…/001-Artikel-PolaresFlachentragheitsmoment`); a lecture slide carries little text per page in any case, so those are read as images.

⚠️ **They are licensed copies.** The report cites a clause and never reproduces one (§2 rule 7): what crosses into `data/` and into the glossary is a value, a symbol, and the norm's own word for a term — never a paragraph of its text. ⚠️ *Lifted by the engineer for the norms on 22.10.2026 (v0.124, D-22): an excerpt's words are copied into its norm file and shown by the window, its image cut out of the shipped PDF; see the head of this section.* The same holds for the literature: Lignum's Bemessungsbeispiele explains a method, it does not authorize it; the clause behind it does.

👉 The folder mirrors `301-Normes`, the norm library that sits beside the project in the engineer's own tree. Since v0.82 it is `ExternalFiles/`, beside `Woodcore/` and the projects, and it weighs about 900 MB, of which about 610 MB of norms and 170 MB of `000-JonasHalter/node_modules` (measured at v0.77) — which the code's repository no longer carries: a first clone fetches the code alone.


---
