# The sections of formulas.md on the retired commands

> Moved verbatim from `docs/typst/formulas.md` §10quinquies on 2026-10-22: the commands `#val`, `#var-line`, `#var-unit`, `#var-domain` and the arguments `note:`, `sep:` and `summary:` of `#var` and `#eq`, which the spec 2026-10-21-commandes-typst-refonte retired or replaced (lot 19). What a call of each becomes is `calc/renamed-commands.json`.

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

The engineer typed `#var("b", 208, "mm") ;` to set two values apart on one line; from v0.117 to v0.118 a `;` after a call made its line a text, which the «Formules» tab refused (`text_trailing`, retired in v0.119: the `;` is now a text glued to the command, see above), and a `var-line` was the only way left — a container the tab does not write. He asked for the separator to be **an argument of the command itself**, as the choice between inline and a line of its own already is (`note:`): «l'option ... serait un argument de var» (spec docs/requirements/active/2026-10-11-argument-sep-var.md).

```typ
#var("b", 208, "mm", sep: ";")
#var("t", 8.5, "mm", sep: ";")
#var("epsilon", 124)
```

prints `b = 208 mm; t = 8.5 mm; ε = 124`. The separator is printed **after** its value and its footnote, glued to it; the space after it is the source's line break, as between any two values written one under the other. It belongs to its value, so a value its level hides takes its separator with it (`check-sep`, `check-sep-row`, `sep-after` in lib/formula.typ) — what a row was made for. `sep: none`, the default, changes nothing. It is **refused**, naming why, with `note: "line"` (a line of its own has no neighbour to separate it from), inside a `var-line` (the row writes its own: `var-line(sep:)`), and when it is not a string. `var-line` stays (D-05): reports use it. The «Formules» tab offers it in «Affichage» as «Séparateur (en ligne)», and its refusal of `#var(...) ;` names `#var(..., sep: ";")` as what to write instead.

### `summary:` — one line of a summary table (v0.99)

`#var(..., summary: true)` and `#eq(..., summary: true)` list the variable in a summary table (`show-load-summary`, `show-load-summary(v, unit: "kN/m")`, §10bis) — and **its unit decides which**: `kN/m²` an area load, `kN/m` a line load, any other unit refused naming the two. It is the one way a load the export does not carry reaches a summary, and the export carries no line load at all (§3.3octies).

⚠️ **The mark is not a state of its own.** `summary-mark(d, on, key)` is a **pure function of the variable registry's own dictionary**, called from inside the `var-registry.update` that `var` and `eq` already have — `var-store`'s own shape. Two things follow, and they are why that shape was chosen over one more `state`. v0.85's rule — a state written from inside a `context` is not read back by the folded chain an update function reads (§3.3quinquies) — is satisfied **by construction**: there is no second state that could be emitted in the wrong place. And the **var-domain** the variable belongs to, `var-current(d)`, is readable only *there*: outside an update nothing can read a state at all.

⚠️ **What is recorded is the name, never the value.** An `#eq` computes its answer inside that very update, and so does a `#var` reading a var-domain (§10quinquies, v0.85): the value does not exist yet. It is therefore read where the table is printed — which is also the value the variable *ends up* holding, `#var-unit` having perhaps converted it in between.

⚠️ **And that is why the unit is checked there and not at the call.** A marked `#eq` often states no `unit:` at all, its answer coming out in whatever unit the algebra gives its operands; and `#var-unit` may carry a variable out of its unit on the line after. A check at the call would therefore refuse a variable that is right by the time it is read. The accepted price: a `summary: true` in a report that prints no summary is **never** refused — nothing listed it, and nothing is wrong with the page. And **either** table refuses every mark, whichever unit it is itself gathering: what is wrong is the mark, not the table it is missing from. ⚠️ The refusal does **not** send the engineer to `#var-unit`: a kN is not a kN/m in another unit but in another dimension, which `var-unit` refuses with its own red line.

---

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
