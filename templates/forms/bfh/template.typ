// **Form «bfh»** (templates/forms/bfh, calc/forms.py): the look of the project's three documents in the Berner Fachhochschule's academic style -- the BFH's colours, its logo in the running header, the school's names in the footer, a chapter on a page of its own. A *form* is the layout alone: no project data lives here -- no name, no client, no figure -- which is what lets one form serve any project, and the title page that goes with it (`title.typ`, at the top of the project) hold the data; the department, the programme and the place it prints are title.typ's.
//
// **All the text is set in Lucida Sans** (Segoe UI, then Arial, where it is not installed), as the BFH's Word template does -- the body, the tables, the captions, the outline, the headings, the header and the footer. Only the formulas keep Typst's own math font, and code its monospaced one.
//
// Woodcore switches the form (the old `Template/` and `title.typ` go to the archives, never deleted), so do not keep your own edits in this file: write them in `config.typ`, in the place it marks, where they win over the form's.
//
// Keep this file free of *state*: no `context` beyond the running header's own, nothing that reads report-level or the report language, no custom pagination logic -- that is what lets it stay the plain styling file it is (docs/typst/language.md §4bis).

// --- The school -------------------------------------------------------------
// What the footer says of the school, in its three names. The department, the programme and the place the title page prints are title.typ's, in the document's language, with the rest of the title page.
#let school-names = ("Berner Fachhochschule", "Haute école spécialisée bernoise", "Bern University of Applied Sciences")

// --- BFH identity -----------------------------------------------------------
#let bfh-grey = rgb("#697D91")    // the grey-blue of the logo and of the BFH's Word template
#let bfh-yellow = rgb("#FAC300")  // the yellow of the F and the H, used once per chapter, never for text
#let muted = luma(95)

// Lucida Sans for everything, as the BFH's Word template; Segoe UI and Arial where Lucida Sans is not installed.
#let sans = ("Lucida Sans", "Segoe UI", "Arial")

// The running header of every page after the title page: the BFH logo on the left, the current chapter on the right -- the chapter starting on this page, else the last one started before it.
#let report-header() = {
  set text(font: sans, size: 7.5pt, fill: muted)
  grid(
    columns: (auto, 1fr),
    align: (left + bottom, right + bottom),
    image("logo-bfh.png", height: 0.95cm),
    context {
      let chapters = query(heading.where(level: 1, outlined: true))
      let here-page = here().page()
      let on-page = chapters.filter(h => h.location().page() == here-page)
      let before = chapters.filter(h => h.location().page() < here-page)
      let current = if on-page.len() > 0 { on-page.first() } else if before.len() > 0 { before.last() } else { none }
      if current != none {
        if current.numbering != none { numbering(current.numbering, ..counter(heading).at(current.location())) + "  " }
        current.body
      }
    },
  )
}

// The footer, as the BFH's Word template: the school's names on the left, the page on the right.
#let report-footer() = {
  set text(font: sans, size: 7.5pt, fill: muted)
  line(length: 100%, stroke: 0.4pt + bfh-grey)
  v(-0.5em)
  grid(
    columns: (1fr, auto),
    align(left, school-names.join("  |  ")),
    align(right, context counter(page).display()),
  )
}

/// The look of a document: `#show: template.with(lang: "de", region: "CH")`, which `config.typ` does for the three documents.
/// - doc (content): the document.
/// - lang (str): the language Typst itself works in -- the hyphenation patterns, the quotation marks, the words it writes of its own accord («Abbildung»/«Fig.», the outline's title).
/// - region (str): its region.
/// -> content
#let template(doc, lang: "de", region: "CH") = {
  set page(
    paper: "a4",
    margin: (top: 3.2cm, bottom: 2.5cm, left: 2.5cm, right: 2.5cm),
    header-ascent: 35%,
    numbering: "1",
    // The BFH's running header and footer on every page of the three documents -- the logo and the current chapter above, the school's names and the page below. The title page (title.typ) is a page of its own with neither.
    header: report-header(),
    footer: report-footer(),
  )

  set text(font: sans, size: 10.5pt, lang: lang, region: region)
  set par(justify: true, leading: 0.68em, spacing: 1.1em)
  set heading(numbering: "1.1")

  // Headings: in the BFH's grey-blue.
  show heading: set text(fill: bfh-grey, weight: "bold")
  show heading.where(level: 2): set text(size: 12pt)
  show heading.where(level: 2): set block(above: 1.8em, below: 0.9em)
  show heading.where(level: 3): set text(size: 10.5pt)
  show heading.where(level: 3): set block(above: 1.5em, below: 0.8em)

  // A chapter: a page of its own, its number beside its title in a lighter grey, a short yellow bar below. `weak`: no blank page where one already begins there.
  show heading.where(level: 1): it => {
    pagebreak(weak: true)
    v(0.3cm)
    block(below: 0.9cm, {
      set block(spacing: 0.7em)
      set text(font: sans, size: 18pt, weight: "bold")
      if it.numbering != none {
        text(fill: bfh-grey.lighten(45%), counter(heading).display(it.numbering))
        h(0.5em)
      }
      text(fill: bfh-grey, it.body)
      line(length: 1.5cm, stroke: 2pt + bfh-yellow)
    })
  }

  // The outline and the lists of figures and tables, a little smaller, the chapters in bold.
  show outline: set text(size: 10pt)
  show outline.entry.where(level: 1): set text(weight: "bold")
  show outline.entry.where(level: 1): set block(above: 1.1em)

  // Captions -- of a figure and of a table: «Fig. 1 — …», a little smaller than the text.
  show figure.caption: set text(size: 9pt)

  // The formulas keep Typst's math font.
  show math.equation: set text(font: "New Computer Modern Math")

  // A `*` typed in math prints as the multiplication dot, as `#eq` and `#verify` print it (v0.87): $q * L$ reads q · L. A star in a sub- or superscript stays a star -- F* of the most unfavourable superposition, x* -- and so does one in the text.
  show math.equation: it => { show "∗": sym.dot.op; it }
  show math.attach: it => { show "⋅": sym.ast; it }

  // Display math as "display" (shows better in text)
  show math.frac: it => $display(it)$

  // To have every figure read «Figure 1» rather than Typst's own word for the language above -- «Abbildung 1» in German, «Fig. 1» in French -- say so in config.typ:
  //   set figure(supplement: [Figure])

  doc
}
