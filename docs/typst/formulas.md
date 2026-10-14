# Variables and formulas written by hand (var, eq, verify)

> The registry, var-domain, val, var-line, units, verify, levels, stacked formulas.
>
> Moved verbatim from CLAUDE.md (§10quinquies) on 2026-10-07. The § numbers are kept as stable anchors: `docs/README.md` maps every § to its file.

## 10quinquies. The variables a report writes by hand — `var`, `eq`, `verify` (v0.60, rebuilt v0.61)

`show-calc` prints what a Python domain already computed, and its guarantee is structural: the numbers line is *derived* from the letters line by substituting the step's own operands, so the two cannot drift (§10bis). That guarantee stops at the edge of `data/`.

A calculation written directly in `Sections/` had to be written **twice** — once as an expression that computes, once as math that displays — and nothing compared them. v0.59's reading found three lines on one page where they had come apart: `M = 1 kN · 0.5 m = 0.25 kNm` for code that said `F * l/2`; `F = 0.275 kNm · 10⁶ / 135 mm = 2.037 kN`, which as printed gives 2037; and a comparison written twice over, ending in a `= R_d` that means nothing.

**v0.60 closed that and was unreadable.** Its `eq` took the formula once and evaluated it, but a variable carried **three** names — the Typst binding `k-dens`, the `where:` key `k_dens`, the printed symbol `k_"dens"` — the three had to agree, nothing checked that they did, and the `where:` repeated the list of operands the formula already named. **v0.61 gives a variable one name.**

```typ
#var("R_k", 7, "kN")
#var("k_dens", 0.806, level: 0)          // stored, not printed
#var("eta_w", 0.8, level: 0)
#var("gamma_M", 1.7)
#var("eta_M", 1)

#eq("R_d", `k_dens dot eta_w / (gamma_M \/ eta_M) dot R_k`,
    style: "bold", norm: "Sherpa", norm-ref: "ETA-12/0197")

#verify(`F_Ed <= R_d`)
```

→ `R_d = k_dens · η_w / (γ_M / η_M) · R_k = 0.806 · 0.8 / (1.7 / 1) · 7 kN = **2.655 kN**`, with the citation in the right-hand column every other formula's sits in (§10).

### The registry

`var-registry` (declared in `lib/calc-engine.typ`, beside `report-level` and `block-scope`) is **one dictionary for the whole document**: `#var` and `#eq` write into it, and `#eq`, `#verify` and `#val` read it back by name. An entry is a **var of the project** (§3.1) — `value`, `unit`, `symbol`, and optionally `description`, `norm`, `norm_ref`, `source` — which is the shape `var-of(...)` already returns, so a value out of Excel, of Python or of a norm table is written down with its provenance intact:

```typ
#var("s_k", var-of("snow-load", "SL-Dach1", "s_k"))
```

That is the one call Woodcore copies for a load's var (§10quater), and it is what ties a hand-written calculation back to the workbook.

⚠️ **`#var` cannot create a Typst binding, and no later version will change that.** Typst gives a function no way to bind a name in its caller's scope: there are no macros, and `eval(scope:)` evaluates in a fresh scope. The name is therefore a **string**, and the registry is where it lives. For the same reason a formula cannot be passed as a bare expression — `dot` and `\/` are math and not code, and an argument is evaluated *before* the call, so `eq` would receive a number and not a structure to print.

**How one command both reads and writes one state.** Each of `var` and `eq` is **two pieces of content**: a `var-registry.update(...)`, then a `context` that reads the registry back and prints. The arithmetic runs inside the update, which is a pure function of the dictionary and needs no state read; the `context` placed after it sees the result. Reading and writing one state from inside one `context` is the thing Typst cannot be asked to do, and this is the way round it — which is also why the domain stack lives *inside* the same dictionary rather than in a state of its own.

👉 **The design rests on one property, and it was verified before anything else was written:** that a `state` updated inside a `grid` cell resolves in reading order. `Sections/005` has two columns that each declare `F`, `l` and `M`, so if it did not, the registry would collapse precisely there. Checked: the left cell sees a name absent, the right cell sees what the left wrote, and after the grid everything is there, with no layout-convergence warning.

### The names

