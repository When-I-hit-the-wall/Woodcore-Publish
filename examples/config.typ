// The styling the worked examples of the commands tab are set in (docs/typst/command-docs.md §10sexies): the report's own config.typ, copied here in v0.81 so the documentation's pages no longer depend on whichever report sits next to the code. An example is compiled with examples/ as its Typst root and imports this file.

// Basic page/text/heading setup for the report. Keep this file free of *state*: no `context`, nothing that reads report-level or the report language, no custom pagination logic — that is what lets it stay the plain styling file it is (docs/typst/language.md §4bis). Add project-wide styling tweaks here later.

// **The document's own language lives here** (docs/typst/language.md §4bis). `lang` and `region` are what Typst itself works in: the hyphenation patterns, the quotation marks, and the words Typst writes of its own accord — «Abbildung»/«Fig.», «Tabelle»/«Tableau», the outline's title. Set them by hand, to the language this report is written in.
//
// They are deliberately *not* the report language of `#set-report-language` (Statischer Rapport.typ): that command translates what the *engine* prints — the labels of the calculations, the tables' headings and notes, the figures' legends — while what the report says in its own words, its headings and its title and its prose, is the engineer's and is never translated. Two settings, because they answer two questions; a report in French wants both.
#let doc-lang = "de"
#let doc-region = "CH"

#let conf(doc) = {
  set page(
    paper: "a4",
    margin: (top: 3cm, bottom: 2.5cm, left: 2.5cm, right: 2.5cm),
    numbering: "1",
    footer: context align(center, counter(page).display("1")),
  )

  set text(size: 11pt, lang: doc-lang, region: doc-region)
  set par(justify: true)
  set heading(numbering: "1.1")

  // A `*` typed in math prints as the multiplication dot, as `#eq` and `#verify` print it (v0.87): $q * L$ reads q · L. A star in a sub- or superscript stays a star -- F* of the most unfavourable superposition, x* -- and so does one in the text.
  show math.equation: it => { show "∗": sym.dot.op; it }
  show math.attach: it => { show "⋅": sym.ast; it }

  // Display math as "display" (shows better in text)
  show math.frac: it => $display(it)$

  // To have every figure read «Figure 1» rather than Typst's own word for the language above — «Abbildung 1» in German, «Fig. 1» in French — say so here:
  //   set figure(supplement: [Figure])

  doc
}
