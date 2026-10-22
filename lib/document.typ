// The parametric objects of a project's documents -- the convention d'utilisation, the base de projet and the statical report (the three document modes, phase 3): the tables, the live loads and the non-structural self-weight, a labelled field, a list to tick, a single choice, a picture, an extract of a position plan, the signatures and the norms a section names.
//
// Each command is one object. Woodcore writes it between two tags of the section's own .typ file -- `// woodcore:object <command> <id>` and `// woodcore:/object <id>`, a line each -- as one call in the canonical form its editor parses and writes back: one named argument per line, a trailing comma everywhere, the arguments in the order each signature below states them. **The .typ is the source of truth**: an object written by hand is the same call, and prints the same. Nothing here reads the tags; they are the editor's.
//
// ⚠️ **The engineer's own words are content and are never looked up in the glossary**, which is the rule the journal's free text follows (v0.99): a title, a cell, a caption, a label, a note is printed exactly as it is written -- a string included, which is wrapped as content before it reaches `render-table` -- so a use typed «Element 3» cannot match a template of the glossary and come out translated. What the engine says of its own accord -- a column's default heading, the line saying what orange means, a placeholder -- is `calc/i18n/strings.json`'s, in the report's language.
//
// ⚠️ **A table is set as every table of this engine is**, by `render-table` (docs/domain/calculation-domains.md §3.3): three rules and nothing else, a column aligned by what it holds. Only a table without its heading row -- a list of terms and what they are -- is laid out here, with the same rules, the same insets and the same alignments, render-table always setting a heading row.
//
// ⚠️ formula.typ imports the eleven commands from here by name, which is how commands.typ gives every section these and none of the helpers. Nothing is imported back from formula.typ: a value quoted in a cell is `doc-value`'s, which reads the registry and the export through calc-engine.typ's own lookups -- so the chain calc-engine -> bibliography -> document -> formula is acyclic, with no import inside a body (the live-load table imported `val` inside its own until `doc-value` stood in for it).
#import "calc-engine.typ": print-level, report-lang
#import "bibliography.typ": bib-index, bib-line, bib-note, bib-read-file

// --- Refusals and shapes ------------------------------------------------------------------
//
// An argument that is not what the command takes is refused naming the command and what to write, never passed over: an object Woodcore cannot read back is one its editor would silently rewrite. Every refusal is a `panic` inside an `if` and never `assert(cond, message: ...)`, whose message Typst builds before it tests the condition (v0.63.1).

#let doc-refuse(fn, message) = panic(fn + ": " + message)

// --- Columns, hidden columns, rows ----------------------------------------------------------

// --- One value, in a cell -----------------------------------------------------------------------

// --- The live loads, read off SIA 261 Tabelle 8 (docs/domain/loads.md §3.3septies) ----------------

// --- The non-structural self-weight (Auflast) --------------------------------------------------

// --- A labelled value, a list to tick, a single choice --------------------------------------

// --- A picture, an extract of a position plan --------------------------------------------------

// A frame standing where a picture will be, saying what will stand in it.
#let doc-frame(width, words) = block(width: width, height: 4cm, stroke: (paint: luma(150), thickness: 0.6pt, dash: "dashed"), inset: 8pt,
  align(center + horizon, text(fill: luma(110), words)))

// --- The signatures --------------------------------------------------------------------------

// --- The norms a section names ------------------------------------------------------------------

/// **The norms and documents a section names, listed in full** -- designation, title, publisher and edition, as the bibliography sets them (docs/typst/citations.md §10): the selection the engineer makes in the section of the norms and the documents a convention d'utilisation and a base de projet rest on.
///
/// ```typ
/// #show-norm-list(keys: ("SIA 260", "SIA 261", "SIA 265"))
/// ```
///
/// ```typ
/// #show-norm-list(keys: ("VKF 14-15", "SIA 181:2020", [Lärmschutz-Verordnung (LSV)]))
/// ```
///
/// A key is a document of `calc/norms/norms.json`, or of the project's own `references.bib` where `project:` names it, by its key or one of its aliases (`"SIA 260:2013"`), and it is registered for the bibliography as a citation is; one neither names is printed as it is written and never invented. Content is a line in the engineer's own words, printed as it is and registered nowhere. They are printed in the order given, once each.
///
/// - keys (array): the documents, in order: strings naming an entry, or content.
/// - project (none, str): the project's own `references.bib`, as a path from the project's folder -- `"references.bib"` -- or none.
/// - level (auto, int): 1 each document by its designation alone, «SIA 260:2013»; 2 in full, its title, publisher and edition as the bibliography sets them (what a document prints by default); 3 the same as 2, a list of norms being its own citation. auto follows the document.
/// -> content
#let show-norm-list(keys: (), project: none, level: auto) = {
  let fn = "show-norm-list"
  if type(keys) != array {
    doc-refuse(fn, "keys: is an array of the documents to list, (\"SIA 260\", \"SIA 261\") -- " + (if type(keys) == str { "write (" + repr(keys) + ",) for one" } else { "got " + repr(keys) }))
  }
  for k in keys {
    if not (type(k) in (str, content)) or (type(k) == str and k.trim() == "") {
      doc-refuse(fn, "keys: holds " + repr(k) + " -- a document is named by a non-empty string, \"SIA 260\", and a line of your own is [content]")
    }
  }
  if project != none and type(project) != str {
    doc-refuse(fn, "project: names the project's references.bib as a path from the project's folder, \"references.bib\" -- got " + repr(project))
  }
  // The entries the keys name, found once and outside the context: the catalogue and the project's file are read, not asked of a state. A key and an alias of one document -- «SIA 260» and «SIA 260:2013» -- are one document, listed once and registered under its own key, so that the bibliography, which dedups what it was handed, lists it once too.
  let index = bib-index(if project == none { () } else { bib-read-file(project) })
  let items = ()
  let seen = ()
  for k in keys {
    if type(k) == content {
      items.push(k)
    } else {
      let cited = k.trim()
      let entry = index.at(cited, default: none)
      let name = if entry == none { cited } else { entry.key }
      if not (name in seen) {
        seen.push(name)
        items.push((cited: name, entry: entry))
      }
    }
  }
  // registered before the context, never inside it (docs/typst/api-conventions.md §10bis)
  for name in seen { bib-note(name) }
  context {
    let lang = report-lang()
    for item in items {
      // the level (spec 2026-10-20-indices-et-niveaux, UI-003): the designation alone at 1, the whole entry from 2
      block(above: 0.5em, below: 0.5em, if type(item) == content { item } else if print-level("show-norm-list", level) < 2 { [#item.cited] } else { bib-line(item, lang) })
    }
  }
}
