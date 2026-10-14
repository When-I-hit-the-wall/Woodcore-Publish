// The report's summary tables: the area loads in kN/m², the line loads in kN/m, and the main results -- the whole by domain (v0.99).
//
// A report of forty pages states every load in the section that calculates it and every resistance in the section that checks it, and there is nowhere a reader can see the four numbers he came for side by side. The engineer asked for three tables: «des tableaux récapitulatifs des charges (kN/m2), des charges linéaires (kN/m), puis finalement, des résultats principaux, le tout par domaine».
//
// Three commands and not one with a `kind:`, which is the engineer's own choice: a summary of loads and a summary of results are two things a report prints in two places, and a call that says which of them it is by an argument reads as one command doing three jobs.
//
// ⚠️ **A summary carries no `level:`**, and that is a decision rather than an omission. The engineer's words for it were «un tableau et un tableau»: a summary is the one place in this report whose whole purpose is to be complete, so there is no level at which it would show less. An argument that changed nothing would be a lie in the signature -- an editor would offer it, `build_reference` would catalogue it and a reader would try it -- so there is none, and the three commands are the only printing commands of this engine without one (docs/decisions.md §13).
//
// ⚠️ **The tables are printed in the report's head and read the whole document** (`var-registry.final()`), so a check printed *after* the table figures in it. That is one convergence pass more, which Typst carries -- the arrangement `show-bibliography` already rests on.
//
// Where the rows come from, and it is three places rather than one:
//
//   * **the export**, for the loads and for the main results: every `results` name of every instance of every domain of `data/calculations.json`, and of every record of `data/connectors.json` and `data/connections.json`. Which vars are a calculation's results is the **data's** to say (section 3.3), so the summary asks the data and decides nothing -- a rule that needs no list here and that follows a domain added to the pipeline without an edit;
//   * **what the report writes by hand**, marked with `summary: true` on a `#var` or an `#eq`. There are no line loads anywhere in the export -- a static model's own loads are a drawing and compute nothing (section 3.3octies) -- and the engineer's answer for them was «pour l'instant rien. Mais le user doit manuellement pouvoir ajouter des lignes eq ou var dans typst»;
//   * **the registry**, for the utilisations: every `verify-*` of SIA 265 4.2 publishes its η into a var-domain named `"<member>-verify-<check>"` (section 3.3undecies), and those numbers are computed in Typst and are in no file at all. They are the half of a summary with the most in it, and the only half that must read the registry rather than `data/`.
//
// ⚠️ **It is the unit that decides which table a marked row goes to**, and nothing else: `kN/m²` is an area load, `kN/m` a line load, and any other unit is refused naming the two. The alternative -- gathering every variable of a given unit, with no mark at all -- was rejected: an intermediate of a calculation is often in kN/m² (a layer's own load, a pressure on the way to a force), and a summary that listed them would be a summary of the working. So the mark says «this is a load», and the unit says which kind.
//
// ⚠️ **And the unit is read where the variable ends up, not where it was written.** The check therefore happens when the table is printed and not at the call, which is deliberate and not a shortcut: `#var-unit` converts a variable on the line after it was declared, and `#eq`'s answer comes out in whatever unit its operands give it, so a check at the call would refuse a variable that is in kN/m by the time it is read. A `summary: true` in a report that prints no summary is therefore never refused -- nothing lists it, so nothing is wrong with the page.

// It imports calc-engine.typ and **nothing else**, which is what keeps the chain calc-engine -> summary -> formula acyclic without a single import inside a command's body: formula.typ imports the three commands and `summary-mark` by name, the way it imports `distance` and the member checks (docs/typst/api-conventions.md §10bis point 3).
#import "calc-engine.typ": fmt-number, get-symbol, get-unit, get-value, load-calculations, load-connections, load-connectors, render-table, table-spacing, test-nok, test-ok, test-relations, t-str, tl-str, value-type, var-current, var-registry

// --- What the report has marked ----------------------------------------------

// The two units a load may be summarised in, and the table each goes to. The engineer's own two: kN/m² and kN/m.
#let summary-units = ("kN/m²", "kN/m")

