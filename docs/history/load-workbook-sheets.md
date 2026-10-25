# The load workbooks' sheets, as Woodcore read them (v0.18 to v0.124)

> Moved verbatim from `docs/domain/loads.md` (§3.3bis, §3.3ter, §3.3quater, §3.3sexies-bis) on 2026-10-25, when issue #109 retired the reading of the `SL-*`, `WL-*` and `EL+AL-*` sheets of the Belastungsannahmen workbooks (decision D-33 of the engineer, 24.10.2026: «il n'y aura plus jamais de feuille excel à lire pour le vent, ni pour la neige, ni pour les charges permanentes»; `docs/decisions.md` §13). The modules it names -- `calc/domains/snow.py`, `wind.py`, `calc/io_excel.py`, the reader of `dead_load.py` -- are gone; what it says of the calculations of `snow_source`, `wind_source` and `dead_load_source` is kept current in `docs/domain/loads.md`.

## From §3.3bis

**Since v0.120 a sheet gives its inputs, Woodcore computes (spec `docs/requirements/completed/2026-10-21-restes-issue-69.md`, REQ-001, ARCH-002, D-06 to D-09).** The engineer, 21.10.2026: «classeur = entrées seulement». `calc/domains/snow.py` reads what the engineer enters on an `SL-*` sheet -- the altitude H10, the correction of Anhang D H11 (its label, «+200», read through the `Dropdowns` table B30:C34 and held to the norm), the exposure E14 (B24:C26), C_T H15, the load model F21 (its first word the roof: «Flachdach» flat, «Giebeldach» duo, «Sheddach» shed -- the load model itself is gone, both models of Figur 3 being computed), the plan dimensions or the slopes H23/H24, a height step F19 («Ja») and the sliding F29 -- into a snow-load source (`read_source`), checked field by field by `snow_source.check_fields`, a refusal naming the cell, and computes it by `snow_source.build_instance`: **one calculation of the snow**, the one a load entered in Woodcore is computed by, every value of SIA 261 out of `calc/norms/`. The domain's `ENGINE` is `python`; an instance still names its `workbook` and its `sheet`, and an input keeps its cell as its provenance (`excel:Belastungsannahmen.xlsm!SL!H10`), what is worked out `python:domains/snow_source.py`. A second slope left empty is 0°, as the sheet's own helper block takes it, and said (`sheet_slope_empty`).

**What the sheet computed is compared, never printed (D-07).** Where the sheet shows h_ref (H12), s_k (H17), a Dachformbeiwert (H26, H27, K35) or a load (I37 to I39, N37, N38) apart from Woodcore's -- relative tolerance `_common.SHEET_TOLERANCE`, 10⁻⁶ --, the export says so, naming the cell and the two values (`sheet_value_differs`); an empty cell and an Excel error are no difference. `loads_names.SNOW_COMPARED` says which cell holds which value, by the roof. The two refusals of the old reader -- a Dachformbeiwert computed from another sheet's roof by the shared helper block (`_check_mu_helper`), a load in a cell nothing read (`_check_all_results_read`) -- are gone with what they guarded: such a sheet's value now differs from Woodcore's, and is said. A site above 2000 m (5.1.4) is said too (`snow_above_limit`, `snow_source.notes_of`), for a sheet as for a source.

⚠️ *Retired by the spec 2026-10-21-commandes-typst-refonte (lot 19): `val` -- write #var("M_d") -- #var(name) reprints a variable declared above, #var(name, domain: ("snow-load", "SL")) reads one of the export; `show-calc` -- write #include domain-file(kind, id) -- a load ("snow-load", "wind-load", "dead-load", "live-load"), a connector, a polar moment ("connection"), a script: its file, written out by the export, printed where the section includes it. What follows describes it as it was.* **The names are the source's (D-06, CON-002).** A flat roof's one load is `q_k1` where the sheet called it `q_k11`, its coefficient `mu_1`; `lastmodell` is `dachform` (its value the roof's word, «Flachdach»), `hoehenspruenge` is `hoehensprung` where F19 says «Ja» and nothing where it says «Nein»; Δh (`korrektur`) is a number. The one table of what changed is `calc/domains/loads_names.py`; a project's sections, scripts and sources are rewritten to the new names when it is opened (`calc/domains/loads_migrate.py`: `var-of`, `value-of`, `show-input`, `val(…, domain:)`, `show-calc(…, shown:)`, a script's `value(…)`, every link `{domain, instance, var}` of a source), each file saved first into the archives, as the report commands were (§13); a name with no equivalent, or a call the migration cannot rewrite safely, stops the export naming the file and the line. `woodcore-cli loads migrate [--dry-run]` does the same from a terminal. What follows describes the reader until v0.120.

