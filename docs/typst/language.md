# The report's language (i18n)

> **Two glossaries, one rule (19.10.2026, spec 2026-10-19-base-saine-nettoyage, G7).** What the **report** prints is in `calc/i18n/` (`strings.json`, `commands.json`, `reference.json`), read by Typst and by Python. What the **window** says is its own: each tab keeps its words beside it, a `STRINGS = {"fr": …, "de": …, "en": …}` table in its module or in a `calc/tools/<tab>_words.py` split out of it, merged into the window's one table by `woodcore_gui_words.py`. Neither copies the other: a word the report prints is never in a `STRINGS`, and a word of the window never in `calc/i18n/`. `tests/test_i18n.py` holds both to the three languages and to the keys the code names.

> Document language vs engine language, the glossary, figures per language.
>
> Moved verbatim from CLAUDE.md (§4bis) on 2026-10-07. The § numbers are kept as stable anchors: `docs/README.md` maps every § to its file.

## 4bis. The report's language (v0.52; two settings since v0.54)

A report is written in **German, French or English**, and **two settings decide what that means**, because there are two questions and v0.52 answered them with one command. They are deliberately separate, and the separation is the whole of the design (§13):

| | where | what it governs |
|---|---|---|
| **The document's language** | `config.typ`, `doc-lang`/`doc-region`, written by hand | what **Typst itself** writes: «Abbildung»/«Fig.», «Tabelle»/«Tableau», the outline's title, the hyphenation patterns, the quotation marks |
| **The engine's language** | `#set-report-language(...)` in `Statischer Rapport.typ` | what **the glossary** translates: the labels of the calculations, the titles and notes of the tables, the captions of the figures, the STE legend of a plan |
| **Your own words** | `Sections/*.typ`, the title page | nothing touches them: the headings, the title, the prose, a `title:` or a `caption:` |

```typ
// Statischer Bericht (typst)/config.typ -- the language Typst itself works in
#let doc-lang = "de"        // "de", "fr", "en"
#let doc-region = "CH"
```

```typ
// Statischer Bericht (typst)/Statischer Rapport.typ -- the language the engine prints in
#set-report-language(sys.inputs.at("lang", default: "de"))    // "de", "fr" or "en"
```

`--input lang=fr` forces the **engine's** language for one run, as `--input level=` forces the base level — `woodcore-cli export --lang fr`, or Woodcore's export menu (§12). The document's own language is not a build flag at all: it is a property of the report, edited in `config.typ` like the paper size beside it. A report written in French therefore wants both edited, and that is the point — each one controls a different thing, and v0.52's single command moved them together whether or not that was wanted.

**What follows the language, and what does not.** The line between them is the engineer's own rule:

| Follows the language | Stays exactly as entered |
|---|---|
| What the engine prints itself: «Massgebend», «Feuchteklasse», «Positionsplan», «Mst. ca. 1:50», «Statisches System», «mit», OK/FAILED, the titles and notes of the tables `show-polar-moment` builds, its footnotes | Everything the workbook alone names: descriptions, text values («Flachdach», «Ja»), material and Ebene names, sheet names |
| The labels, step names, group labels, table titles, column headings and notes Python composes and the export carries | The positions and connectors of `Positionen.xlsx`, their types, materials and dimensions |
| The wording of SIA 261's Tabelle 8 — the categories, the norm's examples, the five footnotes — in the French edition's own words | The citation of a norm or of a document: `SIA 261 §5.2.6`, bauforumstahl's handbook title |
| The legend and the notes of the figures Python draws, and the STE legend of a position plan | The prose of `Sections/*.typ`, and any `title:` or `caption:` a call is given |
| A value the **norm** names, even though it reaches the engine from a workbook cell: the category of Nutzfläche, the four Geländekategorien of SIA 261's Tabelle 4 («IV grossflächige Stadtgebiete» → *IV zone urbaine étendue*) | The names of the project's own things: buildings, plans, static models, connections |
| | **The headings of `Sections/` and the document's title**, written by hand in the language the report is written in (v0.54) |
| | **Typst's own localisation** — «Abbildung»/«Fig.», «Tabelle»/«Tableau», the outline's title, the hyphenation — which follows `config.typ`'s `doc-lang`, not this command (v0.54) |
| | The names of commands, arguments and Python variables, and every error message: those are English, and stay English (§1) |

