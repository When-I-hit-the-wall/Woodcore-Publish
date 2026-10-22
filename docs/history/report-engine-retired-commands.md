# The sections of report-engine.md on the retired commands

> Moved verbatim from `docs/typst/report-engine.md` on 2026-10-22: the calculation block (§5) and the description of an input by `show-input` (§9), which the spec 2026-10-21-commandes-typst-refonte retired (lot 19); what a call of each becomes is `calc/renamed-commands.json`.

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

## 9. Describing input parameters in Typst

Every input variable (in `vars`) can carry `description` and/or `choices` (§3.3, e.g. `ce`). `show-calc()`/`show-input()` automatically display a footnote reprising this description, so a reader of the report understands why this value was chosen over another — especially useful for norm coefficients with discrete choices (Ce, Ct, kmod, ...). A `step` may carry a `description` too, footnoted on its formula (§3.3).

```typ
#let show-input(domain, instance, name, level: auto) = {
  let v = ... // resolved inside vars
  [#render-symbol(v) = #fmt-value(v)
   #if level >= 2 [#footnote(get(v, "description"))]]
}
```

⚠️ **One footnote per var, not two.** A var carrying both a `description` and a `choices` list used to print two markers side by side, which read as a single two-digit number rather than as two references. `var-row()` in `lib/calc-engine.typ` merges them into one footnote; every display function goes through it, so a var is formatted identically wherever it appears.

Note: access to `value`/`unit`/`symbol` goes through `get(v, "value")`/`get(v, "unit")`/ `render-symbol` (§6, §6bis), never a direct field access on the JSON.

---

`show-calc` reads it for every var and step it prints; `#member` and the verify-* commands print each line at `timber-at(plan, key)`, the table's level. Connectors and connections are in it too (82 lines, collected as the others): `show-connector-resistance` and `show-polar-moment` decide what they print by thresholds of their own, but a `#show-calc("connector", …)` written by hand reads the lines' levels, which their exports no longer carry. Tables and figures of an export keep their own `level`: they are objects, not lines. `tests/test_line_levels.py` holds every line the domains exported until v0.120 to the level it was exported at (`tests/fixtures/line-levels-history.json`, 302 lines: the domain tests run with the engine instrumented, and the example project's exports as committed before), Typst's reader to Python's, timber's keys to `shown-variables.json`'s, that no domain writes a line's level any more, and that every domain prints differently at 1, 2 and 3. Python reads the table where it shows a level (`calc/line_levels.py`: the «Variables» tab, the reference workbook, a steel check's answer).

**A check's verdict is a key like any other (issue #58).** Each verify-* command's keys in `lib/shown-variables.json` include its verdicts, by the key of the utilisation `timber-verdict` stores -- `eta`, `eta_s`, `eta_y`, `eta_z`, `eta_m`, `eta_m_t`, `eta_m_c` --; `timber-verdict(plan, key, …)` prints at `plan-at(plan, key, 1)`: the check's level, or at -1 the level `shown:` gives it, brief at 1, full at 2 and 3, nothing where it is not named. Issue #39's `results` (the stresses, printed at 1 where left out, refused at 0) are retired with `shown-results` and the `results:` of `level-plan` and `check-shown`; `verify-shear-off` and `verify-shear-perp`, which take no `shown:`, take their plan from `level-plan(level, none)`. `verify-shear` takes `shown:` and -1 since issue #38. `show-calc` also names an instance's drawings, `figure-1`, `figure-2` (schema 1.5).