A key is **letters, digits and `_`** — `R_k`, `k_dens`, `F_Ed`, `n_v`. The symbol printed is derived from it by `key-symbol` (§3.1's own rule: a multi-letter subscript that is not a Greek name is quoted), or given as an optional **second positional argument** for a symbol a formula could not spell: `#var("q_k11", "q_(k,11)", 1.729, "kN/m²")`. A var object handed to `#var` brings its own symbol, so the export's spelling is kept without being retyped. ⚠️ **Every key is accepted** (v0.87, second half, the engineer: «Une clé comme M2 reste refusée»), which reverses v0.79's refusal (periodic audit 260916, B19 and AUD-7-425): until then, without a symbol given, the part before a key's first `_` had to be one letter or a Greek name, and `#eq("M2", …)` stopped saying to write `M_2` or to give the printed symbol as the second argument — a refusal that had replaced a failure deep inside math with nothing to say which line. `key-symbol` now sends such a key through `quoted-words`, the reader of a symbol written by hand (below): `M2` prints M then 2, as `gamma_(M1)` prints M and 1, `FEd` and `Mx` one upright word, `Ed_max` as `"Ed"_"max"`; a key that starts with one letter or a Greek name — `R_k`, `k_dens`, `gamma_M` — comes out exactly as it always did. M with the subscript 2 is written `M_2`. In a formula's letters line **`atom-symbol`** groups a symbol of several atoms into one (`class("normal", …)`), so `M2 / a` sets M2 over a and not M times 2/a — the substituted operand's own rule, applied to its symbol; and a math function named without being called — the «mid» of `M_mid` — is quoted, where it printed as raw code. **Still refused**: a `-` (below); a key starting with `_`, which math reads as a subscript of nothing, unless the printed symbol is given; and a key a formula reads as an operation — `dot`, `max`, `sqrt`, `ln` and the rest of `formula-functions` — which would be substituted into `max(a, b)` and stop the formula on «cannot be computed» with nothing to say why.

**A symbol written by hand may carry its words unquoted** (v0.87, `quoted-words`): before a symbol of `#var`, `#eq` or `#val` is evaluated, every run of letters **`dictionary(math)` does not know** is quoted, so `#eq("G_1_Ed", "G_(1,Ed)", …)` works where `"G_(1,\"Ed\")"` had to be typed, and `W_(y,erf)` likewise. A letter followed by digits becomes a letter and a number — `gamma_(M1)` is read `gamma_(M 1)`, an italic M and an upright 1. A name math knows keeps its meaning — `alpha`, `dot`, `max`, `sqrt`, `arrow.r` — quoted text, `#` code and numbers are left alone, and a symbol already right comes back unchanged, so the rule is idempotent and no symbol of the export moved. ⚠️ **Accepted price**: a word that *is* a name of math is read as that name — `c_(pi)` prints c_π, not c with the subscript «pi» — and `M1` is split into M and 1; a subscript meant as one upright word is written with its quotes, as before (§13).

**A `*` is a multiplication** (v0.87, `star-as-dot`): in the formula of `#eq` and the relation of `#verify` a `*` is read as `dot`, evaluated as one and printed `·` in the letters line and in the numbers line — `` #eq("G_1_Ed", "G_(1,Ed)", `1.35 * g_k`) ``. A `*` inside a quoted span, after a backslash, or as an attachment — `F^*`, `F_*` — is a star and is left as it is. ⚠️ The engineer had tried `show math.star: $dot$` in his `config.typ` first, and it cannot do this: a show rule works on content, and a formula here is a **string** until `eq` evaluates it, so the rule never reached `#eq`. It is read in the formula, where the string is. ⚠️ **In math written by hand between dollars, a `*` stays Typst's asterisk, on purpose** (v0.87, second half): a `show math.star` rule turning it into a dot would reach the engine's own math as well — the `F^*` of `show-polar-moment`'s most unfavourable superposition would print F· — so none was added to the engine or to the template's `config.typ`, and a product written in `$…$` is written with `dot`.

⚠️ **Never a `-` in a key.** A formula is read by substituting each known name for a token *before* it is tokenized, so a key `R-k` would win over the subtraction: in a formula that also names `R` and `k`, `R-k` would silently stop meaning "R minus k". Nothing downstream could detect that, so it is refused at the door.

Only **whole words** are substituted, longest key first, and **never inside quotes** (v0.117, issue #32). Without the word boundary the key `n` would rewrite the `n` inside `ln(x)` and `l` the `l` of `log`; without the longest-first rule `F` would eat the `F` of `F_Ed`; and without the quotes skipped a variable named `m` rewrote the "m" of `(3 "m")`, the line dying on «cannot be computed» — the family of v0.86's defect, where the key `N` rewrote the "N" of "21 N/mm²" at level 3. A quoted span — a literal's unit, a text — is copied whole by `replace-word`, by `skip-quoted`, the tokenizer's own rule (an escaped quote does not end it, a quote left open runs to the end of the formula); every substitution goes through it (the operands found, the values computed, the symbols displayed at level 2 and 3), and `unknown-names` blanks the quoted spans by the same rule where it used a regex that stopped at an escaped quote. `calc/units.py`, the Python twin the «Formules» tab computes with, does the same (`_replace_word`, `_blank_quoted`). So a key that reads as a unit — `m`, `N`, `kN`, `mm`, `s` — is a key like any other, and the «Formules» tab keeps it as the engineer typed it, where until then it made `m` into `m_1`. A word left standing once every known name has been taken out is a name the report never declared, and it stops the compile listing the names it could have used — unless `value:` is given, which says the formula is there to be displayed and not evaluated, its `integral` and `dif` then being expected rather than mistaken.

### `var-domain` — a set of names, not a scope that unwinds

```typ
#grid(columns: (1fr, 1fr),
  var-domain("S10 - 0.55 kN Ende")[ #var("F", 0.55, "kN") #eq("M", `F dot l`) ],
  var-domain("S10 - 1 kN Mitte")[ #var("F", 1, "kN") #eq("M", `F dot l/2`) ],
)
Das massgebende Moment beträgt #val("M", domain: "S10 - 0.55 kN Ende").
```

A domain is a **key** in the registry and is never popped — only the current-domain marker is — so what a column wrote is still readable further down the page. That is what tells it from a scope that unwinds, and it is the whole reason it exists: the engineer asked for two columns kept apart *and* reusable afterwards.

A name resolves in the **innermost domain first, then in the default one**, which is what lets `R_d`, declared at the level of a section, be named inside every column.

👉 A *domain* here is a set of names in the report. It has nothing to do with a **calculation domain** (§3.3), which is a kind of calculation — `snow-load`, `dead-load` — whose instances are Excel sheets. The word is the engineer's; the collision is stated wherever it could mislead. Since v0.80 `val`'s own `domain:` takes both, and tells them apart by their shape: a **string** is a domain of the report, a **pair** is a calculation and its instance.

### A domain written in Woodcore's «Formules» tab — `#include "/Formules/<id>.typ"` (v0.117, issue #15)

The engineer, 08.10.2026: «à chaque fois qu'il y ait des calculs, ils soient compris dans un domaine afin de pouvoir appeler ces domaines à d'autres endroits du rapport». A calculation written in the «Formules» tab (docs/ui/window.md) is **one domain, one file**: `<Typst root>/Formules/<id>.typ`, a `#var-domain("<id>", title: "<name>")[…]` holding its `#var`, `#eq`, `#verify`, `#val` and `#var-unit` and, between them, the engineer's own Typst -- a title, a sentence, a formula --, between one tag `// woodcore:object formula-domain domain` (calc/domains/formula_domain.py). The file is the source of truth: the tab reads and writes it, VS Code edits it, and **a report prints it where it stands with Typst's own `#include`**:

```typ
= Poutre P1
#include "/Formules/poutre-p1.typ"      // its title a heading under «Poutre P1», each command at its own level
La poutre est vérifiée avec #val("M_d", domain: "poutre-p1").
```

**The id is the file's name, and the name is a title** (issue #15, the engineer: «L'id du domaine est le nom de son fichier … pour qu'un renommage du domaine ne casse pas les appels»). `#var-domain` is given the id, so `#val(key, domain: "<id>")` reads a value whatever the domain is called; the name the tab shows is `title:`, which `var-domain` prints as a heading one level below the heading before it (level 1 where there is none). A file whose `#var-domain` names another id than its file -- copied, renamed in the explorer -- is `hand_edited` and written back under its own; two files declaring one `#var-domain` stop the export. An id changed in the tab renames the file; the lines that cite the old one are listed, not rewritten.

**No level of the domain's own** (issue #15, REVERSING v0.117's `#show-formula(name, level:)`, docs/decisions.md): each command prints at the `level:` it states, or the report's; `--input uniform=N` still wins. `include` reads the file from the Typst root, `/Formules/<id>.typ`, which is the project's own folder in three documents and the report's in a report alone: every document reaches it, and nothing is copied. A domain included twice declares its values twice, the second over the first. A title typed as free text (`= …`) in the domain takes the including section's heading offset like any heading of an included file.

**The engineer's own Typst between the commands** is printed as typed and never computed. What Typst would compute and Woodcore's Python would not -- a `#var`, `#eq`, `#var-unit` or `#verify` written inside a text rather than as a block -- is refused by the tab, and makes a file written so by hand unreadable; `#val` in a sentence is text, as is anything in a raw block, an equation's `#`, or a comment (formula_domain.split_items reads the body with typst_paths' lexer, never a regex). The commonest such text is a command followed by something on its own line -- `#var("b", 208, "mm") ;` --: it is refused as `text_trailing`, the message naming the line and what follows the call (the `;`), since a command alone on its line is a block and anything after it makes the line a text (v0.117, 2026-10-11).