**A position's type follows the language of the project, and its id does not** (v0.116, §7). The type of a position is stored once, as the STE key it is entered under, in German, as it always was (`Träger`, `Stütze`); what a window or a page shows is that type **in the language it is read in**: the Positions tab in the **project's** language (`positions_store.project_language()`: `config.typ`'s `doc-lang`, else the report's language, else the window's), the report, `#member`'s line, `calc-block`'s header, the list of the positions and the plan's legends in the language of the **compiled document**, through the glossary — sixteen STE type names are terms of `calc/i18n/strings.json`, German keyed by itself. A type the engineer typed freely, which is no STE key, stays as typed, and a translated name typed in the tab is read back as its key. ⚠️ **The id keeps the STE letter**: a French column is `S001` and not `P001`, the letter being the key the plan's symbol and the colour of the list's ID cell are read from. German output is unchanged to the byte. Accepted limit: the wordings the glossary gives to the three kinds of support and to the two of Abfangung are the implementer's own, to be read over (§14).

**A value typed into Excel is not automatically the engineer's** (v0.54). The glossary decides, as it always has, and what it carries is what the *norm* names: «IV grossflächige Stadtgebiete» is a cell of the workbook's `Dropdowns` sheet, but it is also row IV of SIA 261's Tabelle 4, so it is the norm's word and the norm's own French — *IV zone urbaine étendue* — is what a French report prints. «Flachdach» and «Ja» are named by the workbook and by nothing else, so they stay. The rule reads the same from either side: **a string is the engine's word if the glossary carries it, and the engineer's if it does not** — and what belongs in the glossary is what a norm gives a word for.

**Prose may carry math, between dollars** (v0.54). A description, a note or a choice's text is a plain string in the data, so a symbol in one used to be spelt out in letters — `cred`, `cpe`, `zg` — and read as three letters rather than as c with a subscript. A sentence the engine prints is now split on `$`, and what stands between a pair is set as **Typst math source**, exactly as a `symbol` or a `formula` already is (§3.1, §6bis): `"$c_\"red\"$ ist der Reduktionsfaktor"` prints c_red. `render-prose` in `lib/calc-engine.typ` does it wherever a sentence from the data is printed — a table's `title`, `note` and a text cell carrying a dollar (v0.77), a var's `description` and each of its `choices` (the value and the text beside it), a step's `description`, the footnote of a live load, a connector's warnings, and the description `#var` and `#var-unit` print (§10quinquies).

Splitting on the dollar interprets **nothing else** — not `_`, not `#`, not `*` — which is what makes it safe on a description typed in Excel, and **an unpaired `$` leaves the sentence exactly as it is**, so a price written «5$ pro Stück» is not swallowed into math mode. The German source and all three glossary variants carry the same spans, the German being the key.

**What v0.79 added** (periodic audit 260916). A template may name in **`translate`** the holes that carry a norm's word — «Gewählte Windexposition: {exposure}.» carries SIA 261's exposure — and both readers pass those through the terms, a sheet's name in another hole left as it is (B11). A table's **`note` may be a list** of sentences, each a term or a template, translated one by one and joined: one string whose hole held every piece's provenance came out half German (B12). An **annex** is cited «SIA 261 Anhang D», «annexe D», «Annex D», without the § a clause takes, «Anhang» being a term (`norm-text`, B15). The engine's own **colon and semicolon** joints take French's narrow no-break space (`colon-str`, `semicolon-str`), as `t-label` already did for a glossary word (A 3-12). And **one word per notion**, the norm's (B10, B14): «moyen d'assemblage» / «fastener» for a Verbindungsmittel, in the window as in the report; «charge concentrée» / «concentrated load» for an Einzellast (SIA 261 FR); «poids propre non-structural» / «non-structural self-weight» for an Auflast (SIA 261 Tabelle 80, p. 131); «Dowel» for a Stabdübel (EN 1995-1-1 8.6).

Numbers do not follow the language: the decimal separator is a point in all three, as `calc/norms/sia261-2020-tab08-nutzlasten.json` already says of its own transcription. A comma would have to be taught to `fmt-decimals` and to the substituted formulas, where Typst's math mode already reads a comma as punctuation and `f_(m,k)` uses one.

**A negative number is printed with a minus sign, U+2212 «−», and never a hyphen** (v0.87, the engineer: «un signe moins doit être affiché»), in every language. The sign is changed at the point a number becomes text on the page, and nowhere upstream: `signed-text` in `lib/calc-engine.typ` (one helper, which `lib/formula.typ` imports) in `fmt-number` — every value row, table cell and the polar moment's tables —, `value-text` (the answer of a numbers line), a connector's Ø and L and the connection legend's note, and `#var`, `#eq`, `#val`, `#verify` through `formula-number`. ⚠️ **`fmt-decimals` and `fmt-magnitude` keep the hyphen on purpose**: what they return is also Typst math source, which sets a minus of its own for an unquoted `-0.25`, the value the registry holds, and SVG coordinates a parser reads back. A sentence the data carries goes through **`prose-minus`**, in `render-prose` and a table's text cells: a hyphen standing where a number's sign stands — at the start, or after a space, a bracket, `=`, `:`, `;`, `,` or `/`, and right before a digit — is a minus, so «Δh = -200 m» out of the workbook's Dropdowns sheet prints «−200 m», while «Holz-Holz», «EL+AL-Dach1» and «EN 1995-1-1» keep theirs. ⚠️ It therefore also rewrites such a hyphen in the engineer's own Excel text, which is the rule's accepted reach. The figures Python draws follow the same rule (`statics.figure_number`, `schema.figure_number`; Arial's minus advance, 1196/2048, added to `schema_svg`'s width table), a coordinate or a cell Woodcore reads back keeping `fmt_number`'s hyphen.

### One glossary, read by both sides

`calc/i18n/strings.json` is to the engine's words what `norms/` is to the norm's values: the one place they are written down. It is read by **Python** (`calc/i18n/strings.py`, for the text a figure has to be drawn to measure) and by **Typst** (`lib/i18n.typ`, for everything the report prints), so a word both sides say — the note under a connection's figure, which Python sizes and Typst fills in — is written once. It is hand-written; no generator touches it.

Three blocks, and the middle one is why **`data/calculations.json` did not change by one byte**:

- **`terms`** — the German the export already carries, **keyed by itself**, the way gettext keys by its source string: `"Bezugshöhe": {"fr": "Hauteur de référence", "en": "Reference altitude"}`. So the labels, step names, group labels, table titles, column headings and notes Python composes are translated at the moment they are printed, and neither the schemas, nor `validation.py`, nor Woodcore, nor `build_reference.py` had to learn anything. It is also what draws the line above: `tl` translates a string **only if the glossary carries it**, so a material's name, an Excel description and a value the engineer typed pass through untouched, and the glossary is exactly the list of what counts as the engine's words.
- **`templates`** — the sentences with a hole in them: `"Im Blatt {sheet} wählbare Lastmodelle: {models}."`, `"Maximale globale Windkraft, Bezugsfläche {area}"`, `"Winkel von Element {i} zu Element {j}"`. A sentence with a hole cannot be keyed by its own text, so `tl` matches the German by the **literal segments around the holes** — no regular expression, and a sheet's name cannot confuse it — and re-emits the target language's sentence with the captures put back **by the hole's name**, so a language that orders them differently still comes out right.
- **`engine`** — what the engine prints itself, by a key: `governing`, `moisture_class`, `plan.scale_approx`, the five sentences of a connection figure's legend, the seventeen lines of the STE plan legend (keyed by the `key` `data/plans.json` already carries). 👉 v0.54 removed the sixteen keys v0.52 had put here for the section headings and the document's title (`report.title`, `section.introduction` … `section.references`): those words are the engineer's now, so a key for them would be a translation nothing may apply.

`strings.py` checks the file before a word is taken out of it: a language missing from an entry, an empty string, a template whose holes differ between two languages, a term carrying a German of its own, or a language list other than `LANGUAGES` (which `lib/i18n.typ` asserts again at compile time). `export_all.py` checks it first, whatever the project holds (v0.78), so each stops the export naming the key, exactly as a defective norm table does.

**Where the French and the English come from.** Wherever a norm gives the word, the word is quoted, and each block of the file names its source: SIA 261's French edition (1.2 for the symbols' names, 5 and 6 for snow and wind, **Tabelle 8 word for word from p. 38**, and annex H's Tabelle 80, which gives German → French → English for the terms of chapter 1 — *Nutzlast* → *charge utile* → *live load*); SIA 265's French for timber and connections (table 3 for the moisture class, 6.4 for *prépercé*); SIA 260's French and English editions for *convention d'utilisation* and *base du projet*; STE Compact 02's French for the plan legend; EN 1995-1-1 for the timber terms those do not cover. What no norm gives is a translation and says so: the wording is the engineer's to correct, in that file and nowhere else. 👉 Since v0.53 every edition named here is a PDF in the reference library (§11bis), so a word is checked against the edition it was quoted from rather than against a memory of it.

### In Typst

`lib/i18n.typ` is imported by `lib/calc-engine.typ`, so `commands.typ` re-exports it with the rest and every section file has it (§10bis):

| | |
|---|---|
| `report-language` | the state, default `"de"` |
| `set-report-language(lang)` | the command; an unknown language fails naming the three |
| `report-lang()` | the language in force, inside `context` |
| `t-str(key, ..values)` / `tl-str(text)` | a string, in the report's language — what the engine calls at every print site |
| `t(key, ..values)` / `tl(text)` | the same as content, wrapped in `context` — for a caller in markup rather than inside a show-* function: `#t("governing")`, `#tl(get(v, "label"))`. **Not for a heading** (v0.54): those are the engineer's and are written by hand |
| `t-label(key)` | the word and its colon, set the way each language sets one: French keeps a narrow no-break space before it |
| `t-pattern(key)` | a template with its holes standing, for a sentence whose hole is a piece of *math* (`I_p`, `F_3`): split on the hole and set the math between the halves |
| `t-of(lang, key)` / `tl-of(lang, text)` | the pure lookups the four above are built on, for a caller that states the language itself |

**No signature of the engine changed.** Typst's state can only be read inside `context`, but a plain helper called from within a caller's context reads it too — which is how `number-digits` has always worked (§4) — so `var-row`, `render-table`, `step-rows`, `share-note` and the rest take their language from the air rather than from a new parameter. Four functions were not inside a context and are now (`show-position`, `show-connector`, `connector-summary` through them, and `show-static-model`).

**`config.typ` reads no state at all** (v0.54). v0.52 had it wrap the document in a `context` setting `text(lang:)` from `report-language.final()`, which is what made «Abbildung» and the outline's title follow the engine's language. That import and that `context` are gone, and the file is again what its own header promises — plain `set`/`show` rules and nothing stateful — with `doc-lang`/`doc-region` declared at the top of it and applied in `conf`'s `set text(...)`. Nothing in the document now reads the report language outside `lib/`.

A var whose value is **text rather than a number** is a word, so it goes through the same rule: `value-word` translates the load model's name and the category of Nutzfläche where the glossary carries them (the norm's wording) and leaves «Flachdach» and «Ja» as the workbook wrote them. A **symbol** that is nothing but a quoted word — `"Geländekategorie"`, `"Lastmodell"`, a var whose value is text has no letter to stand for it — follows the language too; `q_k`, `C_e` and `mu` do not, being the norm's own letters in every language.

