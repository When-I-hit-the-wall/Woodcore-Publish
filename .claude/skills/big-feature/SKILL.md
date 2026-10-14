---
name: big-feature
description: Full Woodcore workflow for a substantial change — requirements extraction into a spec file, clarification questions, independent architecture review, one approval, implementation, tests and independent verification against the spec. Use for any new feature, command, tab, schema or calculation domain, any change spanning several modules or touching a data contract or an architectural rule, and for every dictated or transcribed request. Also resumes an interrupted spec when given a path in docs/requirements/active/.
argument-hint: "[transcription ou demande | docs/requirements/active/<fichier>.md]"
---

# big-feature — from a request to a verified change

The engineer's request is in `$ARGUMENTS` (a transcript, a message, or a path to a spec). Talk to him in **French**; write the spec in French and code, docs and comments in English (CLAUDE.md).

This skill orchestrates; each step's method lives in its own skill. Read that skill when you reach the step. Keep the spec file current at every step: it is what makes the work resumable.

## 0. Start or resume

- If `$ARGUMENTS` is a path under `docs/requirements/active/`, read it, read its frontmatter `status` and its **§16 Journal d'avancement**, say in one line where it stopped, and jump to the matching step below. Never redo a finished step unless the engineer asks.
- Otherwise start at step 1. If the request turns out to be small (one module, no contract, no architectural choice), say so and offer `small-feature` instead.

## 1. Requirements → `status: draft`

Follow the **`requirements`** skill: write `docs/requirements/active/<YYYY-MM-DD>-<slug>.md` from `docs/requirements/TEMPLATE.md`, with every point of the source captured or classified. Nothing is implemented in this step.

## 2. Clarification → `status: specified`

- Ask the open questions of §10 together, in one round (AskUserQuestion, recommended option first). Ask only what materially changes requirements, architecture, implementation or acceptance criteria; resolve the rest from the code and `docs/`.
- Record every answer in §10 and the decisions in §7; update the requirements and §12. Set `specified` when no source point is unresolved.

## 3. Architecture review and plan → `status: reviewed`

- Follow the **`architecture-review`** skill (it delegates the review to the `architecture-reviewer` agent, Sonnet). Its result goes into spec §13.
- Then write **§14 Plan d'implémentation** yourself: ordered steps, files touched, which REQ/UI/ARCH each step realises, the test that proves it. Apply every risk the review raised, or say in the plan why not.

## 4. The one approval → `status: approved`

Present in the chat, briefly: the objective, the requirements (IDs and one line each), the decisions taken, the architecture verdict and its main risks, the plan's steps, and what will **not** be done. Then ask once (AskUserQuestion): *Approuver et implémenter* / *Modifier* (say what) / *Arrêter* (→ move the spec to `rejected/` with the reason). Do not write code before the approval.

## 5. Implementation → `status: implementation` then `testing`

Follow the **`implementation`** skill. Update §16 after each plan step (items done), so an interruption loses nothing.

## 6. Verification → `status: verification` then `completed`

- Follow the **`verify-requirements`** skill (independent `requirements-verifier` agent, Sonnet). Its table goes into §15.
- For every ⚠️ or ❌: fix it, then verify again — at most two rounds; what remains is reported to the engineer, never hidden.
- When every criterion is ✅: tick §11, set `completed`, move the file to `docs/requirements/completed/` (git mv if tracked), and report in French: what was done, the tests run with their result, what was deliberately left out, and any decision recorded in `docs/decisions.md`.
- Then follow the **`finish`** skill: the full suite and its repair loop until green, one commit, one question «Pousser et fermer les issues ?», the push and the issues closed with a comment. Nothing is pushed without that answer (CLAUDE.md).

## Rules that hold through every step

- Several sessions may edit the repository: never `git checkout --`, `stash`, `reset` or `clean`.
- Delegate only where it pays (cheapest capable model): `code-scout` (Haiku) for locating code, the three Sonnet agents for their roles; the implementation stays in the main session.
- Every status change is a line in §16 with the date (`mis_a_jour` in the frontmatter too).