/// Marks one variable for a summary table -- and prints nothing.
///
/// It is what `#var` and `#eq` call when they are given `summary: true`, and it is the one piece of this file a caller outside it needs. ⚠️ It is a **pure function of the variable registry's own dictionary**, called from inside the `var-registry.update` those two commands already have, and not a state of its own: a state written from inside a context is not read back by the folded chain an update function reads (docs/domain/connections.md §3.3quinquies, the panne of v0.85), and the domain a variable belongs to -- `var-current(d)` -- can only be read inside an update in the first place. So there is nothing here that could be emitted in the wrong place.
///
/// - d (dictionary): the registry, as `var-store` is handed it.
/// - on (bool): what the call's `summary:` said. `false` returns the registry untouched, so the caller needs no `if`.
/// - key (str): the variable's name, which is what is recorded -- never its value: an `#eq` computes its answer inside this very update and a `#var` reading a var-domain does too, so the value is read back at print time, where it is also the value the variable ends up holding.
/// -> dictionary
#let summary-mark(d, on, key) = {
  if on != true { return d }
  let marks = d.at("summary", default: ())
  let here = (domain: var-current(d), key: key)
  // Recorded once and in the order it was first marked, as `bib-cited` records a citation: a variable declared twice is one row, and it keeps the place its first mark gave it -- the value read at the end being the last one either way.
  d.insert("summary", if marks.contains(here) { marks } else { marks + (here,) })
  d
}

// One marked variable as the registry holds it at the end of the document: (key, the record), or none where the mark points at nothing -- which cannot happen from `var` or `eq`, both of which store before they mark, and is passed over rather than panicked on.
#let summary-marked(d) = {
  let out = ()
  for mark in d.at("summary", default: ()) {
    let dom = d.domains.at(mark.domain, default: (:))
    if mark.key in dom { out.push((key: mark.key, record: dom.at(mark.key))) }
  }
  out
}

// --- The rows -----------------------------------------------------------------
//
// A row is (group, name, var, own) -- the group it is printed under, what it is called in the first column, the var itself, and whether it is the report's own rather than the export's. `own` is what decides how its label is set: the export's words are the engine's and go through the glossary, the report's are the engineer's and are passed through untouched (table-cell, v0.99).

#let summary-row(group, name, var, own: false) = (group: group, name: name, var: var, own: own)

// A number, and nothing else: a result whose value is a word has no place in a column of values. It is what leaves SIA 261's category E out of every table here -- its one «result» is the sentence 8.2.2 states in place of a value (section 3.3septies), and the report refuses to print that category at all, so a summary that carried its sentence in a numeric column would say what no other line of it says.
#let summary-numeric(var) = value-type(get-value(var)) in (int, float)

/// Every variable the report marked, in the unit one table asks for -- and the refusal for one in a third unit.
///
/// ⚠️ The refusal is raised **here, where a table is printed**, and not at the call that marked the variable, because at the call there is often nothing to check: an `#eq` marked for a summary states no `unit:` at all -- its answer comes out in whatever unit the algebra gives its operands -- and `#var-unit` may carry a variable out of the unit it was declared in on the line after. So the unit that decides is the one the variable **ends up** holding. A `summary: true` in a report that prints no summary is therefore never refused, and nothing is wrong with the page: nothing listed it. And **either** table refuses every mark, whichever unit it is itself gathering -- what is wrong is the mark, not the table it is missing from.
///
/// - d (dictionary): the registry at the end of the document.
/// - unit (str): the unit this table gathers, one of `summary-units`.
/// -> array
#let summary-report-rows(d, unit) = {
  let out = ()
  for marked in summary-marked(d) {
    let have = get-unit(marked.record)
    if not (have in summary-units) {
      panic("summary: a variable marked with summary: true is a load, and `" + marked.key + "` is in "
        + (if have == "" { "no unit at all" } else { have }) + " -- a summary row is in "
        + summary-units.join(" or ") + ". State the load in one of the two -- a force divided by the width "
        + "it acts on -- or drop summary: true.")
    }
    if have == unit and summary-numeric(marked.record) {
      out.push(summary-row(t-str("summary.report"), marked.key, marked.record, own: true))
    }
  }
  out
}

