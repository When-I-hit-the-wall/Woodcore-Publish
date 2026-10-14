# Requirements — specifications of work in progress

A **requirement is not a prompt.** What the engineer dictates or types is the *source*; the specification is what is extracted from it, classified, traced and agreed on before code is written. One file per feature, written in **French** (the engineer's language, his words quoted as he said them), from [`TEMPLATE.md`](TEMPLATE.md).

| Folder | Holds |
|---|---|
| `active/` | specifications being clarified, reviewed, implemented or verified |
| `completed/` | specifications whose every criterion was verified ✅ (moved here by `big-feature`, never deleted) |
| `rejected/` | specifications the engineer stopped, kept with the reason |

## File name and IDs

- File: `YYYY-MM-DD-<slug>.md`, e.g. `2026-10-07-report-editor.md`. The file name without `.md` is the spec's `id`.
- Inside a spec, items are numbered `REQ-001` (functional), `UI-001` (interface), `ARCH-001` (architecture), `CON-001` (constraint), `Q-001` (question), `T1, T2…` (numbered points of the source). Outside the file an item is cited `<spec id>#REQ-001`.
- An ID is never reused or renumbered, even when an item is dropped (mark it ~~struck~~ with the reason).

## Status (frontmatter `status:`)

```
draft → clarification → specified → reviewed → approved → implementation → testing → verification → completed
                                                                                                  ↘ rejected (any time)
```

| Status | Means | Next step (`/big-feature <file>` resumes here) |
|---|---|---|
| `draft` | extracted from the source, not yet clarified | ask the open questions |
| `clarification` | questions asked, answers awaited | record the answers |
| `specified` | every source point captured or classified, questions answered | architecture review |
| `reviewed` | architecture review and implementation plan written | ask for the one approval |
| `approved` | the engineer approved spec + review + plan | implement |
| `implementation` | code being written; the progress log lists the items done | continue with the first item not done |
| `testing` | code written, tests running | run/fix tests |
| `verification` | independent verification running or failed items being fixed | re-verify |
| `completed` | every acceptance criterion ✅ | move to `completed/` |

The **progress log** at the end of each spec records every transition with its date and the items done, so an interrupted session can resume exactly where it stopped. Small changes (`small-feature`) write no spec file.