### The figures

A figure's frame is sized from the width of its own text — `connection_svg` measures its legend's five sentences, `statics_svg` its notes against Arial's own advances — so a French legend does not fit a German frame. Each figure is therefore **drawn once per language**: `data/connections/<id>-de|fr|en.svg`, `data/statics/<id>-de|fr|en.svg`, and the record carries one file each (`figure.files`, and for a static model `figures.<lang>.{file, view, notes}`, since the frame travels with the file). Everything else in those records — the fasteners' places, the arrow sizes, the scale, the size unit, every placed point — is geometry, and the same in all three. Duplication in generated data costs bytes and not a second place to edit, which is the v0.49 argument (§13).

Two things followed from drawing those figures in French: `statics_svg`'s `ARIAL_WIDTHS` gained the accented letters of French, since a width the default guessed would size the frame around a note wrongly; and `connection_svg`'s `font-family` became the one bare family `statics_svg` already used, because QtSvg takes the whole string as a single name — the report writes the same one name into the same figure.

**A position plan needs no second file.** Its SVG carries only position numbers, axis names and lengths, which are data; its legend has been Typst's since v0.39 and is keyed, so `plan-legend` looks each line up by that key and falls back to the text the export drew it with.

### What this does not do

Woodcore's window has had its three languages since v0.28 and keeps them; what it shows of the *data* stays German, as its own comment says, though it now previews a connection and a static model in the window's language. The PDF keeps its name, «Statischer Rapport.pdf»: renaming it per language would desynchronize `woodcore-cli`, Woodcore and Tinymist, which must name the same target (§12). And the ψ factors of SIA 260's Tabelle 2, which a load combination will need, are still not read (§14).

---