**Until v0.120** a snow load read from a workbook was **not** calculated in Python (one entered in Woodcore was, by `snow_source`, since issue #36 -- below). It is calculated in the `SL-*` sheets of the Belastungsannahmen workbooks — the workbook the engineer already fills in for a project — and `calc/domains/snow.py` contains no arithmetic at all: it reads each sheet's cells and wraps them in the ordinary `vars`/`steps`/`checks` shape of §3.3, so every `SL-*` sheet enters `data/calculations.json` as one instance of the `snow-load` domain, indistinguishable in structure from any other calculation.

The reader handles both shapes a sheet can take: a flat roof with one result q_(k,11) (the project's one SL sheet today, `SL`) and a pitched load model with two results q_(k,11) and q_(k,12) (`SL-Dach2` of the workbook this module was written against, `GiebeldachLM2`).

What is read, and the order the report prints it in. That order is deliberately **not** cell order: `show-calc` walks a calculation var by var (§10bis), so the order the vars are added in `snow.py` *is* the level-3 layout — the reference height, then the coefficients, then the building geometry, then the qualitative choices, then the roof-shape factors, and the two calculated values last, each where its formula belongs. The `Level` column is what splits the three reports (§3.7), and a var is levelled **separately from the step that produces it**: that is why `h_ref` and `s_k` appear as plain values at level 2 and only grow their formula at level 3. Four pairs also carry a `group` (§3.3) and so share a row apiece — `C_e`/`C_T`, `L`/`B`, `alpha_1`/`alpha_2`, `mu_11`/`mu_12` — and `L` carries the `group_label` **Gebäude Geometrie**, which names its row.

| Var | Cell | Level | Meaning |
|---|---|---|---|
| `h_0` | `H10` | 3 | Höhe ü. NN — never on a row of its own, it appears inside h_ref's substituted formula |
| `korrektur` | `H11` | 3 | Korrektur Wert (SIA 261, Anhang D) — likewise |
| `h_ref` | `H12` | 2 | Bezugshöhe; its step is level 3, so level 2 shows the value alone |
| `ce` | `H14` | 3 | Expositionsbeiwert C_e (its Windexposition label from `E14`) |
| `ct` | `H15` | 3 | Thermischer Beiwert C_T |
| `L`, `B` | `H23`, `H24` | 3 | Abmessungen Gebäude — the flat roof only |
| `hoehenspruenge` | `F19` | 3 | Grosse Höhensprünge? (`Ja`/`Nein`) |
| `abgleiten` | `F29` | 3 | Abgleiten des Schnees (drives the μ ≥ 0.8 rule, SIA 261 5.3.4) |
| `lastmodell` | `F21` | 3 | Dachform / Lastmodell |
| `alpha_1`, `alpha_2` | `H23`, `H24` | 3 | Dachneigung(en) — every load model but the flat roof; the same two cells, which the sheet relabels in place |
| `mu_11`, `mu_12` | `H26`, `H27` | 3 | Dachformbeiwert(e) — `mu_12` only where the load model has one |
| `mu_2m` | `K35`, else `Dropdowns!F66` | 3 | Dachformbeiwert der Schneeanhäufung — `SheddachLM2` only. The sheet *labels* it (`I35`) but its template leaves the value cell blank, so it is read where `I39` reads it: off the helper block |
| `s_k` | `H17` | 2 | charakteristischer Wert auf horizontalem Gelände; its step is level 3 |
| `q_k11`, `q_k12`, `q_k2m` | `I37`, `I38`, `I39` | 1 | charakteristische Schneelast(en); their steps are level 1, so this is what a client report shows. `q_k12` for every load model but the flat roof, `q_k2m` for `SheddachLM2` |

⚠️ *Retired by the spec 2026-10-21-commandes-typst-refonte (lot 19): `show-calc` -- write #include domain-file(kind, id) -- a load ("snow-load", "wind-load", "dead-load", "live-load"), a connector, a polar moment ("connection"), a script: its file, written out by the export, printed where the section includes it. What follows describes it as it was.* Three `steps` carry the formulas the sheet applied — Bezugshöhe, s_k and q_k — as display strings (§6bis) beside the value Excel computed with them. The whole chain is printed by a single `show-calc("snow-load", "SL-Dach1")` (§10bis), which renders each of them as the formula in letters followed by the same formula in numbers. **s_k is the exception, and the reason `show-calc` has one**: its formula states a *bound* (`... >= 0.9 thin "kN/m"^2`, the floor SIA 261 5.2.6 puts under the ground value), and a bound cannot be closed with `= 1.729 kN/m²` without printing a chain of two relations only one of which happened. That step therefore keeps the compact `mit h_ref = 638 m` note and prints its result on a row below.

**The printed q_k formula follows the sheet's own branch.** `I37` and `I38` both test `F29` (Abgleiten): with the sliding hindered the sheet raises μ₁₁ to at least 0.8 and drops μ₁₂ for a flat 0.8 (SIA 261 5.3.4). `snow.py` therefore emits `q_(k,11) = max(mu_11, 0.8) dot C_e dot C_T dot s_k` in that case rather than the unconditional product — printing a formula that does not produce the number standing next to it is exactly the kind of error a reader cannot catch.

Conventions this introduces, both deliberate:

- **A var's `value` may be text**, not only a number: `lastmodell` is `"Flachdach"`, `hoehenspruenge` is `"Nein"`. Their `symbol` is a quoted Typst math string (`"\"Lastmodell\""`) so it renders as upright text, and `fmt-value` prints them unchanged. `schemas/calculations.schema.json` says so explicitly (`"value": {"type": ["number", "string"]}`).
- **`choices` are read from the workbook's own `Dropdowns` sheet** (`B24:C26` for the exposure, `B30:C34` for the correction), never restated in Python — a footnote in the report cannot then disagree with the list the engineer sees in Excel.

👉 The reader is deliberately brittle in one direction only: cell addresses are pinned as constants in `domains/snow.py`, and a cell that turns up empty, holds an Excel error, or holds a value outside its dropdown is a **blocking export error** naming the cell — never a silently empty or wrong load. Note that openpyxl reads *cached* values: the workbook has to have been saved by Excel for its computed cells to carry anything at all.

Two things a value read on its own cannot tell, so both are checked rather than assumed (v0.24):

- **A load the sheet computed and nothing here read.** `RESULT_CELLS` lists every cell an SL sheet can put a characteristic load in — `I37`, `I38`, `I39`, and `GiebeldachLM2`'s `N37`/`N38`. One that holds a number and is not read is refused by name. Which cells carry a load is asked of the cells and never of the load model's name, so the dropdown cannot gain an entry this module silently ignores; `I39` used to be refused *specifically*, and `N37`/`N38` were not looked at at all.
- **A Dachformbeiwert computed from another sheet's roof.** `H26`/`H27` do not compute μ: they read it off a single helper block on `Dropdowns` (`F61` for a flat roof, `F64`/`F65` for a pitched one, `F66` for μ₂m), and that block's formulas name the sheet whose geometry goes in — `'SL-Dach1'!H23`. One block, every sheet, so a **copied** sheet displays its own Dachneigungen while reporting the original's μ, and the value alone gives nothing away. `_check_mu_helper` therefore reads the helper's *formula* (`io_excel`'s `formula()`, a lazily-parsed second read of the workbook) and blocks unless it is anchored to the sheet being exported. It applies only where the sheet's own μ cell actually reaches into the block: give a sheet its own μ formulas and there is nothing left to check. 👉 On the workbook of v0.24 this fired on `SL-Dach2` — a Sheddach with α₁ = 90° and α₂ = 20° reporting `SL-Dach1`'s 20.18/7.8, which puts q_(k,2m) at 2.028 instead of 2.767 kN/m². The fix is in Excel, not here: each SL sheet needs μ formulas reading its own `H23`/`H24`, and μ₂m written into `K35`, the slot its own label already points at.

## From §3.3ter

The permanent loads go the **opposite way round** from snow, and deliberately so (§13). An `EL+AL-*` sheet is a *table*: one row per layer, carrying what the engineer chose — material, thickness, width, spacing — while the load column beside it is Excel arithmetic. So here Excel is the input form and Python is the calculation: `calc/domains/dead_load.py` computes every number from the raw entries and reads not one value out of a formula cell.

Per layer, reproducing the sheet's own `K` column exactly:

```
load [kN/m²] = ρ · Dicke · Breite / (Dist. · 100)
```

The `/100` is the workbook's kg → kN conversion (g taken as 10 m/s²). A material given in kg/m² rather than kg/m³ needs no special case: those rows carry Dicke = Breite = Dist. = 1, so the formula degenerates to ρ/100 on its own. Rows with an empty `Material` cell are skipped, exactly as the sheet's own `IF(E="", "", ...)` does — ⚠️ **except a row with a number typed in the load column K** (v0.79, periodic audit 260916, B3): that is a load entered directly — template 3.2 does it for «Installationen und Innenwände», and a_k came out 0.5 kN/m² short with no word — counted as typed towards the `gk` or `ak` its row names, and printed with «Direkt eingegebene Last» and the load alone, the layer columns left empty.

The layers are summed into `gk` (rows marked `gk`) and `ak` (rows marked `ak`), then `gk_ak`; the build-up itself is carried as the one entry of the instance's `tables`. **What the report prints is four values, and at level 3 the table they come from, above them**: `g_k = 0.371 kN/m²`, `a_k = 0.856 kN/m²`, `g_k + a_k = 1.228 kN/m²`, `(g_k + a_k)_"gew" = 1.3 kN/m²`, one plain row each from level 2 up. **Neither sum carries a formula.** A Σ over the layers would state in letters exactly what the table lists row by row, so the two sums are the table's own `totals` rows instead, each standing under the column it adds up, and the per-layer arithmetic is a `note` under the table rather than a footnote on a formula. The table's first column is the symbol a layer counts towards (`g_k`/`a_k`, real math, not the sheet's `gk`/`ak` shorthand) and its `Gewicht` column prints the library's unit with a real exponent (`500 kg/m³`). **The final result is `gk_ak_gew`** — the *Gewählt* value, the rounded permanent load the engineer decided to design with. That is an entry, not a result, so it is read rather than recomputed, and it is what the report shows at level 1.

Two things follow from Python doing the arithmetic:

- **The specific weight is looked up here**, in the workbook's own `Material (hier ergänzen)` library, instead of being read from the sheet's XLOOKUP column. That also settles a real defect: `EL+AL-Dach2.ohnePV` was copied from another file and its lookups still point at a workbook that is not there (`[5]!Tabelle2`), so its cached weights cannot be trusted.
- **The lookup is keyed `(Ebene, Material)`, not `Material` alone.** The library lists a material once per `Ebene` it can appear under, and those repeats do not always agree — `Gartenplatten` weighs 2200 kg/m³ as a *Beschichtung* and 2000 as a *Beschwerung*, and Excel's XLOOKUP silently takes the first. A layer row names both, so the exact pair is used first, and the name-only fallback **refuses to guess** when the name is genuinely ambiguous. Library rows nobody uses are never resolved, so an inconsistency the project does not touch cannot block an export.

**Two things the sheet can say that contradict what it shows, and both are refused (v0.59).**

*A chosen value below the sum of its own layers.* The *Gewählt* value is an entry, not a result — the engineer rounds the computed sum up, on the safe side — so it is read rather than recomputed. What cannot happen is a chosen value *below* the layers it is chosen from: the report prints the Schichtaufbau above it, so the table would add up to one number and the bold line under it state another, and a checker could not follow the one to the other. Rounding is allowed for (a tenth of a percent, `CHOSEN_TOLERANCE`); anything beyond stops the export naming the cell and both numbers.

*A specific weight typed over the sheet's own lookup.* Column I is an XLOOKUP into the material library, and this module deliberately does not read it. That makes one thing invisible: a cell whose formula has been replaced by a number. Column E then names one material and the number beside it belongs to another, and since this exporter follows the *name*, the report prints a load the sheet does not show. `_check_weight_formula` reads the cell's **formula** — the same instrument `_check_mu_helper` uses on the snow sheets, and for the same reason — and refuses a literal that disagrees with the library. A literal that *agrees* states nothing new and passes.

👉 Both were found on the engineer's own workbook: `EL+AL-Dach ohne Wasser` had `I9` and `K9` typed over with 100 and 1, to get a dry Dachbegrünung, while `E9` went on naming the wet one at 160 kg/m². Python summed the layers to 2.412 kN/m², the sheet showed 1.812, the chosen value said 1.900, and nothing on the page gave any of it away. The fix is in Excel and is always the same: give the library a row for the material actually meant, name *that* row in column E, and put the lookup formula back.

👉 **Nothing here is pinned to a row number.** A facade has fewer layers than a roof, so its `Total` line sits two rows higher; the header, the `Total` line and the *Ständige Lasten* line are each found by their own label (`io_excel`'s `find_row`), and a layout change that loses one of them is a blocking error naming the sheet. An unknown material, a `Dist.` of 0, a non-numeric dimension or a missing *Gewählt* value are blocking errors too, each naming the exact cell.

## From §3.3quater

**Since v0.120 a sheet gives its inputs, Woodcore computes (spec `docs/requirements/completed/2026-10-21-restes-issue-69.md`, REQ-002, ARCH-002, D-07, D-08).** `calc/domains/wind.py` reads what the engineer enters on a `WL-*` sheet -- q_p0 J6, b, d, h J7 to J9, the terrain category I11 (its first word, «IV grossflächige Stadtgebiete» -> IV, the `Dropdowns` table B91:D94 held to Tableau 4), the table of Annexe C F40 and c_d J60 -- into a wind-load source, checked by `wind_source.check_fields` (a refusal naming the cell), and computes it by `wind_source.build_instance`: c_h, q_p, **c_red of Figur 9 and the rule of 6.3.3** (D-08, where the sheet read it off a scroll bar, J19/J20), the global forces of the table's force coefficients and the local pressures of its rows. `ENGINE` is `python`; the inputs keep their cells as provenance. The global forces are named by the table's force coefficients, `qk_max_cf1` where the sheet said `qk_max_bh` (`loads_names.wind_forces`: the one coefficient of a reference area; a table whose facades are b·h1 and d·h1 -- Tableaux 51 to 56 -- or that gives no force coefficient -- 50 -- has no equivalent, and a section that names one stops the export). **What the sheet computed is compared** (D-07): z_g, alpha_r, z, c_h, q_p, the two c_red and the six forces (`loads_names.wind_compared`), and its block of pressure coefficients B77:P81 row by row where its wind direction is one of the table's (a direction the table does not list is said, `sheet_direction_unknown`); each difference is a warning naming the cell and the two values. A facade's (h, beta) that Figur 9 does not draw is said (`wind_c_red_outside`, `sia261_wind.in_range`), for a sheet as for a source. The local-force envelope of the sheet's selection (G85/G86) and its check against the sheet's block (`wind_surfaces_unchecked`) are gone: the local table is the source's. What follows describes the reader until v0.120.

**Until v0.120** the wind load read from a workbook was arranged like the snow load and for the same reason (§13) -- one entered in Woodcore is computed by `wind_source` since issue #37, below: the `WL-*` sheets of the Belastungsannahmen workbooks own the calculation — the reference wind pressure, the terrain category and the profile it implies, the reduction and force coefficients, the global wind forces they produce — and `calc/domains/wind.py` recomputes nothing the sheet computes. It reads cells and gives them the ordinary `vars`/`steps`/`checks` shape (§3.3); its one piece of arithmetic is the envelope of the local wind forces (below), which the sheet does not compute at all. The prefix is `WL`, so copying a sheet (`WL-Halle`) adds that case with no code edit, as everywhere else; the three sheets of `Belastungsannahmen.xlsm` (`WL-Velo`, `WL-Fluchttreppe+Geräte`, `WL-Pavillon`) are all read by the same module.

**What makes this domain different is its answer.** A global wind force is not one number: it is a maximum and a minimum for each of three reference areas — b·h and d·h, the two facade areas, and d·b, the roof — which are three loads on three faces, not three candidates to maximise over. So the calculation ends on a **table**: `q_k = c_red · c_d · c_f · q_p` is printed once in letters, and the six results are the cells of the table under it, each cell naming its var (`value` columns, §3.3) rather than repeating its number. Those six vars *are* the instance's `results`, which is why they come out bold.

What is read, and the order the report prints it in — again not cell order, since `show-calc` walks a calculation var by var (§10bis). The `Level` column, with the two tables' own levels (below), is the whole of the level split this sheet was asked for: level 1 the terrain category and the global forces, level 2 the same with the local forces' table under them (v0.46), level 3 the sheet entire.

| Var | Cell | Level | Meaning |
|---|---|---|---|
| `qp0` | `J6` | 3 | Referenzwert des Staudrucks am Standort |
| `b`, `d`, `h` | `J7`-`J9` | 3 | Abmessungen — one row, under the `group_label` **Gebäude Geometrie** |
| `gelaendekategorie` | `I11` | 1 | Geländekategorie; its `choices` are the workbook's own `Dropdowns` table, each category listed with the z_g and α_r it implies |
| `zg` | `J12` | 3 | Gradientenhöhe |
| `alpha_r` | `J13` | 3 | Bodenrauigkeit |
| `z` | `J14` | 3 | Höhe über Boden (the sheet's own 5 m / 10 m floor) |
| `ch` | `J15` | 3 | Windprofilbeiwert |
| `cred_bh`, `cred_dh` | `J19`, `J20` | 3 | Reduktionsfaktoren der Bezugsflächen b·h und d·h |
| `cd` | `J60` | 3 | dynamischer Faktor |
| `qp` | `J17` | 3 | Staudruck — the one step of this sheet, `q_p = c_h · q_(p0)`, and the one marked **`bold`** |
| `qk_max_*`, `qk_min_*` | `J69`-`L70` | 1 | die sechs globalen Windkräfte — printed by the table, not on rows of their own |

Each of these rows is named on the page, not merely symbolised: a var may carry a `group_label` without a `group` (§3.3), which is what puts the sheet's own label in front of a single value — `Gradientenhöhe: z_g = 450 m`. A profile coefficient printed as `c_h = 1.048` and nothing else says too little.

**The local wind forces are in the engineer's report (v0.29, from level 2 since v0.46).** The sheet's «Lokale Windkräfte» block combines external and internal pressure, `q_k = q_p · (c_pe − c_pi)`, for its eight surfaces — walls A–D, roof zones E–H — but only for the one wind direction (`G85`) and the one opening (`G86`) the engineer has selected there. The report prints the envelope instead: for every surface and every opening case, the largest and the smallest value over all the directions the sheet lists. ⚠️ **Since spec 2026-10-23-onglet-vent-briques (V1) a sheet is computed by `wind_source.build_instance` like a source, and its file prints one openings' case**, the uniformly distributed openings (`rep`): the sheet's own selection `G86` is not read, a sheet's source holding no `openings` (D-24). The table below is that of the versions before. Excel computes no such thing, so `wind.py` does — the sheet's own formula applied to the sheet's own coefficient block (`B77:P81`: one row per direction, c_pe of the eight surfaces in `C:J`, c_pi of the six openings in `K:P`), and nothing more. It is a second entry of the instance's `tables` (§3.3), shown **from level 2** and set after the global forces, with its formula in letters above it:

| Columns | What they hold |
|---|---|
| Lokale Windkraft [kN/m²] | the surface, `Wand A` … `Dach H` |
| gleichmässig — max, min | uniformly distributed openings: both of the sheet's c_pi, `glm. (+)` and `glm. (-)`, enveloped together, since either internal pressure can occur |
| Öffnung A … D — max, min | a dominant opening in wall A, B, C or D: that wall's own c_pi column |

Three things keep it honest. The directions are **read, never assumed**: most figures list 0°, 15°, 45° and 90°, figure 42 lists 180° instead of 45°, and the note under the table names the ones enveloped. A blank `glm. (-)` — left empty by the figures that give a single uniform c_pi in some direction — is a combination that does not exist and is skipped, while a blank in any other column, a coefficient that is not a number, or a header row that moved is a blocking error naming the cell. And the envelope is **checked against the sheet**: wherever `G85`/`G86` hold a selection and `F90:F98` show numbers, each must equal what the envelope's own arithmetic gives for that selection, or the export stops naming the cell — so the arithmetic cannot drift from the sheet's formula, and a workbook saved without recalculating is caught rather than half-believed. A selection the sheet itself shows as an Excel error (`#N/A`, a direction the chosen figure does not list) is only a warning, those cells not being printed. The table's `source` (`python:domains/wind.py`) records the exception on a domain whose `engine` is `excel`.

👉 Two things this domain does **not** do, both deliberate. It does not read the global force coefficients c_f themselves (the `Q78:S81` block whose maxima and minima the six forces are built from): they are named in the table's `note` and in the formula, but the values this sheet was asked for stop at the six forces (§14). And it does not correct a sheet: the domain's `engine` is `excel`, so what it prints is what the sheet computed, defect included. ⚠️ `WL!L70` computed the d·b minimum as `=J19*1*MIN(S79:S81)*J60` — the reduction factor c_red,b/h where the Staudruck q_p belongs, over a range one row short of its neighbours' — in all three WL sheets of `Belastungsannahmen.xlsm`, whose printed d·b minima were c_red,b/h · min c_f until the engineer corrected the three cells to `=J17*1*MIN(S78:S81)*J60` on 17.09.2026 (periodic audit 260916, B1). It was these copies' defect and not the template's: the `Wind` sheet of `«load workbook» template` carries the corrected formula.

## From §3.3sexies-bis

A snow load and a wind load reach the report by two paths -- the load workbook's sheets (`snow.py`, `wind.py`) and the sources entered in Woodcore (`snow_source.py`, `wind_source.py`). ⚠️ Since the restes of issue #69 (v0.120, §3.3bis, §3.3quater) the two paths are one calculation: a sheet is read for its inputs and computed by the source's code, and its `Dropdowns` tables are read for their labels alone, each number still held to the norm. Until v0.120 the workbook path read the norm's numbers off the workbook's own `Dropdowns` sheet, the other off `calc/norms/`: two sources of one value. They were compared on 20.10.2026, the workbook's tables read from two of the engineer's load workbooks (the same in both: they are the template's) and the norm read on SIA 261:2020 (DE):

| Value | Workbook (`Dropdowns`) | calc/norms/ | SIA 261:2020 | Verdict |
|---|---|---|---|---|
| C_e, normal / exposed / sheltered | 1 / 0.8 / 1.2 (B24:C26) | 1.0 / 0.8 / 1.2 (`5.2-schnee`, `exposure`) | 5.2.4, p. 25 | the same |
| Δh of the reference height | -200, ± 0, +200, +400, +500 m (B30:C34) | -200, 0, 200, 400, 500 (`corrections`) | Anhang D, p. 115 | the same |
| μ_1 of a slope α | 0.8 to 30°, 0.8 (60 − α)/30 to 60°, 0 above (F64, F65) | (0, 0.8), (30, 0.8), (60, 0) (`mu_1`) | Figur 2, p. 27 | the same, the figure being a graph whose corners these are |
| μ_2 of the mean slope | 0.8 + 0.8 α/30 to 30°, 1.6 above (F66) | (0, 0.8), (30, 1.6) (`mu_2`) | Figur 2, p. 27 | the same, the figure being a graph whose corners these are |
| μ_1 of a large flat roof | 0.8 to 20 m, + 0.04 per m, 1.0 from 25 m (F61) | (20, 0.8), (25, 1.0) (`large_flat`) | 5.3.5 (p. 26), Figur 4 | the same, the figure being a graph whose corners these are |
| z_g, α_r of the terrain categories II, IIa, III, IV | 300 / 0.16, 380 / 0.19, 450 / 0.23, 526 / 0.30 (B91:D94) | the same (`6.2-wind`, `terrain`) | Tabelle 4, p. 30 | the same |
| c_pe, c_pi of Anhang C | sheet «Wind Tabellen Werte» | `tab31`…`tab64` | Anhang C | compared on 11.10.2026 (tests/fixtures/wind-tables-reference.json): five cells of the sheet were wrong, and the norm won |

Nothing had to be corrected in `calc/norms/`. **Since v0.120 the workbook path takes every number from `calc/norms/` too**: C_e, the corrections and z_g, α_r of a category are read there (`sia261_snow`, `sia261_wind`); the workbook gives its own words, the labels of its dropdowns, and a table of it that states another number than the norm stops the import naming the cell -- the workbook is then the one to correct. The formula of s_k it prints is composed from equation (10)'s values (`_common.plain`, UI-004), as the source path's is. The two warnings the workbook path printed to the console (a domain whose prefix no sheet carries, a wind sheet whose local block could not be compared on every surface) are `engine.Note`s of the export's list since, said in the window's language (C4).

## From docs/domain/calculation-domains.md §3.3

- A **domain** is one kind of calculation — `snow-load`, `dead-load`, `wind-load`, `live-load`. It declares an Excel **sheet prefix**, which side produces its numbers (`engine`: `excel`, `python`, or `norm` for a domain read from a norm table, §3.3septies — a norm domain has no sheet prefix and its instances name no workbook and no sheet, which is checked both ways) and, since v0.28, which kind of **`action`** it is in SIA 260's terms — `permanent` (G: `dead-load`) or `variable` (Q: `snow-load`, `wind-load`) — and not a workbook, since its sheets may sit in several. `action` is a constant of the domain module (`ACTION`, beside `ENGINE`), exported on the domain and validated against those two values: it is what Woodcore groups the loads by (§10quater), and what a load combination will pick its factors by (§3.5), so it lives where the load is calculated rather than in either of them.

- An **instance** is one sheet carrying that prefix, in any of the project's load workbooks: `SL-Dach1`, `SL`, `EL+AL-Fassade`, `WL-Velo`, ... One sheet, one case of the calculation. For a domain read from a norm table, it is one row of that table instead — a category of Nutzfläche, `A1` … `H` (§3.3septies) — addressed exactly the same way.

That is the whole mechanism, and it exists because the workbook itself says so: its `Objekt` sheet instructs the engineer that *"Blätter können kopiert werden"* and that *"Bauteilname wird von Blattname übernommen"*. So **copying a sheet in Excel adds that case to the export** — no Python edit, no id to invent. `calc/registry.py` discovers the sheets. ⚠️ **`Sections/004-einwirkungen.typ` names the cases it prints**, each at the level the report wants it — the engineer's choice (v0.79, periodic audit 260916, B4), where v0.18 wrote an `ids(domain)` loop — so a copied sheet reaches the page when it is named there, or through that loop; `EL+AL-Wand` is exported and not printed today.

**The load workbooks are found the same way, by name (v0.26).** Every file directly in the project folder whose name contains `Belastungsannahmen` and ends in `.xlsm` or `.xlsx` is a load workbook — `Belastungsannahmen.xlsm`, an office's numbered `02_Belastungsannahmen.xlsm`, a second file for an annex — and every one of them is read; `registry.py` states the pattern (`WORKBOOK_NAME`, `WORKBOOK_SUFFIXES`), `io_excel.find_workbooks()` applies it. Both tests ignore case, as Windows does. Excel's `~$` lock files are skipped (they match the pattern while the workbook is open, which is when the engineer builds), subfolders are not searched (an archived copy must not become a second set of loads), and the files are taken in file-name order, which is therefore the order their cases come out in: all of `02_...`'s sheets, then all of `Belastungsannahmen.xlsm`'s, each in tab order. Which files were picked up is printed on every export. ⚠️ **Finding none stops the export only where the last one read a workbook that is gone** (v0.89.1, the engineer's rule; `registry.open_workbooks`): `data/project.json` names every workbook an export read, and where it names a load workbook and the folder holds none, the export stops naming it — renamed out of the pattern, moved into a subfolder or not synced yet, it would otherwise look exactly like a project without loads, and the export would write the report's loads away. A project no export has read one for — a new project — is exported **without loads** — with a warning until v0.116, and since v0.117 with one line of information on stdout (`export_all: no load workbook in … -- loads: none`), which the window does not show as a warning (the engineer: «cette erreur ne doit plus être affichée»; the loads will one day be computed by Woodcore itself, §13): the three sheet domains carry no case, the live loads of SIA 261 Tabelle 8 are all there, and positions, plans and connectors go through. A project that deliberately gave up its loads is exported without them once its `data/project.json` is deleted, which the stop names. Until v0.89.1 finding none was a blocking error whatever the project.

- **An instance entered in Woodcore (schema 1.5, issues #35-#37, D-04)** is computed in Python from a source of the project, `Woodcore-Datei/loads/{dead,snow,wind}/<id>.json`, by the module `registry.SOURCE_MODULES` names for its domain (`dead_load_source`, `snow_source`, `wind_source`), and joins the sheets' instances under the same domain, after them, in file-name order. It carries **`engine: "python"`** -- its own, where the domain's was `excel` (the snow's and the wind's are `python` too since v0.120, a sheet's inputs being computed by the same code, docs/domain/loads.md §3.3bis) -- and **`source_file`** (`loads/snow/SN-01.json`), and no `workbook` nor `sheet`; `validation.validate_calculations_business` holds the three together, and an instance of another engine than its domain's with no `source_file` is refused. **An id a sheet and a source both carry is refused**, naming the source and the workbook. A domain whose cases are all sources is not warned about for having no sheet. It may carry **`figures`** -- `[{file, title, level, width}]`, the SVG under `data/calculations/` (in a project laid out by folders, since v0.119, `Permanent-loads/Exports/Figures/`, named in the JSON from the Typst root -- issue #64, docs/architecture/layout.md §11) (`registry.write_files`, which removes the drawings no case carries any more) --, printed by `show-calc` above its tables from their own level. `schema_version` is 1.5; an export at 1.4 is still read. `registry.export(here)` rebuilds `calculations.json` alone -- what a tab of loads runs when a case is saved.

- **`workbook`** and **`sheet`**: the file and the sheet it was read from. On the instance, not the domain, since one domain's sheets may come from several workbooks; every var's `source` names them too (`excel:02_Belastungsannahmen.xlsm!SL!H17`). Both are absent from an instance of a norm domain, which has no file and no sheet behind it — a required field there would be an empty string pretending to be one (§3.3septies).

```json
{
  "schema_version": "1.4",
  "domains": {
    "snow-load": {
      "label": "Schneelast", "action": "variable",
      "engine": "excel",
      "sheet_prefix": "SL",
      "instances": {
        "SL-Dach1": {
          "workbook": "Belastungsannahmen.xlsm",
          "sheet": "SL-Dach1",
          "results": ["q_k11"],
          "vars": {
            "s_k": {"value": 1.729, "unit": "kN/m²", "symbol": "s_k",
                    "label": "Charakteristischer Wert auf horizontalem Gelände",
                    "level": 2, "norm": "SIA 261", "norm_ref": "5.2.6",
                    "source": "excel:Belastungsannahmen.xlsm!SL-Dach1!H17"},
            "ce":  {"value": 1.0, "unit": "", "symbol": "C_e",
                    "label": "Expositionsbeiwert", "level": 3,
                    "norm": "SIA 261", "norm_ref": "5.2.2",
                    "source": "excel:Belastungsannahmen.xlsm!SL-Dach1!H14",
                    "description": "Gewählte Windexposition: normale Windexposition.",
                    "choices": [
                      {"value": 1.0, "desc": "normale Windexposition"},
                      {"value": 0.8, "desc": "dem Wind stark ausgesetzte Lage"},
                      {"value": 1.2, "desc": "vor Wind geschützte Lage"}
                    ]}
          },
          "steps": [
            {"name": "Charakteristische Schneelast", "level": 1,
             "result": "q_k11", "uses": ["mu_11", "ce", "ct", "s_k", "abgleiten"],
             "formula": "q_(k,11) = max(mu_11, 0.8) dot C_e dot C_T dot s_k",
             "norm": "SIA 261", "norm_ref": "5.2.2"}
          ],
          "checks": []
        },
        "SL-Dach2": {"results": ["q_k11", "q_k12"], "...": "..."}
      }
    },
    "dead-load": {
      "label": "Eigen- und Auflasten", "action": "permanent", "engine": "python",
      "sheet_prefix": "EL+AL",
      "instances": {"EL+AL-Fassade": {"...": "..."}}
    },
    "live-load": {
      "label": "Nutzlasten", "action": "variable", "engine": "norm",
      "sheet_prefix": "",
      "instances": {"A1": {"results": ["q_k", "Q_k"], "...": "..."}}
    }
  }
}
```

- Two domains must not claim the same sheet: a prefix collision is a blocking export error, since one sheet is one calculation.

- ⚠️ *Retired by the spec 2026-10-21-commandes-typst-refonte (lot 19): `show-calc` -- write #include domain-file(kind, id) -- a load ("snow-load", "wind-load", "dead-load", "live-load"), a connector, a polar moment ("connection"), a script: its file, written out by the export, printed where the section includes it. What follows describes it as it was.* Two workbooks must not both hold a sheet of the same name: the sheet name *is* the instance id the report addresses (`show-calc("snow-load", "SL-Dach1")`), so it has to be unique across every load workbook at once. That is a blocking export error naming both files — renaming one sheet is the fix — rather than one of the two silently winning.

- A sheet is read against **its own workbook's** lookup tables — the dead load's material library, the `Dropdowns` sheet — never another's, and a workbook without a single sheet of a domain is not asked for that domain's tables at all.

- A domain that finds no sheet in any workbook is a **warning**, not an error — a project may genuinely have no facade, or no snow.
