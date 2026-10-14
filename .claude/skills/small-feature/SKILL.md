---
name: small-feature
description: Light Woodcore workflow for a small, local change — a fix or adjustment confined to one module or tab, with no new data contract, Typst command, tab or schema and no architectural choice. States 3–8 acceptance criteria in the chat, implements without waiting for approval, tests, then checks every criterion with evidence. Use for such requests; escalate to big-feature when the change turns out larger.
argument-hint: "[demande]"
---

# small-feature — a small change, still verified

The request is in `$ARGUMENTS`. Talk to the engineer in **French**; code, docs and comments stay in English.

## 1. Understand (no file written)

- Restate the request in one sentence and list **3 to 8 acceptance criteria** in the chat (`C1`…`C8`), each observable: a value, a behaviour, a test. Include the documentation a change of behaviour needs (the `docs/` section, `CHANGELOG.md`, translations).
- Read only the `docs/` file that covers the area (find it in `docs/README.md`) and the code concerned. Use `code-scout` (Haiku) only if locating the code is not a quick grep.
- If the answer to an open point would change the criteria, ask it (one round, AskUserQuestion). Otherwise proceed without approval.

**Escalate** to `big-feature` (say so in one line) as soon as the change needs a new or changed schema, Typst command, tab or domain, touches more than one module's responsibilities, or raises an architectural choice.

## 2. Implement

- **A bug starts with a red test.** Reproduce it first: write the test that fails for the reported reason (run it and read the failure, so you know it fails for the right one), then fix, then see it go green. The test stays as the guard. If the bug cannot be reproduced by a test (window, rendering), say so and name the manual check that stands in for it as a criterion.
- Respect `docs/architecture/principles.md`: one source of truth, no hardcoded norm values / words / colours, domain logic out of the UI, three languages for every visible string.
- Targeted edits; keep each file's line endings; never `git checkout --`, `stash`, `reset`, `clean` (other sessions work here).
- Update the `docs/` section the change makes wrong, and add or extend a test where a behaviour changed.

## 3. Test

While working, run the guarding test files: `python tests/run_tests.py -k <name>` or `--related <changed files>` from `Woodcore/`. Report failures by name with their output; a failure you did not cause is reported, not hidden. The full suite comes once, at the end (step 5).

## 4. Verify

Re-read the diff (`git diff`) against each criterion and answer in the chat:

| Critère | Verdict | Preuve |
|---|---|---|
| C1 | ✅ / ⚠️ / ❌ | fichier:ligne, test, sortie |

Fix what is ⚠️/❌ once; report what remains.

## 5. Finish

Follow the **`finish`** skill: the full suite, the repair loop until green, one commit, one question «Pousser et fermer les issues ?», then the push and the issues closed with a comment.
