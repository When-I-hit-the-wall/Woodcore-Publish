// **Form «neutral»** (templates/forms/neutral, calc/forms.py): the look of the project's three documents -- A4, margins of 2.5 cm, justified 11 pt text, numbered headings, the page number centred in the footer, no colour and no decoration. It is the form Woodcore writes into `Template/` when a project is made, and a *form* is the layout alone: no project data lives here -- no name, no client, no figure -- which is what lets one form serve any project, and the title page that goes with it (`title.typ`, at the top of the project) hold the data.
//
// Woodcore switches the form (the old `Template/` and `title.typ` go to the archives, never deleted), so do not keep your own edits in this file: write them in `config.typ`, in the place it marks, where they win over the form's.
//
// Keep this file free of *state*: no `context`, nothing that reads report-level or the report language, no custom pagination logic -- that is what lets it stay the plain styling file it is (docs/typst/language.md §4bis).

/// The look of a document: `#show: template.with(lang: "de", region: "CH")`, which `config.typ` does for the three documents.
/// - doc (content): the document.
/// - lang (str): the language Typst itself works in -- the hyphenation patterns, the quotation marks, the words it writes of its own accord («Abbildung»/«Fig.», the outline's title).
/// - region (str): its region.
/// -> content
#let template(doc, lang: "de", region: "CH") = {
  set page(
    paper: "a4",
    margin: (top: 3cm, bottom: 2.5cm, left: 2.5cm, right: 2.5cm),
    numbering: "1",
    footer: context align(center, counter(page).display("1")),
  )

  set text(size: 11pt, lang: lang, region: region)
  set par(justify: true)
  set heading(numbering: "1.1")
  // The white before and after a heading (v0.100, the engineer: «augmente les espacements avant une nouvelle section, sous-section, ===, ====»). A show-set rule per level rather than one `set heading(above:, below:)`, because each level wants its own: a section is set apart from what precedes it more than a sub-sub-section is, which is what makes the structure readable at a glance. Typst's own default is about 1.2em above and 0.55em below at every level, which is what made a «===» sit as close to its text as a «=» did.
  show heading.where(level: 1): set block(above: 2em, below: 1em)
  show heading.where(level: 2): set block(above: 1.6em, below: 0.8em)
  show heading.where(level: 3): set block(above: 1.2em, below: 0.6em)
  show heading.where(level: 4): set block(above: 1em, below: 0.5em)

  // A `*` typed in math prints as the multiplication dot, as `#eq` and `#verify` print it (v0.87): $q * L$ reads q · L. A star in a sub- or superscript stays a star -- F* of the most unfavourable superposition, x* -- and so does one in the text.
  show math.equation: it => { show "∗": sym.dot.op; it }
  show math.attach: it => { show "⋅": sym.ast; it }

  // Display math as "display" (shows better in text)
  show math.frac: it => $display(it)$

  // To have every figure read «Figure 1» rather than Typst's own word for the language above -- «Abbildung 1» in German, «Fig. 1» in French -- say so in config.typ:
  //   set figure(supplement: [Figure])

  doc
}
