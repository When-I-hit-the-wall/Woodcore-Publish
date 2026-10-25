---
name: finish
description: End of a Woodcore task — the full test suite, then a repair loop that reruns only what failed and what the repair touched until the run is green, then one commit, one question «Pousser ?», the push, and the GitHub issues the task worked on closed with a comment. Last step of small-feature and big-feature; usable alone on finished work.
argument-hint: "[#issues…]"
---

# finish — green, committed, pushed, issues closed

Talk to the engineer in **French**. Issue comments are in French too (working notes, like the issues themselves); code names and paths stay as they are. Run everything from `Woodcore/`.

## 1. The issues this task worked on

The issues are those named in `$ARGUMENTS`, in the engineer's request (`#19`, «issue 20»), or in the spec's frontmatter or title (`docs/requirements/active/…-issues-github-19-20-21.md`). No issue named → none is closed; never guess one from its subject. For each, read it with its comments (`gh issue view <N> -R <owner>/<repo> --comments`; the repository from `git remote get-url origin`; `gh` may be `"/c/Program Files/GitHub CLI/gh.exe"`) and note which of its points (`- [ ]`) this task did.

## 2. The test loop

1. **Full suite once**, in the background, never as a foreground command that a tool timeout cuts off: `python tests/run_tests.py` (run with `run_in_background`, and wait for its notification; do not poll). It runs one file per process, all cores at once, and stops any test stuck past its limit (ten times its measured time, at least 30 s, at most `--test-timeout`, 300 s), naming it with its stack; a process that will not die is abandoned and named with its PID; and the whole run is capped at `--suite-timeout` (1800 s), past which it names what was still running and exits red — so it ends (issue #108). A test reported `FLAKY` passed only when replayed alone: say it to the engineer, it is not a failure. Its budget is **20 minutes**; a full run that takes longer is reported to the engineer with `--times`' slowest files, not ignored (issue #22).
2. **Green** → step 3.
3. **Red** → for each failure: read it (`-v` prints the traceback, and the stack of a stuck test), decide whether **this task** caused it (`git diff` of the task's files; a failure in a file the task did not touch and that fails the same way without the change is someone else's — report it, do not fix it silently).
   - Fix what the task broke, with targeted edits.
   - Rerun **only what matters**: `python tests/run_tests.py --related <each file the repair changed>` — the test files that name those modules **plus every test that failed in the previous run** (`tests/.last-run.json`). A repair that changed no code (only a test) reruns `--failed`.
   - Repeat until green. **At most three rounds**: what is still red after the third is reported by name with its output, and the task stops before step 4 — a red run is never committed, pushed or presented as green.
4. A test that fails without the task (flaky, another session's work in progress) is reported in one line each and does not block, **only** when its failure is shown to be independent of the task's files.

## 3. Commit

- Stage **only the task's own files**, by name (`git add <path>…`): several sessions work in this tree (`CLAUDE.md`), and `git add -A` would commit their half-done work. Never `git checkout --`, `stash`, `reset`, `clean`.
- One commit, message per `docs/conventions/changelog-and-commits.md`, naming the issues (`issue #22`), ending with the attribution lines the session gives.
- A pre-commit hook that fails is fixed, never skipped (`--no-verify` is not used).

## 4. One question, then push and close

Show, in a few lines: the commit (hash, title), the test result (passed / skipped, duration), and for each issue whether it will be **closed** (every point done) or only **commented** (some points left, listed). Then ask once with `AskUserQuestion` (header «Pousser», question «Pousser et fermer les issues ?»):

- **Pousser et fermer** — push, then close/comment as shown.
- **Pousser seulement** — push; the issues stay as they are.
- **Ne rien envoyer** — the commit stays local.

This question is the engineer's explicit word that `CLAUDE.md` requires before publishing; it covers this push and these issues only. The installer and the site are never published here (`docs/conventions/build-and-release.md`).

On «Pousser et fermer»:

1. `git push` (the current branch to its upstream). A refused push (behind the remote) → `git pull --rebase` is **not** run silently: say so and ask.
2. For each issue whose points are all done: write the comment to a UTF-8 file in the scratchpad (Write tool, never a heredoc), then `gh issue comment <N> -R <owner>/<repo> --body-file <file>` and `gh issue close <N> -R <owner>/<repo> --reason completed`. The comment:

   ```markdown
   Fait dans <hash court> (v0.xxx).

   - <point de l'issue> — <ce qui a été fait, fichier ou onglet>
   - …

   Tests : <N> passés, <M> ignorés, en <durée>.
   ```

3. For an issue with points left: the same comment, plus «Reste à faire :» and the points; the issue stays open.

## 5. Report

A short table: issue → fermée / commentée, with its link; the commit and the push; the test result. One line for anything not done and why.
