// lib/calc-engine-records.typ -- the live loads of SIA 261 Tabelle 8 and the report's revision journal.
// Split out of lib/calc-engine.typ by subject, its text moved and not rewritten (spec docs/requirements/active/2026-10-19-base-saine-nettoyage.md, G9). Each part imports the one before it, so a name reads everything defined above it as it did in one file; lib/calc-engine.typ imports the last and is what every caller names.

#import "calc-engine-display.typ": *

// --- Nutzlasten, read off SIA 261's Tabelle 8 (docs/domain/loads.md §3.3septies)
// A live load is neither calculated nor entered: it is looked up, by the category of Nutzfläche a surface belongs to (A1 Wohnflächen, A3 Treppen, B Büroflächen, ... H nicht begehbare Dächer), and the norm's table gives the Flächenlast q_k and the Einzellast Q_k. So the instances of the `live-load` domain are the rows of that table, and the two functions below address one by its category. What they read is the ordinary {vars, tables, results} record every calculation has, exported by calc/domains/live_load.py -- show-calc, var-of and value-of work on this domain unchanged; these two are how the report says it in one line, and how a sentence quotes one of the two values.

// `live-load` stood here until v0.80: one of the two values of a category of Nutzfläche, inside a sentence. It is `val("q_k", domain: ("live-load", "A1"))` now -- exactly as long, since the domain is a named argument, and one command less to remember (section 13). `show-live-load` keeps the category's own line, its notes and Tabelle 8 above it.

// --- The report's revision journal (docs/domain/journal.md §3.3terdecies) -----------
// One entry per revision of the report, written by hand in Woodcore's «Journal» tab and read here: its number, the day, who made it and the office's short form, then the three texts the levels govern -- the label at 1, the short description as well at 2, and everything at 3 (the engineer's decision 6.5).
//
// Nothing is computed. The export is the source's entries sorted, and this prints them: there is no {vars, steps, checks} record behind a journal, so nothing addresses one with show-calc, which is the rule a static model and a detail schema already follow.
// `load-journal` -- which reads one document's journal, `journal-files` and `wc-document` -- is declared with `woodcore-document` near the top of this file, which needs it for the PDF's keywords.

/// Every revision of the report, **newest first** -- the largest index first, which is the order `calc/journal.py` exports them in. Data access, not a display function: `journal-entries().first()` is the revision the report is at, and what the PDF's keywords name (project-info's `revision`).
///
/// ```typ
/// #journal-entries().len()
/// ```
///
/// ```typ
/// #for e in journal-entries() [ Rev. #e.index — #e.label \ ]
/// ```
///
/// Each entry carries `index`, `date` (ISO), `name`, `initials`, `label`, `summary` and `description`, the last two "" where the revision has none. Ordered by the index and never by the date: the date is typed, so it may be wrong, and a journal that reordered itself around a typo would print a revision under the wrong one.
///
/// Each of a project's documents has its own journal. `document:` says which one this reads: the statical report's (`"rs"`, the default, so that the call works outside a `context`, as it always has), the convention d'utilisation's (`"cu"`) or the base de projet's (`"bp"`); `auto` is the document being compiled -- the `document:` its entry file gave `woodcore-document` -- which Typst can only tell inside a `context`.
///
/// - document (str, auto): `"rs"`, `"cu"`, `"bp"` or `auto`. The default is `"rs"`, and **not** `auto`: a function that returns an array cannot ask a state, so `#journal-entries()` in a convention d'utilisation gives the statical report's entries unless it is written `#context journal-entries(document: auto)`. `show-journal` does follow the document by itself.
/// -> array
#let journal-entries(document: "rs") = load-journal(document: document).entries
