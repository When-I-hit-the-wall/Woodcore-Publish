---
name: implementation
description: Implement an approved Woodcore specification step by step following its implementation plan, keeping the spec's progress log current so the work can resume after an interruption, then run the tests and update the documentation. Step 5 of big-feature; refuses a spec that is not approved.
argument-hint: "docs/requirements/active/<fichier>.md"
---

# implementation — carry out an approved plan

Input: a spec (`$ARGUMENTS`) whose status is `approved`, `implementation` or `testing`. If it is earlier than `approved`, stop and say so: code is not written before the engineer's approval.

## 1. Read before writing

- The spec: requirements (§3–§6), decisions (§7), out of scope (§8), review (§13), plan (§14), and §16 to see which steps are already done — resume at the first step not done.
- Only the `docs/` files in the frontmatter `docs:` list, and the code the plan touches. Delegate a search to `code-scout` (Haiku) only when it is more than a grep.

## 2. Implement, one plan step at a time

For each step of §14:
1. Make the change with targeted edits; keep each file's line endings. Never `git checkout --`, `stash`, `reset`, `clean` — other sessions may be working in the tree.
2. Follow the review's risks and `docs/architecture/principles.md`: one source of truth, norm values in `calc/norms/`, words in the glossaries (fr/de/en), colours in `theme.json`, domain logic Qt-free in `calc/domains/`, a schema change with its `schema_version` and old files still read.
3. A new or changed Typst command: `///` block, a bullet per argument, `->` line, two compiling examples, category in `build_reference.CATEGORIES`, French and German in `calc/i18n/commands.json`.
4. Add or extend the tests that prove the step.
5. Append to spec §16: date, step, items (REQ/UI/ARCH) now done. This line is what lets an interrupted session resume.

If a step turns out impossible or wrong as planned, stop and tell the engineer what and why; do not quietly change the plan's scope.

## 3. Test → `status: testing`

Run the guarding files: `python tests/run_tests.py -k <name>` or `--related <changed files>` from `Woodcore/` (`docs/conventions/testing.md` lists what each guards). The full suite is run once, by the `finish` skill, after the verification. Fix what the change broke. Report anything else that fails by name, with its output — never present a red run as green.

## 4. Documentation

Update the `docs/` sections the change made wrong (keeping § anchors), `docs/decisions.md` for a settled decision, `docs/open-questions.md` for what is left, a `CHANGELOG.md` entry, and the «Nouveautés» page of the next version in fr/de/en (`docs/conventions/changelog-and-commits.md`). Large docs: targeted Edit only.

Then hand over to `verify-requirements`. Do not claim a requirement done here — the verifier decides. Committing and pushing are the `finish` skill's, after the verification.