**A file is never written over once it changed on the disk** (v0.117, 2026-10-11). The tab holds the domain as it read it; a save -- a block validated, an option, a text, a rename -- first compares the file on the disk with the text it read (`formula_domain.check_unchanged`) and, where VS Code, another Woodcore or an engine synced changed it meanwhile, writes nothing, says so (`changed_on_disk`, a warning notice even while saving without a question) and reads the domain again as the file now is. Until then the tab's older copy was written over the file, and the lines written elsewhere were silently dropped. A save whose index (`data/formulas.json`) another file of `Formules/` stops -- unreadable, or a second `#var-domain` of one id -- keeps the file written and says why the index was not (`Domain.index_problem`, the notice `fm_index_refused`), never an «Erreur inattendue».

**A blank line beside a command is a paragraph, and is kept** (issue #40, D-05, D-07). A command stands on a line of its own in the file, and Typst reads a line break as a space: a text line, a command printed inline and the next text line are one sentence, a blank line between them a new paragraph. `formula_domain.tidy_items` keeps one blank line, at most, at the head of a text that follows a command and at the tail of one a command follows, and an empty text between two commands; two blank lines are one (the file is then `hand_edited`), and blank lines at the start or the end of the body are none. Until issue #40 every blank line beside a command was dropped, and two paragraphs written by hand ran into one at the next save. A file the tab wrote before has none and reads back to its own bytes. `formula_domain.plain_spans` names the lines that begin in plain markup, which the «Formules» tab reads to refuse a pill dropped inside an equation, a raw block or a call (calc/domains/formula_layout.py).

**`data/formulas.json`** (schema `formulas` 2.0) is the index Woodcore writes at every save of the tab and at every export -- each domain by its id, with its title and its file. Typst no longer reads it; the «Variables» tab lists the domains from it, and the export checks the files through it.

### `val` — one value, printed, wherever it comes from (v0.80)

Four commands printed one value until v0.80: `val` read a name out of the registry, `fmt` formatted a var object or a bare number, `inline-value` read one var of the export, and `live-load` was the shorthand for one of the two values of a Nutzfläche. They were one command's worth of work spread over four, and three of them are gone (§13). What `val` takes is what they took between them:

```typ
#val("R_d")                                              // a variable of the report          2.655 kN
#val("R_d", type: "expression")                          // with its symbol                   R_d = 2.655 kN
#val("M", domain: "S10 - 0.55 kN Ende")                  // one domain of the report          1.32 kNm
#val("s_k", domain: ("snow-load", "SL"))                 // a value of the export             1.729 kN/m²
#val("q_k", domain: ("live-load", "A1"), type: "unit")   // one part of it                    kN/m²
#val(var-of("snow-load", "SL", "s_k"))                   // a var object, handed over
#val(7, unit: "kN", symbol: "R_k", label: "Sherpa XS")   // a number written here
$ q_d = 1.5 dot #val("q_k", domain: ("live-load", "A1")) $   // inside an equation written by hand
```

**The four parts are the engineer's own words**: `"val"`, `"unit"`, `"val+unit"` (the default) and `"expression"` — `"number"` and `"number+unit"`, which `fmt` also read, are refused, naming the four.

**The levels print the extras and never the value**: level 1 the value as `type:` asks for it, level 2 the label and the `choices` with it, level 3 also the citation — and all of them as **one** footnote, because inline there is no em dash to hang a label on and no column for a citation (§9's own rule for a description and its choices). So a value quoted in a sentence of a checking report carries a footnote unless the call says `level: 1`. ⚠️ Inside `$...$` that marker is set as math and comes out as a plain number rather than a superscript, which is Typst's own doing: a value quoted inside an equation is written `level: 1`.

**`unit:` is display only** — the variable keeps the unit it was declared with, which is what tells `val` from `var-unit` — and **a unit written over is said on the page, in orange, at every level**: «Die Einheit ist für die Darstellung überschrieben: der Wert steht in N statt in kN», with the footnote's **marker** orange too (the engineer's request, v0.80). The orange is `override-colour`, the one Woodcore writes an overridden value in (`OVERRIDE_COLOR`, §10quater), and `tests/test_constants.py` holds the two equal. A unit of another dimension is **refused**: nothing is computed here, so it is a typo at the call site and not a formula disagreeing with its declared unit (v0.63's red line, which is the other case).

⚠️ **The old two-positional form is refused, with the rewrite.** `#val("Ende", "M")` was the v0.61 spelling; it now stops with `write #val("M", domain: "Ende")` rather than being read two ways.

### `#var` and `#eq` are inline, and `note:` says where the extras go (v0.87, v0.117)

**`#var` prints inline by default** (the engineer: «de base, #var doit s'afficher inline … S'il y a deux retours à la ligne, alors ça fait un nouveau paragraphe»): `symbol = value unit` as text, a word of the sentence it stands in, so several calls on consecutive source lines run on in **one paragraph** and a blank line starts another — Typst's own rule for words. `#var-unit` follows `#var`. Until v0.87 each `#var` was a row of a grid, a line of its own.

```typ
Der Querschnitt misst #var("b", 100, "mm") auf #var("h", 200, "mm"), bei #var("k_dens", 0.806).
```

**`note:` says where the label, the description and the citation go**, on `var`, `var-unit`, `eq` and `val` (the engineer: «un argument permet de régler si la note vient en ligne (comme actuellement) ou en note de bas de page», «cela doit être fait sur #var #val #eq»). Two values, anything else refused naming them (`check-note`):

| | `note: "footnote"` | `note: "line"` |
|---|---|---|
| `var`, `var-unit` | **the default**: inline, the three gathered into **one** footnote | a line of its own, as until v0.87: the label after an em dash, the description a footnote, the citation in the right-hand column |
| `eq` | **the default since v0.117** (issue #19): inline, as `#var`, a word of its sentence — `symbol = letters = numbers = answer` as its level asks —, the three in one footnote on the answer | a line of its own, the default until v0.117: the label after the answer, the description a footnote, the citation in the right-hand column — what every check of the engine (`lib/timber.typ`) writes |
| `val` | **the default**, as since v0.80: one footnote | `value — label (description; citation)` on the line, a value in a sentence having no column; the `choices` and the orange line of a unit written over stay a footnote |

Since v0.117 the four share one default (issue #19, the engineer: «#eq s'imprime en ligne par défaut, comme #var depuis v0.87, de sorte qu'il peut suivre un #var sur la même ligne ; note: "line" garde la ligne à part»): `Kraft #var("F", 5, "kN") und #eq("M", `F * 2`) danach.` is one sentence. Until then an `#eq` was a formula on a line of its own, where the right-hand column was there to carry its citation, and `note: "footnote"` only moved its extras into one footnote; it is now inline, `#var`'s own branch (`inline-item`). ⚠️ **Accepted price** (spec 2026-10-10-issues-github-19-20-21, D-07, D-13): every `#eq` written without `note:` — or with `note: "footnote"` — changes its look, consecutive ones running on in one paragraph as `#var`s have since v0.87; the «Formules» tab writes the default too. A line of its own is `note: "line"`, which the engine's checks pass once, through `timber-eq` (`lib/timber.typ`), so no check moved — their pages are the same image as before. Inside a `var-line`, `note:` has no effect — a row's items always take one footnote each. Level 0 leaves no stray space, and the red unit warning sits a space away from the value.

⚠️ **Accepted price**: a report written before v0.87 whose `#var` calls stand on consecutive lines now reads them as one paragraph — the example project's `Sections/005` printed `n_v = 5¹ N = 0 kN V = 24.99 kN M = 15.02 kNm` on one line. A blank line between them, or `note: "line"`, is what a paragraph was (§14).

### `var-line` — a row of declarations (v0.80)

Five `#var` calls were five lines until v0.87, because each printed a row of a grid; since then they run on in a paragraph (above), but with nothing between them. `var-line` sets them on one line, joined the way `show-calc` joins the vars of a `group` (§3.3) — which is where the engineer's question started, and what `Sections/005` now reads:

```typ
#var-line[
  #var("R_k", 7, "kN")
  #var("k_dens", 0.806)
  #var("eta_w", 0.8)
  #var("gamma_M", 1.7)
  #var("eta_M", 1)
]
#eq("R_d", `k_dens dot eta_w / (gamma_M \/ eta_M) dot R_k`, style: "bold", norm: "Sherpa", norm-ref: "ETA-12/0197")
```

→ `R_k = 7 kN; k_dens = 0.806; η_w = 0.8; γ_M = 1.7; η_M = 1`, and the formula under it.

**A container and not an `inline:` flag on each command**, which is the decision worth recording (§13). Three things follow from it, and none of them is available to a flag: **the engine writes the separators**, so a value a level hides takes its separator with it — five hand-typed commas around a hidden value leave four; a `;` is **never typed after a `#var(...)`**, where Typst reads it as the end of the expression and swallows it (the defect `show-calc`'s own note hit in v0.59); and the row carries **one label** before its first value, as a var's `group_label` does, and **one citation** in the right-hand column, which is a grid and cannot be reached from inside a line.

`#var`, `#var-unit`, `#eq`, `#val` and `#verify` each know they are in a row — they read one state, `var-line-state`, in the `context` they already print from — so nothing about a row is passed as an argument. In a row, an item's own label and citation become **one footnote** (the label from level 2, the citation from level 3), since neither has anywhere else to go.

`level:` on the row overrides every item's own: `#var-line(level: 0)[ … ]` declares its variables and prints **nothing at all**, not even the space of an empty line. `sep:` replaces the semicolon — `sep: ","` for a row of dimensions. Anything else in the body is printed as it comes, without a separator.

### `sep:` on `#var`, `#eq` and `#var-unit` — a separator without a row (v0.117)

The engineer typed `#var("b", 208, "mm") ;` to set two values apart on one line; since v0.117 a `;` after a call makes its line a text, which the «Formules» tab refuses (`text_trailing`), and a `var-line` was the only way left — a container the tab does not write. He asked for the separator to be **an argument of the command itself**, as the choice between inline and a line of its own already is (`note:`): «l'option ... serait un argument de var» (spec docs/requirements/active/2026-10-11-argument-sep-var.md).

```typ
#var("b", 208, "mm", sep: ";")
#var("t", 8.5, "mm", sep: ";")
#var("epsilon", 124)
```

prints `b = 208 mm; t = 8.5 mm; ε = 124`. The separator is printed **after** its value and its footnote, glued to it; the space after it is the source's line break, as between any two values written one under the other. It belongs to its value, so a value its level hides takes its separator with it (`check-sep`, `check-sep-row`, `sep-after` in lib/formula.typ) — what a row was made for. `sep: none`, the default, changes nothing. It is **refused**, naming why, with `note: "line"` (a line of its own has no neighbour to separate it from), inside a `var-line` (the row writes its own: `var-line(sep:)`), and when it is not a string. `var-line` stays (D-05): reports use it. The «Formules» tab offers it in «Affichage» as «Séparateur (en ligne)», and its refusal of `#var(...) ;` names `#var(..., sep: ";")` as what to write instead.

### `summary:` — one line of a summary table (v0.99)

`#var(..., summary: true)` and `#eq(..., summary: true)` list the variable in a summary table (`show-load-summary`, `show-line-load-summary`, §10bis) — and **its unit decides which**: `kN/m²` an area load, `kN/m` a line load, any other unit refused naming the two. It is the one way a load the export does not carry reaches a summary, and the export carries no line load at all (§3.3octies).

⚠️ **The mark is not a state of its own.** `summary-mark(d, on, key)` is a **pure function of the variable registry's own dictionary**, called from inside the `var-registry.update` that `var` and `eq` already have — `var-store`'s own shape. Two things follow, and they are why that shape was chosen over one more `state`. v0.85's rule — a state written from inside a `context` is not read back by the folded chain an update function reads (§3.3quinquies) — is satisfied **by construction**: there is no second state that could be emitted in the wrong place. And the **var-domain** the variable belongs to, `var-current(d)`, is readable only *there*: outside an update nothing can read a state at all.

⚠️ **What is recorded is the name, never the value.** An `#eq` computes its answer inside that very update, and so does a `#var` reading a var-domain (§10quinquies, v0.85): the value does not exist yet. It is therefore read where the table is printed — which is also the value the variable *ends up* holding, `#var-unit` having perhaps converted it in between.

⚠️ **And that is why the unit is checked there and not at the call.** A marked `#eq` often states no `unit:` at all, its answer coming out in whatever unit the algebra gives its operands; and `#var-unit` may carry a variable out of its unit on the line after. A check at the call would therefore refuse a variable that is right by the time it is read. The accepted price: a `summary: true` in a report that prints no summary is **never** refused — nothing listed it, and nothing is wrong with the page. And **either** table refuses every mark, whichever unit it is itself gathering: what is wrong is the mark, not the table it is missing from. ⚠️ The refusal does **not** send the engineer to `#var-unit`: a kN is not a kN/m in another unit but in another dimension, which `var-unit` refuses with its own red line.

---

### The unit of a result — one per dimension, and `#unit` (v0.63)

`unit:` is optional. Left to itself, the engine names the unit an engineer writes for that dimension, from a table of **one unit per dimension** keyed by the dimension itself (`default-units` in `lib/formula.typ`):

| dimension | unit | | dimension | unit |
|---|---|---|---|---|
| m | mm | | N | kN |
| m² | mm² | | N·m | kNm |
| m³ | mm³ (W) | | N/m² | N/mm² |
| m⁴ | mm⁴ (I) | | N/m | kN/m |
| s | s | | g | kg |
| deg | ° | | *(none)* | a bare number |

So `M_Ed / a`, kNm over mm, comes to `2.037 kN` where v0.60 printed `2037.037 N`. **`#unit("Nmm")` replaces one entry**, from that line to the end of the document: the dimension is read off the unit given, so one call settles one kind of result and leaves the others alone. `#unit("m")` puts computed lengths back into metres; `#unit("%")` is refused, a result without dimensions being printed as a bare number, and so is a unit that cannot be read.

Until v0.62 this was a flat list tried in order, the first candidate landing between **0.1 and 1000** winning. That window had one merit and it is the thing given up here: a stress printed as `12 N/mm²` and a snow load as `1.729 kN/m²` though the two share a dimension. It also made a chosen unit unreachable — 20 kNm is 2·10⁷ Nmm, outside the window — so `#unit` could not have been built on it, and a report's units depended on how big a number happened to come out.

⚠️ **The accepted price: `N/m²` is one dimension.** A stress and a surface load share it, and the default serves the stress, which is the commoner computed result. A line that wants the other says so — `unit: "kN/m²"` on that call, or `#unit("kN/m²")` before the section that needs it. The choice is the engineer's now rather than the value's size.

👉 **`#unit` reaches only what the engine computes.** A value that already carries a unit keeps it: one read from the export (`var-of`, `show-calc`, `show-input`), and one written out by hand (`#var("R_k", 7, "kN")`). The unit of a value is the data's and is never retyped (§2 rule 1); `#var-unit` is what carries one into another unit deliberately.

⚠️ Every unit the engine names or composes is written with **real superscripts**, `N/mm²` and never `N/mm^2`: a unit is printed as a quoted word inside math, where a caret is a caret and not an operator. That is not a style rule but the v0.63 display bug — `F dot F` gives the dimension N², which no table names, and the base-unit fallback wrote it `N^2`, so the page read `1000000 N^2`. It reads `1 · 10⁶ N²` now, and `parse-unit` reads back everything the engine writes, since such a unit is stored in the registry and may come back as an operand. **A caret typed by hand is converted as it comes in** (v0.86.2, `written-unit`): `#var("f_y", 235, "N/mm^2")` is stored, and printed, as `N/mm²`, and so is a unit given to `var-unit`, to `eq`'s and `val`'s `unit:` and to `#unit` — a Swiss keyboard has no key for ². Only `^` and digits, which is all `parse-unit` reads after a caret; it had always read `^2` as an exponent, so nothing was computed wrong, only printed with its caret.

### Where the declared unit cannot be reached (v0.63)

A `unit:` of another dimension — `unit: "N"` on a formula that gives a moment — **no longer stops the compile**. The line prints the answer in the unit the operands were themselves written in, and one small red sentence under it names both:

```typ
#var("F", 2, "kN")
#var("l", 3, "m")
#eq("M", `F dot l`, unit: "N")
```

→ `M = F · l = 2 kN · 3 m = 6 kNm`, and under it, in red: *Die verlangte Einheit N passt nicht zu den Einheiten der Operanden — das Ergebnis steht in kNm.*

The **natural unit** is composed from the operands as they were written — an N times a mm is an `Nmm`, a kNm over a mm is a `kNm/mm` — concatenated the way `kNm` is written, and checked rather than trusted: the spelling is kept only if `parse-unit` returns the very factor and dimensions it was built from, and is rewritten with `·` where it does not. Where the operands compose into nothing writable, the table's own unit is used, and failing that, base units.

Three reasons for a red line rather than a refusal, in order: the number printed is right either way; a report that will not build teaches nobody which of the two units is wrong; and the value stored in the registry is the physically correct one, so every line below goes on computing from it. The same line appears under `#var-unit` and under a `#var` given a unit of another dimension.

**What stays blocking** is a unit that cannot be *read* at all (`unit: "Zork"`) — that is a typo, not a disagreement — along with everything else listed below.

### `#var-unit`, and a unit given to `#var`

```typ
#var("R", var-of("connection", "SD001-V1", "F_max"))   // R = 7 kN
#var-unit("R", "N")                                    // R = 7000 N
```

`#var-unit(key, unit)` converts a variable already declared and **prints it**, which is why it is named after `#var` and not `change-unit`: its line is `#var`'s line. From there on every formula naming it substitutes the new unit, and `#val` gives it. It is written back where the name lives — the current `var-domain`, or the default one it falls back to — so a conversion inside a column converts the variable rather than shadowing it.

**It takes `label:`, `descr:`, `norm:` and `norm-ref:`, as `#var` does** (v0.87, second half, the engineer: «#var-unit ne prend pas label: ni descr:»). Given, each **overrides** what the variable carries, field by field, and is **stored with it** — a conversion is a new declaration of the same variable, so a `#val` or a `#find` further down reads the label it was given here; `norm-ref:` alone replaces the clause and keeps the norm, as on `#var` (v0.86). They are printed by `#var`'s levels and its `note:` rule — in the one footnote inline, on the line with `note: "line"`. Until then `#var-unit` printed the extras the variable already carried and could neither state nor override them.

```typ
#var("I_p", var-of("connection", "VU-MP-1", "I_p"), level: 0)
#var-unit("I_p", "cm²", label: "Polares Trägheitsmoment", descr: "In cm² für den Vergleich mit dem Handbuch", norm: "bauforumstahl", level: 3)
```

And **a unit given beside a value that carries one now converts it**: `#var("F", var-of(...), "N")` on a value the export holds in kN prints `7000 N`. Until v0.63 it replaced the label and left the number alone — `7 N` — which is silently wrong on a value read from the workbook, and is the one class of error this whole file exists to prevent.

⚠️ A name `#var-unit` does not find is refused in its `context`, not in its `state.update`. **The function of a `state.update` runs only where something reads that state**, so a `panic` written there is silent in a document that never looks the registry up again — which is exactly the document a mistyped name produces. `#eq` is safe by construction, its `context` always reading the registry; `#var-unit` had to be made so on purpose, and a test holds it.

### Big numbers (v0.63)

Past **99 999** a number printed by `#var`, `#eq`, `#verify`, `#val` or `#var-unit` is written as a mantissa and a power of ten: `1234567` → `1.235 · 10⁶`, at the document's `number-digits`. Below the threshold nothing changes, and a small number is left as it was (`0.0000123` still prints `0`). A negative one is printed with a minus sign, `−1.235 · 10⁶` (v0.87: `signed-text` over `fmt-magnitude`, which keeps its hyphen, §4bis).

⚠️ **Confined to `lib/formula.typ` on purpose.** `fmt-decimals` is the primitive every other display path goes through — `show-calc`, `show-input`, the tables, the figures — and putting the rule there would have rewritten numbers on pages nobody asked about, a connection's `I_p = 157000 mm²` among them. A test asserts that `fmt-decimals(157000, 3)` is still `"157000"`, which is what makes the confinement a fact rather than an intention. The exponent is written with superscript digits and never `10^6`, for the reason every other superscript here is: these strings are printed inside quoted words in math, which is what keeps a substituted operand **one atom**.

### The unit algebra, unchanged from v0.60

⚠️ **The tables are `lib/units.json`'s since v0.117** -- the prefixes, the bases with their factor and dimensions, the superscript digits, the unit a result of each dimension is printed in, and the units the «Formule» tab offers for a result of each dimension (`offered`). `formula.typ` reads it with `json("units.json")`; `calc/units.py`, the Python twin of this algebra that the tab computes with at once (D-10), reads it as a file; the engine copies it into a project (`project.ENGINE_FILES`). `tests/test_units.py` compiles a corpus of 28 formulas in one probe and holds Python equal to Typst, value and unit, and Python refusing everything Typst refuses -- the price of an instant result in the window, accepted as it was for the member checks (docs/decisions.md).

A unit is parsed into a **scale factor** and a **map of base dimensions**: `kN` is (1000, N:1), `mm²` is (1e-6, m:2), `kN/m²` is (1000, N:1 m:-2) and `N/mm²` is (1e6, N:1 m:-2) — the same dimensions a thousand apart, which is what lets a stress be computed in one and printed in the other. Multiplication adds exponents, division subtracts, a power scales them, a sum requires them equal, `sqrt` halves them.

Reading a unit is a rule, not a table of special cases: at each position the **longest** prefix-plus-base match wins, which tells `mm` (milli-metre) from `m·m` (metre squared) and reads `kNm` as kN·m. N is kept as a base rather than resolved to kg·m/s²: nothing here mixes the two, and every message then reads in the units an engineer writes. **A literal may carry its own unit**, as math writes it: `350 "m"`, `0.4 "kN/m²"`. Norm formulas need it — SIA 261 5.2.6's `s_k = (1 + (h_0/350)²) · 0.4` has a length inside that 350 and a pressure in that 0.4, and without them the sum is dimensionally false. 👉 That is not a defect of the norm but of transcription: a constant with an implicit unit is exactly what a unit algebra is for.

**What stops the compile**, each fired on purpose in `tests/test_formula.py`: a sum of different dimensions, a `sqrt` of an odd power, an unreadable unit (in `unit:`, in `#unit`, in `#var-unit`), a `#unit` without a dimension, a `value:` the formula contradicts, a name the registry does not hold (`#eq`'s operand, `#var-unit`'s key), a key carrying a `-`, an unknown named argument, and two sides of a `verify` whose dimensions differ. 👉 A declared unit the formula cannot **reach** was on this list until v0.62; since v0.63 it is a red line under the result instead, for the reasons given above.

### `verify`

```typ
#verify(`F_Ed <= R_d`)                // F_Ed = 2.037 kN ⩽ 4.969 kN = R_d  ✔
#verify(`F_Ed / R_d <= 1`)            // either side may be a whole expression
```

| level | printed |
|---|---|
| 1 | `F_Ed ⩽ R_d` |
| 2 | `2.037 kN ⩽ 4.969 kN` |
| 3 | `F_Ed = 2.037 kN ⩽ 4.969 kN = R_d` — the right-hand side **reversed**, so the two numbers meet in the middle of the line, which is what the eye compares |
| 3, a side that is a formula | `F_Ed/R_d = 12 kN/24 kN = 0.5 ⩽ 1` — its letters, the same with the numbers and units put in, then its value (v0.87); on the right-hand side the same chain mirrored, its value nearest the sign |

**A side is printed at level 3 by what it is** (v0.87): a single variable as `F_Ed = 12 kN`, a bare number as the number alone, and a whole formula as its letters line, its numbers line and its value, so a checker sees where the 0.5 comes from. `eq` and `verify` build those lines with one function, `formula-lines`, and `verify` substitutes through placeholders as `eq` does, so a key cannot be substituted inside another's number. **A relation too wide for its line is stacked at its signs** (v0.87, second half; below): the first side's letters on a line of their own, then `= <numbers>`, then `= <value> ⩽ <the other side>`, as much on each line as the width holds so the two values the eye compares stay together where they can, each sign under the one before — under the first side's variable where it is one, at a fixed 2 em indent (`relation-indent`) where the first side is a whole formula, whose letters line may well be the widest of all — and the whole double-ruled with the ✔ or ✘ on its last line. A relation that fits is set as before, in a box the width of its line, so it still stands in a sentence and is **no longer split across two lines** by the paragraph around it.

**The printed sign follows the truth.** Where `F_Ed <= R_d` does not hold, the line prints `F_Ed > R_d`: what is written is then a true statement, and the ✘ is what says the relation the report *wanted* is not the one that holds. `<=`↔`>`, `>=`↔`<`, `=`↔`≠`.

A side that is exactly one variable keeps that variable's own unit rather than the one the preference table would pick, so `F_Ed <= R_d` prints the kN the report wrote. The comparison is made on the **full** values, not the decimals printed, with a tie absorbed at a relative `1e-9`.

⚠️ It is **not** called `eval`, which the engineer proposed: `eval` is a Typst global and `commands.typ` re-exports at the wildcard, so the name would be masked in every section — the one rule §10bis puts on the engine's names.

### Levels

`level: auto` on all six, resolved by `resolve-level` like every other command (§4): the line follows the report's level, an explicit `level:` forces that one line, and `--input uniform=N` passes before both. That is what keeps **one file producing the client, engineer and checking reports** (§3.7).

**Level 0 prints nothing, and every other level prints something** (v0.85, the engineer's own rule: «au level 0, il ne doit pas y avoir d'affichage», «tout autre chose que level:0 doit toujours afficher quelque chose»). Until then it was `level: 1` that hid a declaration, which put two different notions on one scale — *how much of a calculation a report shows*, and *whether this line belongs on a page at all* — and they were confused in exactly one direction: a variable written by hand appeared in the engineer's report and the checker's and was missing from the **client's**, level 1, which is the report where a bare `R_d = 4.969 kN` is most nearly the whole point. They are apart now. 0 says *not on the page*; 1, 2 and 3 say *how much of the page*; and `#var` prints at level 1 exactly what it prints at level 2.

**One scale for the three commands that print a single value** (v0.85.1, the engineer's own): **1 the value, 2 the label with it, 3 the description and the citation as well.** `val` already read that way (v0.80); `var` and `eq` did not. `#var` printed its label only at level 3 — one level later than the word that names a number is wanted — and printed its **citation in the right-hand column at every level**, so a client report carried «SIA 265 §6.2.1.1» beside a bare number with nothing saying what the number was. `#eq` had no label at all and now takes one. What did *not* move is `eq`'s own two lines: the formula in letters at 2 and in numbers at 3, which are the working and not an extra.

| level | `var`, `var-unit` | `eq` | `verify` | `val` | `var-line` |
|---|---|---|---|---|---|
| **0** | nothing | nothing | nothing | nothing | nothing, not even the space of a line |
| 1 | symbol, value, unit — inline | symbol and answer | the symbols | the value, as `type:` asks for it | the row |
| 2 | + the label, in its footnote (after an em dash with `note: "line"`) | + the formula in letters, and the label | the numbers | + the label | the same |
| 3 | + the description and the citation, in the same footnote (a footnote and the right-hand column with `note: "line"`) | + the formula in numbers, the description and the citation | both, right side reversed, a formula side as letters, numbers and value | + the description, its choices and the citation | + the row's own citation |

⚠️ **Level 3 says everything the value carries** (v0.85.2, the engineer: «il faut rajouter la description pour être complet»), and **where** each part goes is settled rather than interchangeable. On a line of its own — `note: "line"`, which every `#eq` was until v0.117 — the **label** is what the variable *is*, so it is read with it, after an em dash (v0.61.1); the **description** is why *this* value was chosen, which is §9's footnote and stays one, with the `choices` it explains; the **citation** is the right-hand column's, which is what keeps it level with the line it cites (§10). Inline — in a sentence, in a `var-line`, and by default a `#var` since v0.87 and an `#eq` since v0.117 — there is no em dash and no column, so the three fold into the one footnote `line-note` builds, in that order.

⚠️ **`label` and `description` are two fields, and the registry carries both** (v0.85.1). In the data they always were (§3.1, §9): `label` is what the variable *is* — «Expositionsbeiwert», «Durchmesser» — and `description` is why *this* value was chosen, which carries the `choices` with it and is what §9's footnote exists for. `var-record` stored `#var`'s `label:` under `description`, a leftover from v0.80 renaming `descr:` to `label:` without renaming the field, and a var object read out of the export therefore had its label **dropped**: `#var("ce", var-of("snow-load", "SL", "ce"))` printed the sentence about the wind exposure and never the word the row is called by. ⚠️ It was invisible for five versions because nothing printed both fields side by side, and what exposed it is `find`: its table is the first thing to put a var of the export and a var of the report in one column, and the engineer read the question off it in a sentence. That is the argument for the command existing at all. ⚠️ A **publisher** — code that writes a record into the registry from outside `#var`, as `show-polar-moment` does — states a `label` for the same reason: «Grösste Kraft in einem Verbindungsmittel» is what the variable is, not why a value was chosen.

⚠️ **`var`, `val` and `eq` each take all four** — `label:`, `descr:`, `norm:`, `norm-ref:` — and each **overrides** what the value already carries (v0.85.2). The override is the point rather than the declaration: a var of the export arrives with a label, a description and a citation of its own, and a report quoting it for something narrower than its own label says has to be able to say so at the call. What is not overridden is kept, one field at a time. ⚠️ `descr:` is an argument again, and it is v0.80's rename corrected rather than reversed: that version renamed `#var`'s `descr:` to `label:` on the ground of «one word for one notion» (§4bis), which was right about the word and wrong about there being one notion.

⚠️ **Level 0 prints nothing and does everything else.** The variable is stored, the formula is evaluated, the units are checked, the conversion is performed, the relation is compared — only the emission is held back, and every refusal fires exactly as it would at level 3: a name the registry does not hold, a sum of different dimensions, two sides of a relation that cannot be compared. A line hidden today is a line printed in the next report, and it must not be that report which finds the mistake.

⚠️ **0 is a per-call level and never a report level** (§4). It follows that `--input uniform=N`, which ignores a per-call `level:` by design, prints a level-0 declaration in `out/report-1|2|3.pdf` — as it already printed a level-1 one at uniform 2 and 3.

⚠️ **A level outside `auto`, 0, 1, 2 and 3 is refused**, naming the five (`check-level`). Until v0.85 only `var-line` checked at all: `level: 4` was read as 3, and `level: 0` printed the whole line in `eq`, `val` and `verify`, printed nothing in `var` and `var-unit`, and was refused by `var-line` — three answers to one word, which is what a level nobody had declared gets.

### A formula that wraps, with display fractions (v0.87)

The engineer added `show math.frac: it => $display(it)$` to his `config.typ`, and the two lines of one wrapped calculation ran into each other («lorsqu'un calcul est sur 2 lignes, il n'y a plus assez d'espace entre les deux lignes»): a display fraction reaches well above and below the line box its text edges give it, and **Typst does not count that height in the line**, so raising `par(leading)` did nothing — doubling it bought 3 px. The fix lives in `annotated-rows` in `lib/calc-engine.typ`, which sets the rows of `show-calc` and of every command here: **`row-cell`** measures a row, and only a row that is **taller than a line of roots and indices** (`tall-row-height`, 1.2 em — 0.8 em caught the t₁,₁ rows, whose two lines then read as two formulas) **and actually wraps** is set with its lines measured to their ink (`top-edge`/`bottom-edge: "bounds"`) and **0.5 em** between them (`wrapped-row-leading`), a little less than the 1 em between two rows so the two lines still read as one formula. A row that does not wrap, a row of text or of small math, and every gap between rows are exactly as they were. Accepted price: a uniform-level-3 compile of the report went from 3.35 to 3.57 s, every row being measured. A wide fraction that cannot break at all ran into the citation column until the second half of v0.87, which stacks such a formula at its `=` signs (below).

### A formula too wide for its row, stacked at its `=` signs (v0.87, second half)

The engineer: «Une longue fraction qui ne peut pas passer à la ligne déborde dans la colonne des citations». A calculation printed in letters, in numbers and as its answer stands on one line — `B_v = <letters> = <numbers> = 116.122 kN` — and a display fraction, which his `show math.frac` rule makes of every fraction, is one atom no line break can enter: the line ran into the citation column and off the page, and one that could break broke wherever the width ran out, an `=` left dangling at the end of a line. Such a line is now set the classic way, **stacked at its relation signs**: the left-hand side and the formula in letters on the first line, then the numbers and the answer — on one line where the width holds both, which is where a checker reads the one against the other, a line each where it does not — each `=` under the first, checked in the PDF to 0.2 pt. **What is measured decides, and nothing else changes**: the one-line form is measured against the width its row has (`layout()`), and a row that fits goes through the old code untouched — the snow, wind, dead-load, live-load and polar-moment pages came out pixel-identical, while the SD-10 connector's level-3 lines that used to wrap in mid-formula now stack at their `=`, the page some 3 % taller.

**How.** A row that may be stacked is a `formula-chain` — its one line, its first line, the segments after it, the function that sets some of them as one line under the first, and what the last line ends on — and `annotated-rows` hands a set of rows carrying one to `chain-rows`, which measures and lays them out once the width is known; `chain-lines` packs the segments onto as few lines as fit, and `chain-line` sets a line after the first by measuring the first line's left-hand side and putting an empty box of that width in its place inside the same equation, so the space math sets around the `=` is the first line's own and the signs fall one under the other. `#eq`, `show-calc`'s steps — the one row of an `inline` step, and the numbers line of a step on two — and `#verify` (above, which stacks its relation by the same rule) all go through it; `show-polar-moment`, which joins steps into lines of its own (`n = 4; I_p = …`), takes their one-line form (`one-line`).

**Where the lines and the citation go.** A stacked line spans the citation column, having no citation to leave room for; the citation stands **at the end of the first line**, on that line's own baseline (`note-on-line`) — a first line measured to its ink put the middle of a tall fraction well above the `=`, and a citation centred in its row sat level with the numerator — or at the end of the second where the first alone is wider than the column left of the citation, the second then being packed to that column. The lines of one formula are 0.5 em apart measured to their ink (`chain-leading`, `row-cell`'s `wrapped-row-leading`), the top of the first and the foot of the last keeping the text's own edges, so a stacked formula stands as far from the rows around it as a line that fits. And a line carrying no citation that is too wide for the column left of the citations but fits the full width now spans it **on one line**, where it wrapped.

⚠️ **A single segment wider than the whole text is left as Typst sets it** — an inline equation breaks at its own relations and operators, never inside a fraction — and may still run past the page (§14). Setting such a fraction in inline style instead would overrule the engineer's own `show math.frac` rule in `config.typ`, which is his to make.

### What it still does not give

⚠️ **Untraced** (§1). No `source`, nothing in `data/`, nothing in `docs/typst-reference.xlsx`, and the `norm:` it prints is the caller's word rather than the data's. What it guarantees is that the printed formula, the printed numbers and the printed answer are one statement. A value a checker must re-derive belongs in a Python domain, and load combinations belong in `combinations.py` without exception (§3.5).

⚠️ **It checks dimensions, never sizes.** `1000` is a dimensionless factor, so `M / a dot 1000` is valid and comes to 2037 kN — held by a test that asserts the wrong answer, so nobody later mistakes it for a guarantee. What guards against it is that the substituted line prints the factor where a reader sees it.

---

**`verify-core` (internal, issue #12).** `verify` is `verify-core(relation, level:)`; the member checks' verdict (lib/timber.typ `timber-verdict`) calls the core with three more of its arguments: `brief: true` prints a side that is a formula at level 1 as its symbols *and* its value, `σ_t,0,d / f_t,0,d = 0.41 ⩽ 1`, where `verify` prints the symbols alone; `left-unit: "%"` shows the left-hand side's value in percent, 0.41 as 41 %; `left-only: true` prints the left-hand side and the mark and neither the sign nor the right-hand side, the comparison still made against it -- `σ/f = 41 % ✔`. It is listed among the engine's own bindings and documented here, not in the commands tab.
