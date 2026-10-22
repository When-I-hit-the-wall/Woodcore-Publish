# CLAUDE.md — Woodcore

Woodcore generates structural calculation reports for timber (SIA 260/261/265, EC5) from Excel, Python and Typst: a program (this repository: `calc/`, `lib/`, `schemas/`, `templates/`, `tests/`, `packaging/`, `website/`) that reads and writes **projects** living in their own folders, each named by a `.woodcore` file. A project is written as up to three documents — convention d'utilisation, base de projet, rapport de statique — compiled by Typst from data Python validated and exported. Woodcore's window (PySide6) is where the engineer draws plans, schemas, static models, connectors and member checks.

This file is the entry point and stays short. The reference is **`docs/`** — read [`docs/README.md`](docs/README.md) to find the file a task needs, and read only that.

## Core principles

- **One source of truth.** No value copied by hand; the norm is read from `calc/norms/`, the project's data from its own files. A copy that ages without saying so is the defect this project fears most.
- **Domain logic is independent of the UI.** Calculations live in `calc/domains/` (Qt-free); a tab shows, edits and calls them, never recomputes. Typst prints what the export holds.
- **No hardcoding.** Norm values live in `calc/norms/*.json`, words in three languages (de, fr, en) — the report's in `calc/i18n/`, the window's beside its tab in a `STRINGS` table (`calc/tools/*_words.py` or the tab's module), merged by `woodcore_gui_words.py` and held to the three languages by `tests/test_i18n.py` —, colours in `calc/tools/theme.json`, contracts in `schemas/`.
- **Explicit, versioned data models.** Every exported JSON follows a schema with `schema_version`; every value has a unit and a provenance; data is validated before anything is written.
- **SIA calculations stay traceable.** Every step cites its norm and clause; a value from a norm is read off a named edition in `ExternalFiles/000-Normes/`, never from memory.
- **Preserve the architecture** unless there is a stated, justified reason to change it; when it changes, `docs/decisions.md` (§13) says why and what it costs.
- **A missing input warns, a malformed file stops.** What the project lacks is a warning and a reason in the report; a defect in a file Woodcore wrote stops the export, naming the file and the field.
- **The engineer designs the command surface.** For a new command, argument, tab or data shape, give him the options, their trade-offs and what each would lose; do not decide it silently.
- The full set of 16 design rules is `docs/architecture/principles.md` (§2) — read it before any change to data, commands or architecture.

## How to handle a request

Classify every Woodcore request first, and say in one line which mode you chose:

| Mode | When | What to do |
|---|---|---|
| **Question** | explanation, a value, how something works | Answer from the relevant `docs/` file and the code. No workflow. |
| **Small change** | local fix or adjustment: one module or tab, no new data contract, command, tab or schema, no architectural choice | Follow the `small-feature` skill: acceptance criteria in chat → implement → test → verify each criterion. No approval needed. |
| **Substantial change** | new feature, command, tab, schema or domain; several modules; a change to a data contract or to an architectural rule; a dictated/voice request or a transcript | Follow the `big-feature` skill: requirements → spec in `docs/requirements/active/` → architecture review → **one approval** → implement → test → independent verification. |

`/big-feature` and `/small-feature` force a mode. When unsure between the two, prefer `big-feature` for anything that touches more than one module or a contract. A spec interrupted mid-way is resumed with `/big-feature docs/requirements/active/<file>.md`: its frontmatter `status` says where it stopped.

**Questions.** Ask only those whose answer materially changes the requirements, the architecture, the implementation or the acceptance criteria; never ask what the code or `docs/` can answer. Ask them together, with a recommended option first.

**Subagents.** Use them only when parallel investigation or an independent check pays for itself; never for trivial or strictly sequential work. Cheapest capable model: `code-scout` (Haiku) to locate code, `requirements-analyst`, `architecture-reviewer` and `requirements-verifier` (Sonnet) for their roles; implementation stays in the main session.

## Non-negotiable working rules

- **Several Claude sessions edit this repository at once.** Never `git checkout --`, `git stash`, `git reset` or `git clean`, not even on one path. Make targeted edits; coordinate with peers (SendMessage) before touching a file another session is changing.
- **Large files are edited, never rewritten.** `docs/decisions.md` (400 KB) and `CHANGELOG.md` are the large ones: targeted Edit only, keeping the file's line endings. Every text file is LF, on every machine (`.gitattributes`); only the `.bat` files are CRLF. No other file of `docs/` may pass 100 KB (`tests/test_docs_coherence.py`): split it by subject, or move what is history to `docs/history/` verbatim.
- **Prose is not hard-wrapped**: one paragraph is one line, in every file (`docs/conventions/writing.md`). Code, docs and comments are in English; the window and the report speak de/fr/en through the glossaries.
- **A change is finished when its documentation is**: the `docs/` sections it changed, a `CHANGELOG.md` entry, the «Nouveautés» page of the next version in three languages, and for a Typst command its `///` block, two compiling examples and its translation in `calc/i18n/commands.json` (`docs/conventions/changelog-and-commits.md`, `docs/typst/command-docs.md`).
- **Tests**: `python tests/run_tests.py [-k name | --related <files> | --failed]` from `Woodcore/` (`docs/conventions/testing.md`; a new machine is prepared by `python tests/bootstrap.py`; a new test file takes a row in `docs/conventions/testing-catalogue*.md`). Run the files that guard what changed while working, the full suite once at the end (in the background; it runs files in parallel and stops a stuck test); report failures with their output and their names.
- **Commit at the end of a task through the `finish` skill, or when asked; publishing (installer, site, push) always waits for the engineer's explicit word** — for a push and the issues it closes, the one question `finish` asks (`docs/conventions/build-and-release.md`).
- Never write into the engineer's own projects (e.g. `../Musterprojekt/`) except on his explicit request; tests work on `tests/projet-exemple/`.

## Where things are

| Need | Read |
|---|---|
| Find the right file | `docs/README.md` (every § → its file) |
| Pipeline and design rules | `docs/architecture/principles.md` |
| Folders and modules | `docs/architecture/layout.md` |
| A calculation domain | `docs/domain/<topic>.md` |
| A Typst command | `docs/typst/api-conventions.md`, `docs/typst/formulas.md` |
| A tab of the window | `docs/ui/tab-<tab>.md`, listed in `docs/ui/window.md` (the frame) |
| Why something is the way it is | `docs/decisions-index.md`, then grep `docs/decisions.md` |
| What is not done yet | `docs/open-questions.md` (grep) |
| Work in progress | `docs/requirements/active/` |
| What changed recently | the newest entries of `CHANGELOG.md` |
