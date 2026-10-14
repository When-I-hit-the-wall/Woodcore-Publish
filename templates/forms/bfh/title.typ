// The title page of the project's documents, in the Berner Fachhochschule's academic style -- the convention d'utilisation, the base de projet and the statical report. Each document's entry file sets it with one line, `#title-page(document: "cu")` ("bp" for the base de projet, "rs" for the statical report), so the three share this one file, as they share config.typ. It belongs to the form the project is written in (the `Template/` folder, which Woodcore switches), and is the form's title page, laid out as it wants: it is plain Typst, yours to edit here, in VS Code. Woodcore writes it when the project is made and when its form is switched -- the old one is then kept in the archives -- and never otherwise.
//
// What the page prints comes from two places. The project's details -- its name, number, client, address, author and checker -- are written once, in the project's .woodcore file (Woodcore: Fichier → Propriétés du projet), and read here through `project-info()`. The words the page prints of its own -- the department, the programme, the place, the document's name, the label of each row, the date -- are in the word table further down, in German, French and English: the page takes the language the document is written in, which is config.typ's `doc-lang`.
//
// Two things to edit, and nothing else needs touching: the rows just below, and the word table. What follows the line «How the page is laid out» is the page itself -- the BFH's logo, colours and fonts, which Template/template.typ defines -- and you may change it too: it is plain Typst.

#import "/commands.typ": project-info
#import "/Template/template.typ": sans, bfh-grey, bfh-yellow, muted

// One row of the page: what `rows` below is a list of. See the section «EDIT HERE» for what each argument does.
#let row(label, value: auto, layout: "inline", bold: false, split: auto, documents: auto) = (
  label: label, value: value, layout: layout, bold: bold, split: split, documents: documents,
)

// ==================================================================================================
// EDIT HERE -- the rows of the title page, top to bottom
// ==================================================================================================
//
// One `row(...)` per line of the page, in the order they are printed. A row with nothing to print is left out, so an empty field of the .woodcore leaves no empty line.
//
// row(label, value: auto, layout: "inline", bold: false, split: auto, documents: auto)
//
// - label: what stands before the value. A key of the word table below -- "number", "client", "address", "company", "author", "checker" -- printed in the document's language; your own words, as a string "Architektur" or as content [Architektur]; your own words in three languages, (de: "Architektur", fr: "Architecture", en: "Architecture"); or none, for a value standing alone.
// - value: auto takes the .woodcore field the label names -- row("author") prints the project's author. A string names a field of the .woodcore: "name", "number", "client", "address", "company", "author" or "checker". Content is printed as you write it: [Muster Architekten AG \ Bahnhofstrasse 1 \ 2502 Biel]. An array of strings or content is a list of people, laid out as a field's people are.
// - layout: "inline" joins the people with commas on one line; "lines" sets one person per line.
// - bold: true sets the value in bold.
// - split: how a field is cut into people. "people" cuts it at every new line, «;» and «,» -- the default for author, checker and client, so «Hans Peter Beispiel, Lea Exempel» is two people. "lines" cuts it at new lines alone -- the default for every other field, a comma belonging to an address. "none" leaves it whole. A «- » or «• » at the start of a person is dropped, so a list typed with dashes in the .woodcore reads as names.
// - documents: auto prints the row in the three documents; ("rs",) only in the statical report; ("cu", "bp") only in the convention d'utilisation and the base de projet.
#let rows = (
  row("author"),
  row("checker"),
  row("client", layout: "lines"),
  row("address", layout: "lines"),
  // An architect of your own, with an address, one line each -- uncomment and edit:
  // row((de: "Architektur", fr: "Architecture", en: "Architecture"), value: [Muster Architekten AG \ Bahnhofstrasse 1 \ 2502 Biel], layout: "lines"),
  // People of your own, one per line, in bold:
  // row((de: "Expertise", fr: "Expertise", en: "Expert"), value: ("Anna Muster", "Beat Beispiel"), layout: "lines", bold: true),
  // A line of your own with no label:
  // row(none, value: [Projektarbeit 2 -- HS 2026]),
  // The authors one per line, in bold:
  // row("author", layout: "lines", bold: true),
)

