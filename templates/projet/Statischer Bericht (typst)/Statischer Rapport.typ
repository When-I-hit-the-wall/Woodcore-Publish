// Entry point: assembles the report from config, title page, and sections.

#import "config.typ": conf
#import "commands.typ": *
#import "title.typ": title-page
#show: conf
// The PDF's own metadata -- the project's name, the author and office, and the Woodcore and Typst versions that produced it -- from the project's .woodcore file (v0.82).
#show: woodcore-document

// The language of what the ENGINE prints: "de", "fr" or "en" (docs/typst/language.md §4bis) -- the labels of the calculations, the tables' headings and notes, the captions, the figures' legends, the STE legend of a position plan. Edit the default here; --input lang=fr forces it for one run, as --input level= does for the detail level.
//
// Two things it deliberately does not touch. What you enter: the descriptions and text values of the workbooks, the sheets' names, the positions -- and your own words in this file and in Sections/, the headings and the title and the prose, which are yours to write in the language you are writing the report in. And the language Typst itself works in -- «Abbildung»/«Fig.», the outline's title, the hyphenation -- which is declared in config.typ, by hand, beside the page setup.
#set-report-language(sys.inputs.at("lang", default: "de"))

// Report detail level, fixed at compile time: typst compile --input level=2 ...
#let default-level = int(sys.inputs.at("level", default: "2"))
#assert(
  default-level in (1, 2, 3),
  message: "invalid --input level=" + str(default-level) + ", expected 1, 2, or 3",
)
#report-level.update(default-level)

// The uniform variants in out/: typst compile --input uniform=2 renders EVERY show-* at level 2, ignoring the per-call `level:` overrides written in Sections/ -- so the PDF really is one level throughout. Absent, which is the normal case and the working report, those overrides apply as written on top of the base level above.
#let uniform = sys.inputs.at("uniform", default: none)
#if uniform != none {
  let uniform-int = int(uniform)
  assert(
    uniform-int in (1, 2, 3),
    message: "invalid --input uniform=" + str(uniform-int) + ", expected 1, 2, or 3",
  )
  uniform-level.update(uniform-int)
}

// Decimals on every number the engine prints -- show-calc, show-input, val, the layer tables, the checks, and any equation written by hand that prints its numbers with val. One knob for the whole report.
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