// Every result the export carries, domain by domain and instance by instance, in the order the export gives them -- which is registry.py's own: the permanent actions, then the variable ones, and the sheets in tab order (section 3.3). A domain with no instance is not there at all, so it names no group.
#let summary-load-rows() = {
  let out = ()
  for (_, domain) in load-calculations().domains {
    let group = domain.at("label", default: "")
    for (id, instance) in domain.instances {
      for name in instance.at("results", default: ()) {
        let var = instance.vars.at(name, default: none)
        if var != none and summary-numeric(var) { out.push(summary-row(group, id, var)) }
      }
    }
  }
  out
}

// Every result of every connector and of every connection -- and, for a connection, the force `show-polar-moment` published under its own name (section 3.3quinquies): F_max is computed in Typst from an N, a V and an M the report states, so it is in no file, and it is the answer a reader of a polar moment came for. A connection the report has not printed keeps its I_p alone, which is what its record says its result is.
#let summary-connector-rows() = {
  let out = ()
  for (id, record) in load-connectors().connectors {
    if not record.at("calculated", default: true) { continue }
    for name in record.at("results", default: ()) {
      let var = record.vars.at(name, default: none)
      if var != none and summary-numeric(var) { out.push(summary-row(t-str("fasteners"), id, var)) }
    }
  }
  out
}

#let summary-connection-rows(d) = {
  let out = ()
  let group = t-str("summary.connections")
  for (id, record) in load-connections().connections {
    if not record.at("calculated", default: true) { continue }
    for name in record.at("results", default: ()) {
      let var = record.vars.at(name, default: none)
      if var != none and summary-numeric(var) { out.push(summary-row(group, id, var)) }
    }
    // what the report worked out for this very connection, where it printed one at all
    let published = d.domains.at(id, default: (:))
    if "F_max" in published { out.push(summary-row(group, id, published.F_max, own: true)) }
  }
  out
}

// --- The checks ---------------------------------------------------------------
//
// A check's values live in a var-domain named `"<member>-verify-<check>"` (timber.typ's `timber-domain`), and that name is the contract section 3.3undecies publishes -- it is what `#val("eta", domain: "S001-verify-compression")` writes. So the Nachweisübersicht **reads the domains that carry it**, rather than each check registering itself as it runs.
//
// That is the bibliography's own choice of a walk over a registration, for its own reason: a ninth check added to SIA 265 4.2 appears here by itself, where a registration is a line somebody has to remember. ⚠️ Its price is that a check given a `name:` of its own is listed only where that name keeps the shape -- `"S001-verify-compression-Feld"` is listed, `"Feld 2"` is not (section 14).

#let summary-verify-mark = "-verify-"

// The member and the check one domain name states, or none where it is not a check's. The split is on the **first** `-verify-`, and what follows it is taken whole, so a check named `"S001-verify-compression-Feld"` says its check is «compression-Feld» rather than losing the half after the second dash.
#let summary-check-of(name) = {
  let parts = name.split(summary-verify-mark)
  if parts.len() < 2 { return none }
  (member: parts.first(), check: parts.slice(1).join(summary-verify-mark))
}

// The word a check is named by, in the report's language: SIA 265's own heading for the clause it covers, which is what the check's own heading already prints (timber.typ). A check whose name the glossary does not carry -- one a `name:` invented -- is printed as it is written, never invented around.
#let summary-check-word(check) = {
  let key = "summary.verify." + check
  let word = t-str(key)
  if word == key { check } else { word }
}

// Every check the report made, in the order it made them: (member, check, η, its unit, whether it holds). A domain is a check's where its name carries `-verify-` **and** it declares an `eta` that is a number -- both, so that a var-domain of the engineer's own that happens to be named after a check, or one that happens to declare an eta, is not swept in on one of the two alone.
#let summary-check-rows(d) = {
  let out = ()
  for (name, dom) in d.domains {
    let which = summary-check-of(name)
    if which == none { continue }
    let eta = dom.at("eta", default: none)
    if eta == none or not summary-numeric(eta) { continue }
    let unit = get-unit(eta)
    // Against 1, or against 100 where the check was asked for its utilisation in percent (`unit: "%"`, timber.typ's `timber-one`). The comparison itself is `verify`'s own -- its table, its tolerance -- so a verdict here and the verdict the check printed cannot come to disagree (docs/architecture/principles.md §2, rule 1).
    let limit = if unit == "%" { 100 } else { 1 }
    let holds = (test-relations.at("<=").holds)(get-value(eta), limit)
    // a check in the design situation fire (issue #46) copies its member's k_fi, which no check at normal temperature has: said beside the check's word, so that a utilisation against R_d,fi is never read as one against R_d
    out.push((member: which.member, check: which.check, eta: eta, holds: holds, fire: "k_fi" in dom))
  }
  out
}

