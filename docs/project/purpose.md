# Purpose and choice of stack

> What Woodcore is for, and why Typst + Python + JSON + Excel rather than a web app.
>
> Moved verbatim from CLAUDE.md (§1, §1bis) on 2026-10-07. The § numbers are kept as stable anchors: `docs/README.md` maps every § to its file.

## 1. Purpose

Build a structural calculation report engine (timber, SIA/EC5) that allows:

- importing results calculated in Excel or Python as variables in Typst,
- automatically displaying either just the result, the detail, or the full calculation chain, with a **global default level, overridable per calculation**,
- also performing one-off calculations directly in Typst, rendered the same way as Python calculations,
- linking **every calculation to a position number from the layout plan** (`T001`, `S002`, ...) **and to its plan axes (X, Y)**, displayed automatically,
- describing each position by its own **type, material, and section** (dimensions) — no shared catalog, no load ever assigned to a position (§7-§8),
- systematically citing the **norm and norm clause** used,
- documenting the meaning of input parameters (e.g. `Ce=1.0` if exposed, `1.5` if sheltered),
- retrieving **any intermediate variable**, at any time, from anywhere in the Typst report.

The same engine must produce several reports (client, engineer, review) from the **same data**, without duplicating logic.

---

## 1bis. Why this stack rather than a dedicated web app

Deliberate decision: Typst + Python + JSON + Excel rather than a custom web application (in the style of Calcs.com / CalcTree).

**Reasons:**
- No infrastructure to maintain (server, database, authentication, hosting) for a use case that is fundamentally local and sequential.
- Text files versioned in Git = native normative traceability (proof, years later, of which values and which version of the engine produced a given PDF).
- Excel remains the input interface engineers already know.
- No dependency on the commercial survival of a SaaS vendor, for a tool that must stay usable over the very long term (review by a checking engineer years later).

**Limits to keep watching regardless** (infrastructure simplicity doesn't excuse software rigor in `engine.py` / `calc-engine.typ`):
- **Version the norm edition used per project**: if the tables in `norms/*.json` evolve (an SIA revision), it must be possible to say which commit/hash produced a given report — freeze/tag the version on every export.
- **Multi-user collaboration**: JSON files edited in parallel by several engineers on the same project can create Git merge conflicts; acceptable for a single author per project, worth watching if usage grows.

---
