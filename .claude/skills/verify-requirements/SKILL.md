---
name: verify-requirements
description: Independently verify a Woodcore implementation against its specification — every REQ, UI, ARCH and CON item and every acceptance criterion checked in the code, the diff and the tests, not taken from the implementer's word — and report ✅ / ⚠️ / ❌ with evidence. Step 6 of big-feature; usable alone on any spec.
argument-hint: "docs/requirements/active/<fichier>.md [depuis <commit>]"
---

# verify-requirements — prove each requirement

Input: a spec (`$ARGUMENTS`), optionally the commit the work started from (else the first commit after the spec's `cree` date, else uncommitted changes against `HEAD`).

## 1. Delegate to an independent verifier

Spawn the **`requirements-verifier`** agent (Sonnet). Give it **only**:
- the spec path;
- the base commit (or «working tree against HEAD»);
- the test command `python tests/run_tests.py -k <names>` for the files the plan named.

Do **not** give it the implementer's summary or claims: it must find the evidence itself in the spec, `git diff`, the code and the test output.

## 2. What it must check

For every item of §3–§6 and every line of §11:
- **Where** it is realised (`path:line`) and **how** it can be observed (a test name and its result, a command's output, a value read back);
- that the criterion is met as written — not a weaker version of it;
- the documentation obligations (docs sections, `CHANGELOG.md`, «Nouveautés» fr/de/en, Typst command docs and translations), the three languages of every visible string, and that out-of-scope items (§8) were not done anyway;
- regressions: the guarding tests pass; anything red is named with its output.

Verdicts: ✅ realised and proved · ⚠️ partly realised, or realised without proof · ❌ not realised.

## 3. Record and act

- Write the table into spec **§15 Vérification** (Élément | Verdict | Preuve), tick the ✅ lines of §11, log the round in §16.
- Report to the engineer in French: the table's counts, every ⚠️/❌ with what is missing.
- Within `big-feature`: fix the ⚠️/❌ items and verify again (at most two rounds), then hand back.