// The date at the foot of the page, after the place: auto is the day the document is compiled, written out in the document's language («3. Oktober 2026»); a day of your own is datetime(year: 2026, month: 10, day: 3); content is printed as you write it, [Oktober 2026]; none prints neither the place nor the date.
#let date = auto

// ==================================================================================================
// The word table -- every word the page prints of its own, in German, French and English
// ==================================================================================================
//
// `department`, `programme` and `place` are the school's, under its logo and at the foot of the page; `documents` is what each document is called (Woodcore's own names, calc/documents.py); `labels` the label of each row a key names; `long-date` how a day is written out and `dateline` how the place and the day are set together. A document written in another language than these three is printed in German.
#let words = (
  de: (
    department: "Architektur, Holz und Bau",
    programme: "BSc Holztechnik",
    place: "Biel",
    documents: (cu: "Nutzungsvereinbarung", bp: "Projektbasis", rs: "Statischer Bericht"),
    labels: (
      name: "Projekt",
      number: "Projekt-Nr.",
      client: "Auftraggeber",
      address: "Projektort",
      company: "Büro",
      author: "Verfasst von",
      checker: "Betreuung",
    ),
    long-date: d => {
      let months = ("Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember")
      str(d.day()) + ". " + months.at(d.month() - 1) + " " + str(d.year())
    },
    dateline: (place, day) => [#place, #day],
  ),
  fr: (
    department: "Architecture, bois et génie civil",
    programme: "BSc Technique du bois",
    place: "Bienne",
    documents: (cu: "Convention d'utilisation", bp: "Base de projet", rs: "Rapport de statique"),
    labels: (
      name: "Projet",
      number: "N° de projet",
      client: "Mandant",
      address: "Lieu du projet",
      company: "Bureau",
      author: "Rédigé par",
      checker: "Encadrement",
    ),
    long-date: d => {
      let months = ("janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre")
      (if d.day() == 1 { "1er" } else { str(d.day()) }) + " " + months.at(d.month() - 1) + " " + str(d.year())
    },
    dateline: (place, day) => [#place, le #day],
  ),
  en: (
    department: "Architecture, Wood and Civil Engineering",
    programme: "BSc Wood Technology",
    place: "Biel/Bienne",
    documents: (cu: "Service criteria agreement", bp: "Basis of design", rs: "Statical report"),
    labels: (
      name: "Project",
      number: "Project no.",
      client: "Client",
      address: "Project location",
      company: "Office",
      author: "Written by",
      checker: "Supervision",
    ),
    long-date: d => {
      let months = ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December")
      str(d.day()) + " " + months.at(d.month() - 1) + " " + str(d.year())
    },
    dateline: (place, day) => [#place, #day],
  ),
)

// ==================================================================================================
// How the page is laid out -- plain Typst, yours to change as well
// ==================================================================================================

// The fields of the .woodcore a row may take, and how each is cut into people where the row does not say (`split: auto`).
#let title-fields = ("name", "number", "client", "address", "company", "author", "checker")
#let title-split = (author: "people", checker: "people", client: "people")

// A field's text cut into its people: at new lines, «;» and «,» for "people", at new lines alone for "lines", not at all for "none"; each trimmed, a leading «- » or «• » dropped, the empty ones left out.
#let title-pieces(text, mode) = {
  assert(mode in ("people", "lines", "none"), message: "title.typ: split is \"people\", \"lines\" or \"none\" -- not " + repr(mode))
  let parts = if mode == "people" { text.split(regex("\r?\n|;|,")) } else if mode == "lines" { text.split(regex("\r?\n")) } else { (text,) }
  parts.map(p => p.trim().replace(regex("^[-•]\\s+"), "").trim()).filter(p => p != "")
}

// What one row prints, as a list of people (strings or content) -- empty where it has nothing to print.
#let title-items(r, info) = {
  let value = r.value
  let field = if value == auto {
    assert(type(r.label) == str and r.label in title-fields,
      message: "title.typ: the row " + repr(r.label) + " names no field of the .woodcore -- give it a value: (a field: " + title-fields.map(repr).join(", ") + "), or content [ … ]")
    r.label
  } else if type(value) == str {
    assert(value in title-fields,
      message: "title.typ: " + repr(value) + " is no field of the .woodcore -- the fields are " + title-fields.map(repr).join(", ") + "; write your own words as content: [" + value + "]")
    value
  } else { none }
  if field != none {
    let mode = if r.split == auto { title-split.at(field, default: "lines") } else { r.split }
    title-pieces(str(info.at(field, default: "")), mode)
  } else if type(value) == array {
    value.filter(x => x != none and x != "" and x != [])
  } else if value == none or value == "" or value == [] {
    ()
  } else {
    (value,)
  }
}

