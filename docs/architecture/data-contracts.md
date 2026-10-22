# Data contracts: schemas, positions record, validation, levels

> JSON schemas, the position record, validation levels, the three detail levels.
>
> Moved verbatim from CLAUDE.md (§3, §3.0, §3.1, §3.2, §3.4, §3.6, §3.7) on 2026-10-07. The § numbers are kept as stable anchors: `docs/README.md` maps every § to its file.

## 3. Schemas and data structure

### 3.0 Mandatory JSON schemas

Every JSON file produced by the pipeline (`positions`, `positions-index`, `calculations`, `connectors`, `connections`, `plans`, `statics`, `schemas`, `formulas` -- 2.0 since issue #15, keyed by the domain's id with its title --, `dependencies` -- 1.0 since issue #71, the graph of which object reads which, docs/domain/dependencies.md §3.3quinvicies --) and every file Woodcore keeps for the window (`lists`, `Woodcore-Datei/lists.json`: the order of the lists and the «Formules» tab's folders, 1.0, issue #15 -- checked on read and on write, a malformed one said and left as it is, never an export input) must follow an **explicit, documented JSON schema**, which acts as a **formal contract** between Python and Typst.

A schema defines:
- the **required fields**,
- the expected **types** (number, string, object, array, ...),
- the expected **structure** (nesting, allowed keys).

**`sync.json`** — each document's record of what it shares (`schemas/sync.schema.json`, `woodcore-sync` 1.0, docs/domain/documents.md §3.3octodecies) — had no schema until v0.117 (issue #33), its contract being the code of `sync.check_source`; it has one now, which `check_source` validates against before its own rules.

The schemas live in `schemas/` (see §11 — detailed Python layout) and are used by the Python validation module (§3.6) before anything is exported to `data/`.

Every exported JSON file also carries an explicit version field:

```json
"schema_version": "1.0"
```

Goals:
- allow the format to evolve without breaking older projects,
- guarantee backward compatibility,
- track which data structure produced a given report (the `schema_version` is checked against its contract on every export (§3.6) and archived with `data/` (§12); the report itself does not print it, §1bis).

### 3.1 One file per position — `data/positions/T001.json`

⚠️ **As of v0.11, `domains` is always `{}`** — a position is descriptive only (§7-§8), so the `domains` block below documents the *shape* a domain must have (the schema contract, still enforced by `schemas/position.schema.json` and by `lib/calc-engine.typ`'s `show-calc`/ `show-check`), not something any file currently contains. The real `data/positions/T001.json` today is just its nine top-level fields (`schema_version`, `position`, `type`, `material`, `strength_class`, `dimension`, `units`, `moisture_class`, `description`), with `"domains": {}`.

```json
{
  "schema_version": "1.2",
  "position": "T001",
  "type": "Träger",
  "material": "Fichte",
  "strength_class": "GL24h",
  "dimension": "140/400",
  "units": "mm",
  "moisture_class": 1,
  "description": "Roof beam, axis 3-C",

  "domains": {
    "bending": {
      "vars": {
        "M_Ed": {
          "value": 26.9, "unit": "kNm", "symbol": "M_\"Ed\"",
          "label": "Design moment", "level": 1,
          "source": "python:domains/bending.py",
          "norm": "SIA 265", "norm_ref": "4.2.1"
        },
        "sigma_m": {
          "value": 7.2, "unit": "N/mm²", "symbol": "sigma_m",
          "label": "Bending stress", "level": 1,
          "source": "python:domains/bending.py",
          "norm": "SIA 265", "norm_ref": "4.2.1"
        }
      },
      "steps": [
        {
          "name": "Design moment", "level": 1, "result": "M_Ed", "uses": [],
          "norm": "SIA 265", "norm_ref": "4.2.1"
        },
        {
          "name": "Bending stress", "level": 1, "result": "sigma_m",
          "uses": ["M_Ed"], "formula": "sigma_m = M_\"Ed\" / W",
          "norm": "SIA 265", "norm_ref": "4.2.1"
        }
      ],
      "checks": [
        {"name": "Bending utilization", "eta": 0.42, "unit": "",
         "level": 1, "status": "ok",
         "norm": "SIA 265", "norm_ref": "4.2.1"}
      ]
    }
  }
}
```

Notes:
- `schema_version` is **mandatory** at the top of the file (§3.0).
- **A line carries no `level` since v0.120** (spec `2026-10-20-indices-et-niveaux`, UI-002, ARCH-002, D-13): the `"level"` of a var, a step or a check above is the shape an export had until then. The level each line is printed from is `lib/line-levels.json`'s, read by Typst when it prints (docs/typst/report-engine.md §4); `level` became optional in the schemas, and every export writes the version that says so -- `calculations` 1.8, `steel` 1.2, `connectors` 3.3, `connections` 4.4, `scripts` 1.1 --, each holding what the versions before it held (links, drawings named from the root). An older export is still read, a line's own level then read where the table names it not. A table and a figure keep their own `level`: they are objects, not lines.
- `type`, `material`, and `dimension` are the position's own descriptive data (§7) — no shared catalog, no indirection. `material` is what the element is made of (`Fichte`, `Stahl`) and `strength_class` its strength class (`C24`, `GL24h`, `S355`), two columns since v0.77 (§7); `dimension` is **free descriptive text**, carried through exactly as typed in Excel (`"140/400"` for a cross-section, `"180"` for a panel thickness) — no `{b, h}` object. Dimensions a calculation needs are given manually in Typst, not read back out of this string (§7), with one lenient exception: a detail schema's element takes its default b and h from it (`schema.parse_section`, v0.75, §3.3decies). `units` is the sheet's own unit column for that text (`"mm"`), printed after it; it may be empty, in which case nothing is printed after the dimension.
- `moisture_class` (v0.36) is the element's moisture class (Feuchteklasse), `1`, `2` or `3`, or `null` where the sheet leaves it blank — the one field of a position a calculation reads as a number (§7). It is a class, not a quantity, so it carries no unit.
- `section_type` and `section` (v0.94, `position.schema.json` **1.3**): the type the sheet's `section type` column states, and what `calc/domains/section.py` read of the dimension for it — `type`, `kind` (`timber` or `steel`), the `text` a line prints («100/200 mm», «Ø 200 mm», «ROR 101.6×10») and every length in mm (`b`/`h`, `d`, `t`, a CLT panel's `layers`, a steel profile's `dims`). `null` where the type is empty and the dimension descriptive, which is what every position was until v0.94. It is written **once**, at the export, and nothing downstream reads `dimension` as a number again (§7).
- Loads (`snow`, `wind`, `dead load`, ...) **never appear here in any form** — not as a domain, not as a `load_id`, not as a line load derived from one, and not as the span or influence width that would be needed to derive one (§8). The load calculations themselves live in `calculations.json`, as domains whose instances are Excel sheets (§3.3), and stay there. Whatever mechanism eventually populates `domains` must respect this (§14).
- **Axes are no longer stored in this file** (the old `"axes": {"x": "3", "y": "C"}` field is gone): see §3.0 point 12 and §5 for the current approach.
- Every numeric value (`value`, `eta`, ...) carries an explicit `unit` field, including an empty string `""` for dimensionless quantities — never an implicit unit.
- `symbol` fields are authored as **Typst math source**, not plain text (§6bis): `"M_Ed"` would be looked up as an unknown variable in Typst math mode, so multi-letter subscripts that aren't a recognized symbol name (like `Ed`, `mod`, `lin`) must be quoted (`M_"Ed"`), and comma-grouped subscripts need parens (`f_(m,k)`). Single letters (`e`, `k`, `m`) and known Greek names (`gamma`, `mu`, `sigma`, `eta`) need no quoting — Typst renders them as real subscripts and Greek glyphs automatically.
- `source` says where a var's value comes from, as a prefix and a reference: `excel:<workbook>!<sheet>!<cell>` (a workbook's cell), `python:<module>` (computed by a module of `calc/` or a project's script), `norm:<edition, table>` (read off a norm table by Woodcore), `woodcore:<source file>` (an input saved in Woodcore's window, the connectors'). Every schema leaves it free text; the prefixes are named once, in `calc/variables.py`'s `PROVENANCE`, which the Variables tab reads to say *Excel* or *Woodcore* (v0.117, issue 13), and `tests/test_variable_sources.py` fails on a prefix of the example project that table does not name — a module writing a fifth kind adds it there. A var copied into a document's registry by `#var` keeps its `source`, and is shown as Typst's all the same.
- **Multiplication in `formula` strings uses `dot`, never `*`**: Typst math mode renders a literal `*` as the asterisk-operator glyph, not a multiplication sign. Write `q_"Ed" dot L^2` (renders as a centered dot, like `\cdot` in LaTeX), not `q_"Ed" * L^2`.

### 3.2 Section catalog — removed (v0.10)

There is no shared `data/sections.json` catalog anymore. `b`/`h` live directly on the position (`dimension`, §3.1); section properties that depend on geometry alone (e.g. the elastic section modulus `W`) are computed as a traced step inside the consuming domain instead of being looked up from a catalog — the elastic section modulus was such a step in `domains/bending.py`, which v0.59 deleted for having had no caller since v0.11 (§14).

### 3.4 Assigning loads to positions — removed (v0.10)

There is no `data/assignments.json`, no assignment schema, and no `loads/assignment.py` module anymore: **positions carry zero data-level link to loads.** See §8 for how a calculated domain that still needs a design load (e.g. the worked bending example) gets it instead.

### 3.6 Data validation (mandatory)

Before anything is exported to `data/`, **three levels of validation** must be implemented on the Python side, against the schemas defined in §3.0:

**3.6.1 Structure**
- presence of the required fields (`position`, `domains`, `schema_version`, etc.) as defined by the corresponding schema.

**3.6.2 Type**
- `value` is a number, or text for a var the workbook fills from a dropdown (§3.3bis),
- `unit` is a string (including empty),
- `axes` (when passed as an argument to Typst, see §5) and the other fields follow their declared type in the schema.

**3.6.3 Business rules**
- physical constraints where the sign is known (e.g. a check's `eta` is not negative, a layer's `Dist.` is not 0),
- allowed values (e.g. `Ce ∈ {1.0, 1.5}`, cf. `choices` in §3.3; a position's moisture class ∈ {1, 2, 3} or none, §7),
- combination consistency, once `combinations.py` exists (§3.5, §14): a ULS combination will have to reference calculations that exist in `calculations.json` — nothing checks it today, there being no combination,
- every name in an instance's `results` is a declared var whose value is a number or text — deliberately not required to be positive, a wind suction or an uplift being a negative result (§3.3quater).

👉 **Validation must happen on the Python side before export** — `export_all.py` fails explicitly (a blocking error, not a silent warning) if any of the three validations fails for a given file.

### 3.7 Levels (unchanged)

| Level | Meaning                       | Typical report      |
|-------|--------------------------------|-----------------------|
| 1     | Essential result                | Client report          |
| 2     | Important calculation           | Engineer report        |
| 3     | Full intermediate detail        | Review (checking) report |

👉 A fourth value exists and is **not** a report: **`level: 0` on a call prints nothing at all** (§10quinquies, v0.85). It is how a report declares a variable it does not want on the page — a coefficient a formula below will name — and it is per call only. The three above are the levels a *document* is compiled at.

👉 A fifth value, **`level: -1` with `shown: (A: 2, W_y: 1)`** (v0.117, issue #20), is not a report either: it prints the variables `shown:` names, each at its own level, and is per call only — the keys a command may name are `lib/shown-variables.json`'s (docs/typst/report-engine.md §4).

---
