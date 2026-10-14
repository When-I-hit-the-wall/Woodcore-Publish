---
name: issue
description: Turn the engineer's raw list of problems and wanted changes into GitHub issues for Woodcore — sorts every point by category and by subject (tab, domain, command), rewrites it precisely, asks each open question as a clickable multiple-choice question (one after another, no limit on their number), then creates the issue or adds the points to the issue that already covers that subject (e.g. «Plan de positions»). Shows the plan and waits for one approval before touching GitHub. Use only when the engineer types /issue; it files requests, it never implements them.
argument-hint: "[liste des problèmes et modifications]"
disable-model-invocation: true
---

# issue — from a raw list to tidy GitHub issues

The list is in `$ARGUMENTS`. If it is empty, answer in one line that you are ready (**«Envoie la liste, je trie»**) and take the engineer's **next message** as the list. Talk to the engineer in **French**; issues are written in **French** too (they are working notes, like the specs in `docs/requirements/`); code names, file paths and Typst commands stay as they are.

This skill **files** requests. It does not implement them, does not write a spec, does not touch the code or `docs/`.

## 1. Prepare GitHub (read-only)

- Repository: `git remote get-url origin` → pass `-R <owner>/<repo>` to every `gh` call. Never write a name down.
- `gh` may not be on the PATH of Git Bash: try `gh`, then `"/c/Program Files/GitHub CLI/gh.exe"`.
- `gh auth status`. **Not logged in → do steps 2–5 anyway, show the plan and the drafts in the chat, and stop** with: «`gh` n'est pas connecté : lance `gh auth login`, puis redis `/issue` ou dis-moi de poursuivre.» Never ask for a token, never use `WOODCORE_GITHUB_TOKEN` (that one belongs to the releases repository, `packaging/publish.py`), never put a token in a command.
- Fetch what exists: `gh issue list --state all --limit 200 --json number,title,state,labels,body` and `gh label list --limit 100 --json name,description`. These are the only labels you may use; one that is missing goes into the plan (step 5) and is created only after approval.

## 2. Split and sort

Cut the list into **atomic points** (one wish, one defect, one question each) and give every point:

- a **subject** — the tab, domain or command it concerns, named as the window and `docs/ui/window.md` name it («Plan de positions», «Vérification flexion», «Onglet Formule»…). A quick grep in `docs/README.md` / `docs/ui/window.md` fixes the exact name; do not read more. A point that fits no subject goes under «Général».
- a **category**, one of: `bug` (something works wrongly), `amélioration` (something works, should work better), `fonction` (something new), `documentation`, `tests-outillage`, `question` (a decision is needed before anything can be done). Use the repository's existing label for each when one matches; otherwise propose the label in the plan.

Merge duplicates inside the list. A point that holds two requests becomes two points. Do not drop a point, ever: what cannot be sorted goes under «Général» / `question`.

## 3. Reformulate

Rewrite each point so that someone who was not in the room can act on it:

- Imperative or observable, one sentence; the engineer's intent, not yours. **Never invent** a cause, a reproduction step, a value or a norm clause. For a `bug` keep what was said, in the shape *observé / attendu / pour reproduire* — leave out a part the engineer did not give.
- Use the project's vocabulary (the glossaries, the tab names). Name the file or `docs/` § only when you looked it up.
- **The engineer designs the command surface.** A new command, argument, tab or data shape is never decided here: write the point as a need and note a *question ouverte* if the wording hints at a choice (it is asked in step 4, not left as prose).
- A fuzzy point stays faithful and gets a *question ouverte*; it is not guessed.

Keep a list of the open questions as you go: each one with its point, its wording, and the options you can ground (see step 4).

## 4. Ask the open questions — one clickable question at a time

Every open question collected in step 3 is asked **with the `AskUserQuestion` tool**, not written as prose for the engineer to answer in a message. Ask **before** matching and showing the plan, so the plan already carries the answers.