// A row's label in language `lang`: a key of the word table, words of your own, a dictionary of them by language, or none.
#let title-label(label, w, lang) = {
  if label == none { none }
  else if type(label) == str { w.labels.at(label, default: label) }
  else if type(label) == dictionary { label.at(lang, default: label.at("de", default: label.values().first())) }
  else { label }
}

// The rows of document `document` as grid cells: a label and its value, or a value standing alone across both columns.
#let title-cells(document, info, w, lang) = {
  let cells = ()
  for r in rows {
    assert(type(r) == dictionary and "label" in r, message: "title.typ: every entry of `rows` is a row(...) -- found " + repr(r))
    assert(r.layout in ("inline", "lines"), message: "title.typ: layout is \"inline\" or \"lines\" -- not " + repr(r.layout))
    if r.documents != auto and document not in r.documents { continue }
    let items = title-items(r, info)
    if items.len() == 0 { continue }
    let shown = items.map(x => if r.bold { strong(x) } else { [#x] })
    let body = if r.layout == "lines" { shown.join(linebreak()) } else { shown.join([, ]) }
    let label = title-label(r.label, w, lang)
    if label == none {
      cells.push(grid.cell(colspan: 2, body))
    } else {
      cells.push(text(fill: muted, label))
      cells.push(body)
    }
  }
  cells
}

/// The title page of document `document` -- "cu" the convention d'utilisation, "bp" the base de projet, "rs" the statical report -- in the language the document is written in: a page of its own, with no header and no footer, so that what follows starts on the next page.
/// - document (str): "cu", "bp" or "rs".
/// -> content
#let title-page(document: "rs") = {
  assert(document in ("cu", "bp", "rs"), message: "title-page: document is \"cu\", \"bp\" or \"rs\" -- not " + repr(document))
  page(header: none, footer: none, margin: (top: 2cm, bottom: 2.5cm, left: 2.5cm, right: 2.5cm), context {
    let info = project-info()
    let lang = text.lang
    let w = words.at(lang, default: words.de)
    let day = if date == auto { (w.long-date)(datetime.today()) } else if type(date) == datetime { (w.long-date)(date) } else { date }
    set text(font: sans)

    // The BFH's logo, top left, the department and the programme below it.
    image("/Template/logo-bfh.png", width: 7.5cm)
    v(0.6cm)
    text(size: 10pt, fill: bfh-grey)[#w.department \ #w.programme]

    v(1fr)

    // The title: the document, the project, its number.
    line(length: 2.5cm, stroke: 3pt + bfh-yellow)
    v(0.5cm)
    text(size: 11pt, fill: muted, tracking: 0.12em, upper(w.documents.at(document)))
    v(0.2cm)
    block(text(size: 28pt, weight: "bold", fill: bfh-grey, info.name))
    if info.number != "" {
      v(0.1cm)
      block(text(size: 12pt, fill: muted, info.number))
    }

    v(1.5cm)

    // The rows: who wrote it, who supervised it, for whom -- each label in grey, its value beside it.
    let cells = title-cells(document, info, w, lang)
    set text(size: 10pt)
    grid(columns: (3.8cm, 1fr), row-gutter: 0.7em, ..cells)

    v(1fr)

    if day != none { text(size: 10pt, (w.dateline)(w.place, day)) }
  })
}
