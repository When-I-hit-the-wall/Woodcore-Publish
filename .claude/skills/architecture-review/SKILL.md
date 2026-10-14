---
name: architecture-review
description: Review a Woodcore specification against the existing architecture before any code is written — affected modules, code to reuse, duplication, hardcoding, domain logic in the UI, circular imports, data contracts and schema versions, i18n, the 16 design rules — and give a verdict with the risks to address. Step 3 of big-feature; usable alone on any spec in docs/requirements/active/.
argument-hint: "docs/requirements/active/<fichier>.md"
---

# architecture-review — check the spec against what exists

Input: a spec (`$ARGUMENTS`). Output: spec **§13 Revue d'architecture**, and the verdict in the chat.

## 1. Delegate the review

Spawn the **`architecture-reviewer`** agent (Sonnet, read-only) with:
- the spec path and its requirements (§3–§6);
- the `docs/` files listed in the spec's frontmatter `docs:`, plus `docs/architecture/principles.md` and `docs/architecture/layout.md`;
- the instruction to read the **code** those files describe, not just the docs.

For a change touching several unrelated areas (e.g. a domain module and a window tab and a Typst command), it is worth one reviewer per area in parallel; otherwise one.

## 2. What the review must answer

1. **Affected modules** — files and functions, with `path:line`; what each owns today.
2. **Existing code to reuse** — functions, widgets, patterns already doing part of the job (e.g. `identity.py`, `cards.py`, `grouped_list.py`, `source_archive.py`, `figure_style.py`, `render-table`, `find-calculation`, `var`/`eq`). A new helper beside an existing one is a finding.
3. **Risks**, each `ARCH-RISK-001…` with severity (bloquant / important / mineur), the place, and the fix:
   - duplicated source of truth (a value, a list, a word, a colour written twice; Python and Typst computing the same thing without a test holding them equal);
   - hardcoding (norm values outside `calc/norms/`, visible strings outside the glossaries, colours outside `theme.json`, paths outside `project.py`);
   - domain logic in the UI or in Typst where Python owns it, and the reverse;
   - circular or late imports (`calc-engine → bibliography → distance → formula`; `timber.typ` imports inside bodies; Qt in `calc/domains/`);
   - data contracts: a schema changed without `schema_version`, a field not additive, an old file no longer read, export no longer byte-reproducible;
   - the read-only guard (`WRITERS`), three languages, the documentation obligations of a Typst command (`///`, two compiling examples, `commands.json`);
   - a rule of `docs/architecture/principles.md` broken, or a settled decision of `docs/decisions.md` contradicted (grep it for the topic);
   - dead code left behind, needless abstraction, API inconsistent with its siblings, a solution that works now and will hurt later.
4. **Recommended approach** — the shape of the change in a few lines.
5. **Tests to add or extend** — `tests/test_*.py` by name.
6. **Verdict** — APPROUVER / APPROUVER AVEC RÉSERVES (list) / REVOIR (what must change in the spec first).

## 3. Record

Write the result into spec §13 (French headings, English code names), add any requirement the review made necessary as a new `ARCH-xxx` with source «revue», set `status: reviewed` only once the plan (§14) is also written (by `big-feature`), and log it in §16. A REVOIR verdict goes back to the engineer before the plan.
