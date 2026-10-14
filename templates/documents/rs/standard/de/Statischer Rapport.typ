// Entry point of the statical report: assembles the report from the project's config, a title page and its sections.
//
// The sections are the `#include` lines at the foot of this file, in the order they print: a section is one file `Sections/NNN-<name>.typ`, numbered in that order, and a line commented out with `//` is a section that is not printed. Woodcore writes these lines when a section is added, removed, moved or switched off; everything else in this file is yours.

#import "/config.typ": conf
#import "/commands.typ": *
#import "/title.typ": title-page
#show: conf
// The PDF's own metadata -- the project's name, the author and office, the versions that produced it -- and which revision journal `show-journal` prints: the report's own (docs/domain/journal.md §3.3terdecies).
#show: woodcore-document.with(document: "rs")

// The language of what the ENGINE prints: "de", "fr" or "en" (docs/typst/language.md §4bis). Edit the default here; --input lang=fr forces it for one run. Your own words in this file and in Sections/ are yours to write in the language of the report, and the language Typst itself works in is declared in config.typ.
#set-report-language(sys.inputs.at("lang", default: "de"))

// Report detail level, fixed at compile time: typst compile --input level=2 ...
#let default-level = int(sys.inputs.at("level", default: "2"))
#assert(
  default-level in (1, 2, 3),
  message: "invalid --input level=" + str(default-level) + ", expected 1, 2, or 3",
)
#report-level.update(default-level)

// typst compile --input uniform=2 renders EVERY show-* at level 2, ignoring the per-call `level:` overrides written in Sections/.
#let uniform = sys.inputs.at("uniform", default: none)
#if uniform != none {
  let uniform-int = int(uniform)
  assert(
    uniform-int in (1, 2, 3),
    message: "invalid --input uniform=" + str(uniform-int) + ", expected 1, 2, or 3",
  )
  uniform-level.update(uniform-int)
}

// Decimals on every number the engine prints. One knob for the whole report.
#number-digits.update(3)

// --- Title page ---------------------------------------------------------
// The title page is title.typ's, at the top of the project and shared by the three documents: its rows take the project's name, number, client, office and people from the .woodcore file, and the words it prints follow the document's language (config.typ's `doc-lang`). Edit it there, in VS Code -- the rows, the labels, the layout.
#title-page(document: "rs")

#outline()
#pagebreak()

// --- Sections ------------------------------------------------------------
#include "Sections/001-einleitung.typ"
#include "Sections/002-grundlagen.typ"
#include "Sections/003-baustoffe.typ"
#include "Sections/004-einwirkungen.typ"
#include "Sections/005-tragwerksanalyse.typ"
#include "Sections/006-nachweise.typ"
#include "Sections/007-literatur.typ"
#include "Sections/008-journal.typ"
// #include "Sections/009-anhang.typ"