// --- Printing -----------------------------------------------------------------

// ✔ or ✘, as `verify` sets it: the **heavy** glyphs U+2714 and U+2718 and never the light ✓ and ✗, Libertinus Serif -- the font this report is set in -- covering the heavy pair and not the light one, and Typst warning about neither. Never bold either, Libertinus Serif Bold covering neither pair; the colour and the size carry it.
#let summary-mark-glyph(holds) = text(fill: if holds { test-ok } else { test-nok }, size: 1.15em, if holds { "✔" } else { "✘" })

// A label as the table is to set it: the export's words through the glossary, the report's own left exactly as they were typed.
//
// ⚠️ **A hand-written label is content and is never looked up**, which is the rule `table-cell` states for the journal's own free text (v0.99): a template of the glossary matches on the literal segments around its holes, so a variable the engineer labelled «Element 3» would match «Element {n}» and a French report would print «élément 3». What the export carries is the engine's word by construction and goes through `tl-str` like every other table read from the data (section 4bis).
#let summary-label(var, own) = {
  let label = var.at("label", default: none)
  if label == none { return [] }
  if own { [#label] } else { label }
}

// The first column's cell: an id of the export -- a sheet, a category, a connector, a connection -- or, for a row the report wrote itself, the variable's own name, which is what a report addresses it by (`#val("g_k_Dach")`). Either way it is set as **content and not as a string**, so that `table-cell` passes it through instead of looking it up: neither an id nor a variable's name is a word of the engine's, and a sheet called «Wand» would otherwise be translated (v0.99's own rule for the journal's free text).
#let summary-name(name) = [#name]

// One table of loads or of results, grouped: a bold row carrying the group's name, then its own rows under it.
//
// ⚠️ A group is named by **a row of its own set bold**, and not by `render-table`'s `group`, which names a run of *columns* (section 3.3) and is a different notion entirely. A bold row over the rows it covers is how a printed table names a block, and `bold-rows` is the argument `render-table` already takes for exactly one row being louder than the others.
//
// Every group gets its row, the one with a single group included: for the line loads that row is «Im Bericht berechnet», and what it says -- that these numbers are the report's own and are traced nowhere (section 1) -- is the first thing a checker of a summary wants to know.
#let summary-table(rows, columns, cells, title: [], above: auto) = {
  let groups = rows.map(r => r.group).dedup()
  let body = ()
  let bold = ()
  for group in groups {
    bold.push(body.len())
    // the group's name in its first cell and nothing in the others, set bold by `bold-rows` below -- a name read across the columns it covers, where a table has no rule to draw under one
    body.push(([#(if type(group) == str { tl-str(group) } else { group })],) + (columns.len() - 1) * ([],))
    for row in rows.filter(r => r.group == group) { body.push(cells(row)) }
  }
  render-table((title: title, columns: columns, rows: body), bold-rows: bold, above: above)
}

// The four columns of a table of loads: the case, the symbol, the value -- its unit in the header, every row of one table being in one unit -- and what the value is. The engineer's own words for the first, `find`'s for the other three, so a reader who has met `#find` has met these.
#let summary-load-columns(unit) = (
  (label: [#t-str("summary.case")], kind: "text"),
  (label: [#tl-str("Symbol")], kind: "math"),
  (label: [#tl-str("Wert")], kind: "number", unit: unit),
  (label: [#tl-str("Bezeichnung")], kind: "wide"),
)

#let summary-load-cells(row) = (
  summary-name(row.name),
  get-symbol(row.var),
  get-value(row.var),
  summary-label(row.var, row.own),
)

// And the five of a table of results, whose rows are of three kinds and therefore of as many units: a unit column of its own, since a unit is a field of its own and never typed into a value (section 3.3) -- and a column of values in mm² beside one in kN would line up on nothing without it.
#let summary-result-columns() = (
  (label: [#tl-str("Name")], kind: "text"),
  (label: [#tl-str("Symbol")], kind: "math"),
  (label: [#tl-str("Wert")], kind: "number"),
  (label: [#tl-str("Einheit")], kind: "text"),
  (label: [#tl-str("Bezeichnung")], kind: "wide"),
)

#let summary-result-cells(row) = (
  summary-name(row.name),
  get-symbol(row.var),
  get-value(row.var),
  [#get-unit(row.var)],
  summary-label(row.var, row.own),
)

// The blocks `show-result-summary` prints, in this order.
#let summary-blocks = ("values", "checks")

// A heading above the whole summary, where the call asks for one. `show-journal`'s own arrangement: auto and none print none, the section's heading being the engineer's (section 4bis).
#let summary-heading(title) = {
  if title == auto or title == none { return none }
  title
}

/// **Every area load of the report in one table, in kN/m², one line per case and grouped by domain** (v0.99).
///
/// ```typ
/// #show-load-summary()
/// ```
///
/// ```typ
/// #var("g_k", 1.35, "kN/m²", label: "Eigenlast Dachaufbau", summary: true, level: 0)
/// #show-load-summary(title: "Flächenlasten")
/// ```
///
/// Its rows are every `results` name of every instance of every load domain the export carries -- which is what `show-calc` prints at level 1 -- and every variable the report marked with `summary: true` whose unit is kN/m². The domains come in the order the export gives them, the permanent actions before the variable ones; a domain with no case at all names no group.
///
/// The table reads the **whole document** (`var-registry.final()`), so it may be printed in the report's head and still carry a variable marked fifty pages further down.
///
/// ⚠️ It takes no `level:`: a summary is complete or it is not one (docs/decisions.md §13).
/// - title (auto, none, str, content): auto and none print no heading -- the section's own heading is the engineer's -- a string or content prints one above the table.
/// -> content
#let show-load-summary(title: auto) = context {
  let d = var-registry.final()
  let rows = summary-load-rows().filter(r => get-unit(r.var) == summary-units.at(0))
  let own = summary-report-rows(d, summary-units.at(0))
  let head = summary-heading(title)
  let below = 0.7em
  if head != none { block(above: 1em, below: below, sticky: true, text(weight: "bold", head)) }
  let all = rows + own
  if all.len() == 0 {
    block(above: if head == none { table-spacing } else { below }, below: table-spacing, emph(t-str("summary.loads_empty")))
  } else {
    summary-table(all, summary-load-columns(summary-units.at(0)), summary-load-cells,
      above: if head == none { auto } else { below })
  }
}

/// **Every line load of the report in one table, in kN/m** (v0.99).
///
/// ```typ
/// #var-line[ #var("g_k", 2.5, "kN/m²") #var("b_e", 3.6, "m") ]
/// #eq("q_d", `g_k dot b_e`, unit: "kN/m", label: "Dachlast auf den Träger", summary: true)
///
/// #show-line-load-summary()
/// ```
///
/// ```typ
/// #var("q_Dach", 4.2, "kN/m", label: "Dachlast auf den Träger", summary: true, level: 0)
/// #show-line-load-summary(title: "Linienlasten")
/// ```
///
/// ⚠️ **Nothing in the export is a line load**, and that is not an omission of this command: a load reaches `data/` as an action per square metre (section 3.3), and a static model's own line loads are a *drawing* which computes nothing and is not addressed as a calculation (section 3.3octies). So every row here is one the report wrote by hand and marked with `summary: true` -- and the group's name says so, which is what tells a checker that these numbers are the report's own and traced nowhere (section 1).
///
/// - title (auto, none, str, content): as `show-load-summary`.
/// -> content
#let show-line-load-summary(title: auto) = context {
  let d = var-registry.final()
  let rows = summary-load-rows().filter(r => get-unit(r.var) == summary-units.at(1))
  let own = summary-report-rows(d, summary-units.at(1))
  let head = summary-heading(title)
  let below = 0.7em
  if head != none { block(above: 1em, below: below, sticky: true, text(weight: "bold", head)) }
  let all = rows + own
  if all.len() == 0 {
    block(above: if head == none { table-spacing } else { below }, below: table-spacing, emph(t-str("summary.line_loads_empty")))
  } else {
    summary-table(all, summary-load-columns(summary-units.at(1)), summary-load-cells,
      above: if head == none { auto } else { below })
  }
}

/// **The report's main results: every load domain's own results, every connector's resistance, every connection's force, and the utilisation of every member check with its ✔ or ✘** (v0.99).
///
/// ```typ
/// #show-result-summary()
/// ```
///
/// ```typ
/// #member("S001")
/// #verify-compression("S001", N: -40, l-k-y: 3000, l-k-z: 3000, level: 0)
///
/// #show-result-summary(blocks: ("checks",))
/// ```
///
/// Two tables, because its rows are of two shapes: **the values** -- a number with a unit, grouped by load domain, then the fasteners, then the connections -- and **the Nachweisübersicht**, one line per check with its η against 1 and the mark the check itself printed. A utilisation against 1 and a resistance in kN share no column set, and one that held both would hold neither well.
///
/// What a calculation's results *are* is the data's to say (section 3.3), so this asks the record and decides nothing: a load domain's `results`, a connector's `R_d` and `R_d,Verb`, a connection's `I_p` -- and beside it the **F_max** `show-polar-moment` published under that connection's own name, which is computed in Typst and is in no file at all (section 3.3quinquies). A result whose value is a word rather than a number is left out, which is what leaves SIA 261's category E -- whose one result is the sentence 8.2.2 states in place of a value -- out of the table the report refuses to print it in anyway.
///
/// The checks are read from the registry: every `verify-*` stores its η in a var-domain named `"<member>-verify-<check>"` (section 3.3undecies), and the table reads the **whole document**, so a check printed after it is in it.
///
/// ⚠️ It takes no `level:`, as the two load summaries do not (section 13).
/// - blocks (array, auto): which of `"values"` and `"checks"` to print, in order. auto prints both; a block with nothing in it is left out, and where everything asked for is empty one line says so.
/// - title (auto, none, str, content): auto and none print no heading above the two tables -- each of them carries its own title, there being two -- a string or content prints one.
/// -> content
#let show-result-summary(blocks: auto, title: auto) = {
  let blocks = if blocks == auto { summary-blocks } else { blocks }
  assert(type(blocks) == array, message: "show-result-summary: blocks: is an array of " + summary-blocks.map(b => repr(b)).join(", ") + ", got " + repr(blocks))
  for b in blocks {
    assert(b in summary-blocks, message: "show-result-summary: " + repr(b) + " is not a block -- they are " + summary-blocks.map(x => repr(x)).join(", "))
  }
  context {
    let d = var-registry.final()
    let values = if "values" in blocks { summary-load-rows() + summary-connector-rows() + summary-connection-rows(d) } else { () }
    let checks = if "checks" in blocks { summary-check-rows(d) } else { () }
    let head = summary-heading(title)
    let below = 0.7em
    if head != none { block(above: 1em, below: below, sticky: true, text(weight: "bold", head)) }
    if values.len() == 0 and checks.len() == 0 {
      block(above: if head == none { table-spacing } else { below }, below: table-spacing, emph(t-str("summary.results_empty")))
    } else {
      if values.len() > 0 {
        summary-table(values, summary-result-columns(), summary-result-cells,
          title: [#t-str("summary.values")], above: if head == none { auto } else { below })
      }
      if checks.len() > 0 {
        render-table((
          title: [#t-str("summary.checks")],
          columns: (
            (label: [#t-str("member")], kind: "text"),
            (label: [#tl-str("Nachweis")], kind: "wide"),
            (label: [], label_math: "eta", kind: "number"),
            // the mark's column is headed by nothing: a column of ✔ and ✘ says what it is
            (label: [], kind: "text"),
          ),
          rows: checks.map(c => (
            [#c.member],
            [#summary-check-word(c.check)#if c.at("fire", default: false) [ (#t-str("summary.fire"))]],
            fmt-number(get-value(c.eta), get-unit(c.eta)),
            summary-mark-glyph(c.holds),
          )),
        ), above: if values.len() > 0 or head == none { auto } else { below })
      }
    }
  }
}