- **One question per call, in order**, so the engineer clicks an answer and lands on the next question. **There is no limit to the number of questions**: the 4-question cap is per call, not per session — make as many calls as there are questions. Never drop or merge questions to stay under a number.
- **Options (2–4) exist only when you can ground them**: they come from the engineer's own wording («option A / option B»), from a choice the wording hints at, or from what `docs/` / the code say (looked up, never recalled). Each option gets a short label and a description with its trade-off and what it would lose (`CLAUDE.md`: the engineer designs the command surface). `multiSelect: true` when the options are not exclusive. Mark one «(Recommended)» and put it first only when the engineer's text or the docs point to it; never to push your own design. The tool always offers «Other» for free text.
- **No grounded option → no invented ones.** The tool needs at least two options, so ask such a question as **plain text in the chat** («Question N/M — … Réponds par une phrase.»), alone in the message, and wait for the answer before the next question.
- `header` = the subject (max 12 characters); `question` = the point in the engineer's vocabulary, ending with «?».
- **Fold each answer into its point**: a chosen option makes the point concrete (the decision is stated in the point, with no *Question ouverte* left); a free-text answer is kept faithfully and, if it still leaves a choice open, is asked again once at most. A question the engineer skips or answers «je ne sais pas» stays a *Question ouverte* in the issue, with its options written out.
- Number the questions («Question 3/9») in the `question` text so the engineer knows how many remain. If there is no open question, skip this step silently.

## 5. Match against the existing issues, then show the plan

For each subject, look for an existing issue whose **title or body covers the same subject** (compare meaning, not spelling: «plans de positions» = «Plan de positions»).

- **Open issue found** → the points are **added** to it.
- **Only a closed one found** → never reopen silently: new issue, citing the closed one («Suite de #N»).
- **Nothing** → new issue.
- Doubt between two issues → say so in the plan and propose the likelier one.

Show **one table** in the chat:

| Sujet | Action | Issue | Labels | Points |
|---|---|---|---|---|
| Plan de positions | Compléter | #12 | amélioration | 3 |
| Vérification flexion | Créer | — | bug, amélioration | 2 |

Under it, for each row, the reformulated points with the answers of step 4 already folded in (and, for a creation, the proposed title); a question left unanswered is listed there as *Question ouverte*. Add the labels to create, if any.

Then, once the table and the points are written out (so the engineer reads them first), ask once for approval **with `AskUserQuestion`** (one question, header «Plan», question «Envoyer ce plan à GitHub ?») with these options:

- **Valider et envoyer** — the plan is sent exactly as shown.
- **Corriger une ligne** — merge, split, other issue, other category: the engineer then says which row and how in free text («Other» also accepts it directly).
- **Annuler** — nothing is sent.

On a correction, apply it, show only what changed and ask the same approval question again. «Annuler» ends the skill with nothing sent.

**Nothing is sent to GitHub before this approval** — creating, commenting and labelling are outward-facing (`CLAUDE.md`: publishing waits for the engineer's word). Approval covers exactly the plan shown.

## 6. Write to GitHub

Write each body to a UTF-8 file in the scratchpad directory with the Write tool (never a heredoc, never inline text in the command line: quoting and backslashes break on this machine) and pass it with `--body-file`.

**New issue** — title: the subject as a short noun phrase, no verb, no category («Plan de positions»); the category is a label.

```markdown
## Contexte
<one or two lines: the tab / domain, `docs/…` § if looked up>

## Demandes
- [ ] <point, reformulated>
- [ ] <point>

## Questions ouvertes
- <question — option A / option B>
```

*Questions ouvertes* holds only the questions the engineer left unanswered in step 4 (with their options); leave the section out when there is none. A `bug` point carries *observé / attendu / pour reproduire* as indented lines under its checkbox.

Create with `gh issue create --title … --body-file … --label a --label b`.

**Existing issue** — add a **comment**, never rewrite the body (another session or the engineer may have edited it; the comment keeps the history):

```markdown
### Ajouts du <YYYY-MM-DD>
- [ ] <point>
- [ ] <point>

**Questions ouvertes** (if any)
- …
```

`gh issue comment <N> --body-file …`, then add the labels the issue lacks (`gh issue edit <N> --add-label …`). Never remove a label, close, reopen or reassign.

If one call fails, say which and why, keep going with the others, and list what was not done at the end.

## 7. Report

A table, nothing else: subject → issue number and link (`[#12](https://github.com/<owner>/<repo>/issues/12)`), «créée» / «complétée», the number of points. Then one line for anything left undone. Do not start working on the issues.
