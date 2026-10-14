# Report engine: levels, calc-block, data access, inputs

> Global level with local override, the calc-block, the get-* abstraction, input descriptions.
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
#show-calc("snow-load", "SL")

// Local override: force this ONE calculation to show full detail,
// even if the report is compiled in "summary" mode
#show-calc("snow-load", "SL", level: 3)
```

Implementation in `lib/calc-engine.typ`: a global `state("report-level", 1)`; `show-calc(..., level: auto)` reads the state via `context` when `level` is `auto`, otherwise uses the value passed explicitly — without touching the global state.

**A third setting exists for one purpose: the reference variants in `out/`.** `--input uniform=N` sets a second state, `uniform-level` (default `none`), and when it holds a level **every** `show-*` renders at it — the per-call `level:` overrides are ignored, not merely outranked. That is the only way to obtain a PDF that is genuinely one level throughout, because an override is a literal argument at the call site: no outside state can disarm it, and no separate entry file could either. The three routes are therefore distinct and each has a job:

| Input | Base level | Per-call `level:` | Used for |
|---|---|---|---|
| *(none)* | the document's own `sys.inputs.at("level", default: ...)` | honoured | the working report, `Statischer Rapport.pdf` |
| `--input level=N` | N | honoured | the same, with the base forced for one run |
| `--input uniform=N` | N | **ignored** | `out/report-N.pdf`, one level throughout |

All three resolve through one helper, `resolve-level(level)`, which replaced the `if level == auto { report-level.get() } else { level }` that `show-input` and `show-calc` each carried a copy of — the level is decided in one place now, so a third caller cannot get it subtly wrong.

⚠️ **A per-call `level:` may also be 0, which prints nothing at all** (§10quinquies, v0.85) — but only on the six commands a report writes its own calculations with (`var`, `var-unit`, `eq`, `val`, `verify`, `var-line`). **A report level may not be 0**: `--input level=N`, `--input uniform=N` and the document's own `default-level` take 1, 2 or 3, a report compiled at 0 being a report with nothing in it. The `show-*` commands take 1, 2 or 3 for a reason of their own — each of them prints its result at level 1, and a `show-calc` that printed nothing would *declare* nothing either, which is what not writing the call already does.

**A per-call `level:` may be -1 since v0.117, which prints what `shown:` names** (issue #20; spec 2026-10-10-issues-github-19-20-21): `level: -1, shown: (A: 2, W_y: 1)` prints the variables it names, each as a line of the level it gives it, and none of the others — the title and the verdict as at level 1, a heading printed from level 2 only where one of its keys is chosen, a figure where a key is chosen at 2 or 3, a result not chosen not at all (D-09, D-12). It is taken by `member`, the five `verify-*` the member checks call, `show-check-member` (one list for the member and its check, a key both print being the check's, D-11), `show-calc` (the window offering it in the three load tabs too since issues #56, #57), `show-connector-resistance` and `show-polar-moment`. **What a command may name is written once**, in `lib/shown-variables.json` — every key it can print, in its order, axes written out (`k_c_y`, `k_c_z`), and the keys under each heading printed from level 2 only —, read by `lib/calc-engine.typ` (`json("shown-variables.json")`) to refuse a key a command does not print, naming those it does, and by `calc/shown_variables.py` for the boxes the window ticks; it travels with the engine (`project.ENGINE_FILES`). `show-calc`'s keys are the instance's own, its vars and its tables (`table-1`, `table-2`); `show-polar-moment`'s are groups of lines (`positions`, `centre`, `theta`, `n`, `I_p`, `forces`, `components`, `F_x_i`, `F_z_i`, `F_max`, `beta`, `forces_table`, `worst_table`). The list is a superset: a key a call does not print for its arguments — α = 0, a round section, no stability — is accepted and ignored. **One place decides the level a line prints at** — `level-plan`, `plan-at`, `plan-row`, `plan-part`, `plan-any` beside `resolve-level`, the only `-1` of lib/ being `selection-level` —, and the value of every line is computed and stored at every level as before (`calc/variables.py` reads the same registry). Like 0, -1 is a level of **one call and never of a report**: `resolve-level` hands it back as it stands, `--input uniform=N` still forces its level over it, and `report-level.update(-1)` is refused. `shown:` with any other level, an unknown key and a level outside 1–3 in it are refused.

**A check's verdict is a key like any other (issue #58).** Each verify-* command's keys in `lib/shown-variables.json` include its verdicts, by the key of the utilisation `timber-verdict` stores -- `eta`, `eta_s`, `eta_y`, `eta_z`, `eta_m`, `eta_m_t`, `eta_m_c` --; `timber-verdict(plan, key, …)` prints at `plan-at(plan, key, 1)`: the check's level, or at -1 the level `shown:` gives it, brief at 1, full at 2 and 3, nothing where it is not named. Issue #39's `results` (the stresses, printed at 1 where left out, refused at 0) are retired with `shown-results` and the `results:` of `level-plan` and `check-shown`; `verify-shear-off` and `verify-shear-perp`, which take no `shown:`, take their plan from `level-plan(level, none)`. `verify-shear` takes `shown:` and -1 since issue #38. `show-calc` also names an instance's drawings, `figure-1`, `figure-2` (schema 1.5).

**Decimals are a second, separate document-wide setting**, on the same pattern: `number-digits` (a `state`, default 3) is set once in `Statischer Rapport.typ` and every number the engine prints goes through `fmt-decimals` — so `show-calc`, `show-input`, `val`, the layer tables and the checks all change together. An equation written by hand in math mode joins the same setting as long as it prints its numbers with `val` (§1, §10bis) — as does the substituted second line of every formula (`value-in-formula`, `value-text`), which builds Typst math *source* and so goes through the string primitive `fmt-decimals` rather than through `fmt`.

The rule is **at most** `number-digits` decimals, with trailing zeros dropped: `1.7291232 → 1.729`, `0.800 → 0.8`, `438 → 438`. So a whole number stays whole and nothing is padded to a false precision.

⚠️ `calc.round` + `str` is the obvious implementation and the wrong one: it leaks float artefacts, printing a value that rounds to `1.084` as `1.0840000000000001`. `fmt-decimals` builds the digits from an integer instead, so what is printed is exactly what was rounded, then trims the tail.

---

## 5. The calculation block: attributing calculations to positions

**Current approach (v0.12).** The unit of work in the report is not a single calculation but a **calculation block**: one or more calculations that all concern the same position(s). The block declares which positions it concerns; the engine renders their descriptive summaries as its header and frames the body so everything inside is visibly tied to them.

```typ
#calc-block("T001", title: "Berechnung von Schneelast", axes: "Achse X3 / Achse YC")[
  Prose, calculations and figures for T001 ...

  #show-input("snow-load", "SL-Dach1", "ce")
  #show-calc("bending", "T001")
  #show-check("bending", "T001", "Bending utilization")
]
```

renders as a left-ruled block whose header is the title, then one summary line per declared position:

```
│ Berechnung von Schneelast
│ T001: Träger, Fichte GL24h, 140/400 mm, Feuchteklasse 1 (Achse X3 / Achse YC)
│ ──────────────────────────────────────────────────────────────────────
│ ... body ...
```

Several positions at once — the common case of identical elements sharing one calculation — are declared as an array, with either one `axes` string for all of them or one entry per position:

```typ
#calc-block(
  ("T001", "T002"),
  title: "Biegenachweis Dachträger",
  axes: ("Achse X3 / Achse YC", "Achse X4 / Achse YC"),
)[ ... ]
```

**Direction of attribution: block → position, never the reverse.** This is the same presentation-only relationship as axes. Naming a position in a `calc-block` writes nothing into `data/positions/<id>.json`, and a load's `show-input()` may sit inside a block without that creating any position↔load link (§8) — the block says "this is where the reader should look on the plan", not "this position owns this load".

**Why a container function** rather than the alternatives:
- A trailing content block is Typst's idiom for a scoped, framed region. It nests, it composes, and the whole visual treatment lives in one place instead of being re-typed per section.
- Attribution is stated once instead of being repeated (and mistyped) on every call.
- It is the only construct that can carry a **scope guard**: because the block knows which positions it declares, `show-calc`/`show-check`/ `show-input` can verify at compile time that the position they read belongs to the enclosing block, and `panic()` with an actionable message otherwise. A calculation for the wrong position printed under a position's header is exactly the kind of error that is invisible in a finished PDF and expensive in a structural report.
- Rejected: keying the grouping off headings (couples report structure to data, breaks as soon as one block spans several positions or a position recurs in several sections), and the v0.4-v0.11 mechanism below.

**Replaces the old banner mechanism.** Until v0.11, `show-calc()` took an `axes:` argument and printed a `T001 -- axis X3 / axis YC` banner before the first calculation shown for a position, tracked by a `last-position-shown` state. That is gone: `show-calc()` no longer has an `axes` parameter, and nothing groups calculations implicitly by "first time this position appears". Positions and axes are now announced once, explicitly, by the block that owns them.

⚠️ Accepted consequence, unchanged from v0.4: axes are **not traced in the data**. They are a pure presentation detail, now supplied once per block rather than per call.

**The plan in the header (v0.34).** A block may also show where its positions are: `plan: auto` sets, under the summaries, a detail of every position plan its positions are drawn on, with them highlighted, at the scale of the whole plan (§3.3sexies). A plan id shows that plan instead, and the default `none` shows nothing. The plan reads the block's positions; it adds nothing to them.

---

## 6. Data-access abstraction (Typst)

Access to JSON data in Typst must go through **abstraction functions**, defined in `lib/calc-engine.typ`:

```typ
#let get-value(v) = v.value
#let get-unit(v) = v.unit
#let get-symbol(v) = v.symbol
#let get-norm(v) = v.norm
#let get-norm-ref(v) = v.norm_ref
#let get-description(v) = v.at("description", default: none)
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

