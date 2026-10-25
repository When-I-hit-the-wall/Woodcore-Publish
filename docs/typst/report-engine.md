# Report engine: levels, positions and their calculations, data access, inputs

> Global level with local override, a position and the calculation that concerns it, the get abstraction, input descriptions.
>
> Moved verbatim from CLAUDE.md (§4, §5, §6, §6bis, §9) on 2026-10-07. The § numbers are kept as stable anchors: `docs/README.md` maps every § to its file.

## 4. Global level with local override (Typst)

```typ
// Statischer Bericht (typst)/Statischer Rapport.typ
#import "commands.typ": *    // every command of lib/calc-engine.typ, report-level among them (§10bis)

// Default level, fixed at compile time: typst compile --input level=2 ...
#let default-level = int(sys.inputs.at("level", default: "2"))
#report-level.update(default-level)

= Element T001

// Uses the global level (2, if compiled with --input level=2)
#include domain-file("snow-load", "SL")

// Local override: force this ONE value to show full detail,
// even if the report is compiled in "summary" mode
#var("s_k", domain: ("snow-load", "SL"), level: 3)
```

Implementation in `lib/calc-engine.typ`: a global `state("report-level", 1)`; a command given `level: auto` reads the state via `context`, otherwise uses the value passed explicitly — without touching the global state; between them, `#calc-defaults(level:, scope:)` and a `#domain`'s own `level:` (lib/formula.typ `resolve-display`, REQ-007).

**A third setting exists for one purpose: the reference variants in `out/`.** `--input uniform=N` sets a second state, `uniform-level` (default `none`), and when it holds a level **every** command renders at it (but a cell of a `#sync`, which prints what it holds, Q-005, Q-007) — the per-call `level:` overrides are ignored, not merely outranked. That is the only way to obtain a PDF that is genuinely one level throughout, because an override is a literal argument at the call site: no outside state can disarm it, and no separate entry file could either. The three routes are therefore distinct and each has a job:

| Input | Base level | Per-call `level:` | Used for |
|---|---|---|---|
| *(none)* | the document's own `sys.inputs.at("level", default: ...)` | honoured | the working report, `Statischer Rapport.pdf` |
| `--input level=N` | N | honoured | the same, with the base forced for one run |
| `--input uniform=N` | N | **ignored** | `out/report-N.pdf`, one level throughout |

All three resolve through one helper, `resolve-level(level)`, which replaced the `if level == auto { report-level.get() } else { level }` that `show-input` and `show-calc` each carried a copy of — the level is decided in one place now, so a third caller cannot get it subtly wrong.

⚠️ **A per-call `level:` may also be 0, which prints nothing at all** (§10quinquies, v0.85) — but only on the six commands a report writes its own calculations with (`var`, `var-unit`, `eq`, `val`, `verify`, `var-line`). **A report level may not be 0**: `--input level=N`, `--input uniform=N` and the document's own `default-level` take 1, 2 or 3, a report compiled at 0 being a report with nothing in it. The `show-*` commands take 1, 2 or 3 for a reason of their own — each of them prints its result at level 1, and a `show-calc` that printed nothing would *declare* nothing either, which is what not writing the call already does.

