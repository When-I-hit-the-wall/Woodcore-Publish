# Building a tab of calculation

> How a tab of calculation is built on the common base -- the snow first, the wind, the live loads, the seismic action and the member checks after it -- and what its domain declares (spec `docs/requirements/completed/2026-10-22-onglet-neige-type.md`, issue #94; `docs/decisions.md`, «a tab of calculation is described, never copied»).

## 10quater. The tab of calculation, a described tab (v0.124)

The engineer, 22.10.2026: «la façon dont l'onglet Neige est construit doit être un onglet type. Le vent, le séisme, les charges permanentes, les charges utiles et les vérifications en reprendront le fonctionnement. Un futur onglet ne doit pas réinventer sa base : il repart d'une base saine, déjà écrite et documentée, et n'apporte que ce qui est propre à son domaine.» A tab of calculation is therefore **described by its domain and drawn by one base**: adding the wind is writing its declaration and its domain's functions, never copying a widget.

### What the base does once, for every tab of calculation

| Part | Where | What |
|---|---|---|
| The frame | `calc/tools/load_tab.py` `LoadTab` (and `source_editor.SourceEditorTab` under it) | the list of the cases in folders with «Archives», «Nouveau» · «Dupliquer» · «Supprimer», Nom · Description · ID, «Enregistrer», the two views «Calcul» and «Affichage» (`views.CALC_VIEWS`), a number linked to a variable of the export (`linked`, issue #42) |
| The form | `calc/tools/calc_tab.py` `DeclaredTabMixin`, `calc/tools/calc_fields.py` | the domain's sections as cards, each datum with its words and its ⓘ; the kinds of field: `number` (with its unit; linked where the domain's `LINKABLE` says), `buttons` that say what they are worth with a value of the engineer's own beside them (`free_id`, `free_key`), `tiles` each a drawing, `checkbox`, `select`, `custom` (a widget the tab builds: `custom_field`); the rows a source shows (`visible_fields`); a message's click giving its field the focus and a flash |
| The norm | `calc/tools/norm_bubble.py`, `calc/tools/norm_reader.py`, `calc/tools/excerpt_image.py`, `calc/norms/excerpts.py`, `calc/norms/library.py` | hover a ⓘ ~350 ms: a bubble with the norm, its edition, the clause and the page, the words first and the image cut out of the shipped PDF under them (a tile's bubble the image alone); it stays while the pointer is on the ⓘ or on it, opens under the ⓘ, above where there is no room, scrolls where neither holds it (`place`); click: pinned as a module; Ctrl+click: the chapter in Woodcore's reader at the clause, framed, or a map's site (`map.url`); the window's language, German where the norm has no edition in it |
| The right pane | `calc/tools/module_pane.py` | modules reordered by drag and drop on their header, folded with ▾/▸ to a summary, an excerpt unpinned with ×, ⧉ a minimal window zoomed by Ctrl+wheel; the order and the folding kept per tab on this machine (`layout_store.get_state/put_state`), the pins the session's (kept through a window rebuilt) |
| The modules | `calc/tools/calc_tab.py` | «État du calcul» (red: what stops the calculation; orange: what is only said; green: every input there, the calculation made), «Résultats» (what is computed, never an input), the domain's drawing and its interactive chart where it has them, the excerpts pinned under «Résultats» in the order they were pinned, each once |
| «Affichage» | `calc/tools/domain_file_display.py`, `calc/domains/unfold_display.py`, `calc/line_display.py` | the case's file compiled on a page an A4 high, what the report hides shown pale and marked «masquée» (`show-masked`); one card: the file, the command to copy (`#include domain-file(kind, id)`), the domain's level (auto, 1, 2, 3: `#domain(…, level: n)`), «Éléments du fichier» with each line's 0 1 2 3 (the one it follows dotted), a line's arguments -- those of its display, read from `lib/display-presets.json` --, the line as written and the whole file (read only); every change written into the file at once and kept by the exports |
| The words | `calc/tools/calc_tab_words.py` (`ct_`) | the base's, in three languages |

### What a domain brings, without Qt (`calc/domains/contracts.py` `CalcTabDomain`)

- **`declaration()`** -- a `Declaration(prefix, norm, sections, fields)`: the prefix of its tab's words (`sn_`), the norm file its excerpts are read from (`sia261-2020-5.2-schnee`), its sections in order, each `(id, field keys)`, and its `Field`s: key, kind, unit, choices (`Choice(id, word, value, excerpts)`: a word of the glossary, or of the tab where it begins with the prefix), the excerpts its ⓘ shows, a number's range, decimals and step, whether it may follow a variable, and for buttons the free value's id and key.
- **`visible_fields(src)`**, **`messages(src)`** -- `Message(code, field, severity, params)`, an `error` per field the calculation cannot read and an `info` for what is only said, every threshold and clause the norm file's --, **`results(instance)`** -- the values computed, never an input --, and its source's functions: `new_source`, `check_source`, `read_source`, `build_instance`, `stamp_version`, `LINKABLE`, `FOLDER`, `DOMAIN`, `ID_PATTERN`.
- Optionally **`figure_svg(src, lang=None)`** (the drawing the tab shows and the export prints: one code, no word in the report's), **`tile_svg(choice)`**, **`chart(src)`** (series, marks; the base reads a value under the pointer and knows nothing of what they mean).
- **The excerpts of its norm** in the norm file it reads (`calc/norms/<norm>.json`): `editions` (each language's PDF in `norm-library/` and the chapter Ctrl+click opens) and `excerpts` (per id: kind, and per edition the clause as it names it, the page, the box in PDF points from the top-left corner, the words copied once and held to the PDF by a test), `map` where it opens a site.
- **The generator of its file** (`calc/domains/unfold.py` `GENERATORS`), the figure at its head through `unfold.figure_line`.

The tab itself is a few lines: `class SnowTab(calc_tab.DeclaredTabMixin, load_tab.LoadTab)` naming its key, its module, its ID prefix and its list's words, a row of `tab_registry.TABS`, and its words module (`snow_tab_words.py`), merged by `woodcore_gui_words.py`. `tests/test_calc_tab_base.py` mounts the base on a domain invented for it (`tests/fake_domain.py`) and finds no word of the snow in the base's code.

### The snow, a complete example

`calc/domains/snow_source.py` declares the building first (L, B: always entered, read by a flat roof for Figur 4), the site (h₀; Δh of Anhang D, whose ⓘ opens 261.sia.ch's snow map at Ctrl+click; C_e's three buttons and a value of the engineer's own; C_T), the roof (five tiles drawn as Figur 3, the slopes, the sliding, a height step). Its messages: the 2000 m of 5.1.4 and the 800 m of 5.3.7 in orange, C_T under 1, a slope of 60° free to slide, a large flat roof, a height step; a field it cannot read in red. Its drawing is the column of Figur 3 of the case's roof (`snow_svg.figure`), its chart Figur 2. See `docs/ui/tab-snow.md`.

### What the others will bring (the architecture review, spec §13)

- **The wind** (`calc/domains/wind_source.py`, 6.2 and the ~50 tables of Annexe C): `select` for the table, a number with a special value (`z` «= h»), results in tables (`instance["tables"]`), excerpts spread over several norm files (`calc/norms/excerpts.py` reads any), the map `layer=wind`. `wind_source.messages` already gives its messages.
- **The permanent loads**: their table of layers is a `custom` field; their drawing is the build-up.
- **The seismic action**: a chart (the spectrum), numbers and lists.
- **The member checks** (`MemberCheckTab`): they keep their own parent and mix `DeclaredTabMixin` in, its demands being `SourceEditorTab`'s; the card «Position» stays a hook of their own; a verdict will be a severity of its own; «Affichage» already sets a `#verify`.
- Until their own issues the permanent loads and the wind keep `LoadTab`'s former frame: a tab takes the new one by mixing the base in (D-25).