A `symbol` field is Typst math *source*, not a label to print verbatim. `lib/calc-engine.typ` evaluates it with `eval(get-symbol(v), mode: "math")` so it renders with a real subscript and, for names Typst recognizes (`gamma`, `mu`, `sigma`, `eta`, ...), the actual Greek glyph — never a literal underscore or a spelled-out Greek name. This is why `symbol` strings in `data/` must already be valid Typst math (§3.1's note on quoting multi-letter subscripts).

---

## 9. Describing input parameters in Typst

Every input variable (in `vars`) can carry `description` and/or `choices` (§3.3, e.g. `ce`). `show-calc()`/`show-input()` automatically display a footnote reprising this description, so a reader of the report understands why this value was chosen over another — especially useful for norm coefficients with discrete choices (Ce, Ct, kmod, ...). A `step` may carry a `description` too, footnoted on its formula (§3.3).

```typ
#let show-input(domain, instance, name, level: auto) = {
  let v = ... // resolved inside vars
  [#render-symbol(v) = #fmt-value(v)
   #if level >= 2 [#footnote(get-description(v))]]
}
```

⚠️ **One footnote per var, not two.** A var carrying both a `description` and a `choices` list used to print two markers side by side, which read as a single two-digit number rather than as two references. `var-row()` in `lib/calc-engine.typ` merges them into one footnote; every display function goes through it, so a var is formatted identically wherever it appears.

Note: access to `value`/`unit`/`symbol` goes through `get-value`/`get-unit`/ `render-symbol` (§6, §6bis), never a direct field access on the JSON.

---
