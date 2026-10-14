# Writing conventions

> Prose is not hard-wrapped: one paragraph is one line, in every file.
>
> Moved verbatim from CLAUDE.md (§1ter) on 2026-10-07. The § numbers are kept as stable anchors: `docs/README.md` maps every § to its file.

## 1ter. Writing conventions — prose is not hard-wrapped

**One paragraph is one line.** Prose is written unwrapped and the editor soft-wraps it; there are no manual line breaks every few words. This holds for every file this project owns: `CLAUDE.md` and `README.md`, Python comments and docstrings, Typst `//` and `///` comments, the German report text in `Sections/*.typ`, and the body of a commit message.

A line break then means something — it ends a paragraph, a list item, or a line of code — instead of recording where a 72-column ruler happened to fall. That is what keeps a diff honest: editing one word changes one line, not the six lines a reflow pushed around, so `git diff` and `git blame` point at the actual change rather than at the wrapping.

What keeps its own line structure, all of it structural rather than cosmetic:

- **Code.** This rule governs prose, not statements; a language's own line-length habits are unaffected.
- **Markdown tables**, one row per line, and **fenced or indented code blocks**, verbatim.
- **List items**, one per line — joining two items would merge two thoughts, which is not the same operation as unwrapping one.
- **A break that carries meaning**: a Typst `\` line break, or an enumeration deliberately set one entry per line.

👉 The convention was applied to every file at once in v0.19, not left to trickle in edit by edit. Nothing but line breaks moved: each file was checked before and after with its whitespace and its comment markers normalized away, and the two texts are identical.

---