**A per-call `level:` of -1, «Sélection manuelle» (v0.117 to v0.120, issue #20), is retired**: `check-level` refuses it since the spec 2026-10-21-commandes-typst-refonte, the window offers it no more since the spec 2026-10-22-retrait-niveau-manuel, and `lib/shown-variables.json`, which listed what `shown:` could name, is gone. What a line prints is set by the fine display arguments and the level presets (docs/typst/formulas.md). The paragraph as it was: `docs/history/2026-10-22-niveau-manuel.md`.

**The level of each line is written once, in `lib/line-levels.json`, and read where the line is printed (v0.120, spec `2026-10-20-indices-et-niveaux`, UI-002, ARCH-002, D-13).** The engineer: «Niveau de détail : corrige (décidé par la commande)». Until v0.120 a line's level was a literal in two places -- each domain wrote `level=` into its export (snow, wind, the loads, steel), and `lib/timber.typ` wrote `plan-at(plan, "key", n)` for the member checks. The table now holds, domain by domain, the level each line is printed from: `lines` (a level, or `{var, step}` where a value and the working that produces it differ -- snow's `h_ref`: the value from 2, its working from 3), `kinds` (steel's `N_Rd`: 1 in a tension or a compression, 2 in a bending), `patterns` (wind's `qk_max_cf1`… by a regex) and `*` (a script's results, named by the engineer). `line-level(domain, kind, key, role, line)` (lib/calc-engine-core.typ) and `calc/line_levels.py`'s `level` read it by **one rule**:

Since the spec 2026-10-21-commandes-typst-refonte the export writes each line out with its level (calc/domains/unfold.py), read from this table; a line of the engineer's prints at its own level, its domain's or the document's. Until then the commands that rendered a calculation entire read it at compile time, in this order (the two paragraphs on them are in `docs/history/report-engine-retired-commands.md`):

1. the uniform level, else the call's `level:`, else the report's, is the command's level -- what it prints;
2. a line's own level is the table's for its domain, its kind and its role (var, step, check);
3. else the level the line carries in the export -- an export written before v0.120, a domain written by hand;
4. else the domain's `*`;
5. a line nothing gives a level stops the report naming its domain and key, a defect of Woodcore's.

**Every command that prints a figure, a table or a list takes `level:` too (v0.120, spec `2026-10-20-indices-et-niveaux`, UI-003, docs/decisions.md §13).** 1 the figure or the table alone, 2 with its legend and titles -- what a document printed until then, a document's own level --, 3 with its sources and citations, or as 2 where it has none (`build_reference_lib.LEVELS_CONFOUNDED`). `print-level(fn, level)` resolves it as every level is resolved (`resolve-level`), and `at-level(arg, lv, from)` decides an argument left `auto` -- a legend, a scale bar, a plan's lengths and centres, a schema's aids -- while an argument written outranks it. A sheet sets its report level to 2 unless `--input level=` says otherwise. The commands that take none -- the accessors, a form's field, a document's table, a sheet's text, section and title block -- are `build_reference_lib.NO_LEVEL`, each with its reason; tests/test_command_levels.py holds both registries to the engine.

**What prints from a level on, `#from-level(n)[…]` (spec `docs/requirements/completed/2026-10-23-onglet-vent-briques.md`, D-29).** A domain's file writes a figure that only its most detailed print shows in `#from-level(3)[#figure(…) <label>]`: the place's level -- the innermost `#domain` that states one, else the report's, the uniform level over both -- decides at the compile, so that the line is always written and «Affichage» sets its width, caption, label and «Afficher» as every figure's (`unfold.figure_line(level=3)`, `unfold_display.figure_parts` reads the level back). The preview of «Affichage» prints it pale (`show-masked`, `masked-line`). Its level is its argument, never a level of its own (`build_reference_lib.NO_LEVEL`). The wind's figure of the norm is its first user (version 4 of that spec).

**A number is printed by one rule, written once (v0.120, spec 2026-10-19-base-saine-nettoyage UI-002, UI-003).** `lib/number.typ`'s `display-number` is what every display of the engine goes through -- `fmt-number`, `fmt-value`, the tables, `value-text` and `value-in-formula` of a formula's second line, `#var`, `#eq`, `#verify`, `#val`, a connection's numbers -- and `calc/number_text.py`'s `display` is its Python twin, held equal by tests/test_number_text.py. At most **three decimals**, trailing zeros dropped (`3.120 → 3.12`, `438 → 438`); a **minus sign** U+2212 for a negative number; a **mantissa and a power of ten** past 99 999 (`123456 → 1.235 · 10⁵`) and below 0.1 where three decimals would not write the value whole (`0.00234 → 2.34 · 10⁻³`, while an exact `0.05` stays `0.05`) -- the engineer's rule of 19.10.2026 (Q-005: «3 chiffres significatifs, mais pas plus de 3 chiffres après la virgule»). A unit follows after a no-break space, and «°» after none (Q-013). The decimal mark is the point in the three languages. `number-digits`, the setting that chose the decimals until then, no longer changes anything: its state is kept so that a document that sets it still compiles. What is **transported** -- a literal Typst evaluates again, a figure's coordinate -- is not displayed and keeps its precision (D-22): `fmt-decimals`, the pure rounding the rule is built on, writes it.

`fmt-decimals(x, digits)` is **at most** `digits` decimals, with trailing zeros dropped: `1.7291232 → 1.729`, `0.800 → 0.8`, `438 → 438`. So a whole number stays whole and nothing is padded to a false precision.

⚠️ `calc.round` + `str` is the obvious implementation and the wrong one: it leaks float artefacts, printing a value that rounds to `1.084` as `1.0840000000000001`. `fmt-decimals` builds the digits from an integer instead, so what is printed is exactly what was rounded, then trims the tail.

---

## 5. A calculation and the position it concerns (spec 2026-10-21-commandes-typst-refonte, REQ-015; `#calc-block` until then)

A position is named on a line of its own by `#position(id, category-show: …)` -- its id in its type's colour, then the fields asked for --, and the calculation that concerns it is a `#domain(id, label: …)[…]` or a domain Woodcore wrote out, `#include domain-file(kind, id)`. Nothing checks any more that a calculation read inside a block belongs to the block's positions: the domain names what it reads, `#var(key, domain: …)`, and the graph of dependencies (docs/domain/dependencies.md) says which object reads which. The section on `#calc-block` is in `docs/history/report-engine-retired-commands.md`.

## 6. Data-access abstraction (Typst)

Access to JSON data in Typst must go through **abstraction functions**, defined in `lib/calc-engine.typ`:

```typ
#let get(v, "value") = v.value
#let get(v, "unit") = v.unit
#let get(v, "symbol") = v.symbol
#let get(v, "norm") = v.norm
#let get(v, "norm_ref") = v.norm_ref
#let get(v, "description") = v.at("description", default: none)
```

❌ To avoid elsewhere in the Typst code (`Sections/*.typ`, utility functions):

```typ
v.value
```

Goals:
- **decouple** Typst from the exact JSON structure,
- make **future schema changes** (§3.0) easier without breaking the whole report — a structural change only ripples through the `get-*` functions,
- **centralize** data-access changes in one place.

Every new display function (`show-calc`, `show-input`, etc., §9) must go through these `get-*` functions rather than accessing fields of the imported JSON directly.

### 6bis. Rendering symbols as real math (built example)

A `symbol` field is Typst math *source*, not a label to print verbatim. `lib/calc-engine.typ` evaluates it with `eval(get(v, "symbol"), mode: "math")` so it renders with a real subscript and, for names Typst recognizes (`gamma`, `mu`, `sigma`, `eta`, ...), the actual Greek glyph — never a literal underscore or a spelled-out Greek name. This is why `symbol` strings in `data/` must already be valid Typst math (§3.1's note on quoting multi-letter subscripts).

---

## 9. Describing input parameters in Typst (spec 2026-10-21-commandes-typst-refonte, REQ-009; `#show-input` until then)

Every input variable (in `vars`) can carry `description` and/or `choices` (§3.3, e.g. `ce`). `#var(name, domain: (domain, instance))` prints it, read live from the export, its label, description and choices placed by its `label-position` and `descr-position` -- the footnote at level 3 by default, as `#show-input` printed it. The section on `#show-input` is in `docs/history/report-engine-retired-commands.md`.
