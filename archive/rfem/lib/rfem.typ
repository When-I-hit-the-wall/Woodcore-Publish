// What a report prints out of an RFEM model: one extreme with the combination that produced it, a bar's whole table of them, and a combination's own formula (v0.99, docs/domain/rfem.md §3.3quindecies).
//
// The engineer's own list: «(1) affichage de l'effort maximal (e.g. M), et affichage de la combinaison de charge qui a calculé cet effort maximal (e.g. CO33), (2) affichage d'un tableau qui contient tous les efforts ou déformations maximales ainsi que les combinaisons de charge qui les ont calculés», and «les combinaisons de charge: affichage de la formule, au choix, sous forme 1.35 * CC1 + 1.5 * CC2 ou en remplaçant CC1 et CC2 par leur nom».
//
// ⚠️ **The design situation is always stated, and a call that leaves it out is refused naming the ones there are.** That is the engineer's own rule -- «il faut toujours préciser quelle situation ou combinaison on regarde» -- and it is enforced rather than defaulted: an ELU moment and an ELS moment differ by half, and a default would put one of them on the page under the other's name.
//
// ⚠️ **Nothing here computes.** Every number is an extreme RFEM's own result-combination tables carry, with the combination RFEM named beside it (`calc/rfem_import/envelopes.py`); these commands arrange them. Which is also why they cite no norm: a solver's answer is not a clause, and the prose must cite what the model was calculated to.
//
// ⚠️ **`show-rfem-forces` takes a bar *or* a support node**, because the export gives them one shape: a bar is `T001_1`, a support is `N1`, and both are the `bar` field of a var. One command and one table, with no argument saying which kind it is.
//
// ⚠️ **A name the export does not carry may be a quantity that is identically zero**, which a plane model has six of, so the refusal names those apart from the ones the bar simply has not got (`record.zero`) -- «this structure carries no M_z» and «this export was read without M_z» must not read alike.
//
// ⚠️ Kept out of `calc-engine.typ` and imported into `formula.typ` **by name**, as `distance.typ`, `timber.typ`, `bibliography.typ` and `summary.typ` are (docs/typst/api-conventions.md §10bis point 3): the wildcard would put this file's helpers in every section's scope. It imports `calc-engine.typ` and nothing else.

#import "calc-engine.typ": fmt-decimals, fmt-number, load-rfem, number-digits, render-table, resolve-level, t-str, tl-str

// The two kinds of extreme RFEM writes, and the order a table sets them in.
#let rfem-kinds = ("max", "min")

// The quantities of each table, in the order a report reads them. A bar carries the first two runs and a
// support node the third; which of them a name belongs to is never asked, since the record only holds what
// that object actually has.
#let rfem-forces = ("N", "Vy", "Vz", "MT", "My", "Mz")
#let rfem-deformations = ("|u|", "ux", "uy", "uz", "φx", "φy", "φz")
#let rfem-reactions = ("Px", "Py", "Pz", "Mx", "My", "Mz")


// Every var of one structure about one object in one situation: `("My": ("max": var, "min": var))`.
#let rfem-slots(record, bar, situation) = {
  let out = (:)
  for (_name, value) in record.vars {
    if value.bar != bar or value.situation != situation { continue }
    let held = out.at(value.quantity, default: (:))
    held.insert(value.kind, value)
    out.insert(value.quantity, held)
  }
  out
}


// The structure's record, or a refusal naming what there is.
#let rfem-record(fn-name, structure) = {
  let known = load-rfem().structures
  assert(structure in known,
    message: fn-name + ": no RFEM structure '" + structure + "' -- " + (if known.len() == 0 { "this project names no RFEM export yet (add one in Woodcore's RFEM tab, then export again)" } else { "valid structures: " + known.keys().join(", ") }))
  let record = known.at(structure)
  if not record.calculated {
    panic(fn-name + ": the RFEM structure '" + structure + "' carries no result -- " + record.reason)
  }
  record
}


// The design situation a call states, refused where it states none -- the engineer's own rule.
#let rfem-situation(fn-name, record, situation) = {
  let there = record.situations
  let first = if there.len() > 0 { there.keys().first() } else { "SP1" }
  assert(situation != auto,
    message: fn-name + ": say which design situation to read -- situation: \"" + first + "\"; this structure carries " + (if there.len() == 0 { "none" } else { there.keys().join(", ") }))
  assert(type(situation) == str and situation in there,
    message: fn-name + ": " + repr(situation) + " is not a design situation of this structure -- it carries " + there.keys().join(", "))
  situation
}


// What a bar has, for a refusal that helps: what it carries, and what is identically zero on it.
#let rfem-has(record, bar, slots) = {
  let zero = record.at("zero", default: (:))
  let carried = if slots.len() == 0 { "it carries nothing there" } else { "it carries " + slots.keys().join(", ") }
  let flat = if bar in zero { "; identically zero on it: " + zero.at(bar).join(", ") } else { "" }
  carried + flat
}


/// One extreme RFEM found on a bar, with the load combination that produced it.
///
/// The engineer's own «(1) affichage de l'effort maximal, et affichage de la combinaison de charge qui a calculé cet effort maximal». `#val` prints the value alone; this prints the value **and** what produced it, which is the half `#val` cannot know about.
///
/// ```typ
/// Das grösste Feldmoment beträgt #rfem-max("VU", "T001_1", "My", situation: "SP1").
/// ```
///
/// ```typ
/// #rfem-max("VU", "T001_1", "My", situation: "SP1", kind: "min", level: 3)
/// ```
///
/// - structure (str): the RFEM structure, as `rfem-ids()` gives it.
/// - bar (str): the bar, `T001_1`, or a support node, `N1` -- as `rfem-bars()` gives it.
/// - quantity (str): the quantity as RFEM writes it -- `N`, `Vy`, `Vz`, `MT`, `My`, `Mz`; `|u|`, `ux`, `uy`, `uz`, `φx`, `φy`, `φz`; `Px`, `Py`, `Pz`, `Mx`, `My`, `Mz`.
/// - situation (str): the design situation, `"SP1"`. Always stated: a call that leaves it out is refused naming the ones there are.
/// - kind (str): `"max"` or `"min"`.
/// - loading (bool): print the combination that produced it, `(CO3)`. On by default -- it is what this command is for.
/// - level (int, auto): 0 prints nothing, 1 the value, 2 also what the value is, 3 also the situation and where along the bar it stands.
/// -> content
#let rfem-max(structure, bar, quantity, situation: auto, kind: "max", loading: true, level: auto) = context {
  let shown = resolve-level(level)
  assert(kind in rfem-kinds, message: "rfem-max: kind must be \"max\" or \"min\", got " + repr(kind))
  let record = rfem-record("rfem-max", structure)
  let key = rfem-situation("rfem-max", record, situation)
  let slots = rfem-slots(record, bar, key)
  assert(quantity in slots,
    message: "rfem-max: bar '" + bar + "' carries no '" + quantity + "' in " + key + " -- " + rfem-has(record, bar, slots))
  let slot = slots.at(quantity)
  assert(kind in slot, message: "rfem-max: '" + quantity + "' on bar '" + bar + "' has no " + kind + " in " + key)
  let v = slot.at(kind)
  if shown <= 0 { return }
  let out = fmt-number(v.value, v.unit)
  if loading { out = out + " (" + v.loading + ")" }
  if shown >= 2 { out = out + " — " + tl-str(v.label) }
  if shown >= 3 {
    let digits = number-digits.get()
    let where = if v.at("at", default: none) != none { ", x = " + fmt-decimals(v.at, digits) + " m" } else { "" }
    out = out + " [" + record.situations.at(key, default: key) + where + "]"
  }
  out
}


/// Every extreme RFEM found on one bar, in one table, each with the combination that produced it.
///
/// The engineer's own «(2) affichage d'un tableau qui contient tous les efforts ou déformations maximales ainsi que les combinaisons de charge qui les ont calculés». A support node is given in place of a bar -- `N1` -- and the table is then its reactions.
///
/// ```typ
/// #show-rfem-forces("VU", "T001_1", situation: "SP1")
/// ```
///
/// ```typ
/// #show-rfem-forces("VU", "T001_1", situation: "SP1", title: "Schnittgrössen des Trägers", level: 3)
/// ```
///
/// - structure (str): the RFEM structure, as `rfem-ids()` gives it.
/// - bar (str): the bar or the support node whose extremes to print.
/// - situation (str): the design situation, `"SP1"`. Always stated.
/// - quantities (auto, array): which quantities to print, in this order; `auto` prints everything that bar carries.
/// - level (int, auto): 0 prints nothing, 1 the values with the combination that produced each -- which is what this table is for -- and 2 also where along the bar each stands.
/// - title (auto, none, str): `auto` heads the table with the bar and the situation, `none` prints no title, a string replaces it.
/// -> content
#let show-rfem-forces(structure, bar, situation: auto, quantities: auto, level: auto, title: auto) = context {
  let shown = resolve-level(level)
  let record = rfem-record("show-rfem-forces", structure)
  let key = rfem-situation("show-rfem-forces", record, situation)
  let slots = rfem-slots(record, bar, key)
  assert(slots.len() > 0,
    message: "show-rfem-forces: bar '" + bar + "' carries nothing in " + key + " -- " + rfem-has(record, bar, slots))
  if shown <= 0 { return }

  // ⚠️ `My` and `Mz` are both a member's moment and a support's, so the three runs share two names and a
  // filtered concatenation listed them twice. The first occurrence wins, which keeps the reading order.
  let order = if quantities == auto {
    let seen = ()
    for q in rfem-forces + rfem-deformations + rfem-reactions {
      if q in slots and q not in seen { seen.push(q) }
    }
    seen
  } else { quantities }
  for wanted in order {
    assert(wanted in slots,
      message: "show-rfem-forces: bar '" + bar + "' carries no '" + wanted + "' in " + key + " -- " + rfem-has(record, bar, slots))
  }

  // ⚠️ **The combination is a column at level 1**, where every other command of this engine keeps its
  // provenance for level 3. This table exists to carry it -- the engineer asked for «un tableau qui contient
  // tous les efforts maximaux ainsi que les combinaisons de charge qui les ont calculés» -- so a level that
  // printed the numbers without them would print a table that is not the one he asked for. What the levels
  // do govern is where along the bar each extreme stands, which is a checker's question.
  let columns = ((label: t-str("rfem.quantity"), kind: "math"),)
  for kind in rfem-kinds {
    columns.push((label: t-str("rfem.value"), kind: "number", group: t-str("rfem." + kind)))
    columns.push((label: t-str("rfem.loading"), kind: "text", group: t-str("rfem." + kind)))
    if shown >= 2 { columns.push((label: "x", kind: "number", unit: "m", group: t-str("rfem." + kind))) }
  }
  columns.push((label: t-str("rfem.unit"), kind: "text"))

  let digits = number-digits.get()
  let rows = ()
  for wanted in order {
    let slot = slots.at(wanted)
    let row = (slot.values().first().symbol,)
    for kind in rfem-kinds {
      let v = slot.at(kind, default: none)
      row.push(if v == none { "" } else { fmt-decimals(v.value, digits) })
      row.push(if v == none { "" } else { v.loading })
      if shown >= 2 {
        row.push(if v == none or v.at("at", default: none) == none { "" } else { fmt-decimals(v.at, digits) })
      }
    }
    row.push(slot.values().first().unit)
    rows.push(row)
  }

  let head = if title == auto {
    t-str("rfem.table-title") + " " + bar + ", " + record.situations.at(key, default: key)
  } else { title }
  render-table((title: if head == none { "" } else { head }, columns: columns, rows: rows))
}


// One term of a combination, as the page sets it: `1.35 · CC1`, or with the case's own name in its place.
#let rfem-term(factor, case, names, cases, digits) = {
  let shown = if names and case in cases and cases.at(case).name != "" { cases.at(case).name } else { case }
  // ⚠️ A case's name may itself be a sum -- CC1 is «EG + AL» -- so `1.35 · EG + AL + 1.50 · Schnee` would
  // read as three terms. The engineer's own rule: parenthesise as soon as the name is not a simple word.
  let simple = shown.clusters().all(ch => ch not in ("+", "-", "−", "·", "*", "/", "(", ")", ",", ";"))
  let body = if simple { shown } else { "(" + shown + ")" }
  fmt-decimals(factor, digits) + " · " + body
}


/// The formula of one load combination: `1.35 · CC1 + 1.50 · CC2`, or with the load cases' own names in place of their ids.
///
/// The engineer's own «affichage de la formule, au choix, sous forme: 1.35 * CC1 + 1.5 * CC2 ou en remplaçant CC1 et CC2 par leur nom 1.35 * EL+AL + 1.5 * SL».
///
/// ```typ
/// Die massgebende Kombination ist #show-rfem-combination("CO2").
/// ```
///
/// ```typ
/// #show-rfem-combination("CO2", names: true, level: 3)
/// ```
///
/// - id (str): the combination, as RFEM names it -- `"CO3"`.
/// - names (bool): write each load case's own name in place of its id. A name that is not a simple word is parenthesised, since CC1 is «EG + AL» and `1.35 · EG + AL` would read as two terms.
/// - level (int, auto): 0 prints nothing, 1 the formula, 2 also the combination's own id before it, 3 also the design situation it belongs to.
/// -> content
#let show-rfem-combination(id, names: false, level: auto) = context {
  let shown = resolve-level(level)
  let doc = load-rfem()
  let known = doc.at("combinations", default: (:))
  assert(id in known,
    message: "show-rfem-combination: no load combination '" + id + "' -- " + (if known.len() == 0 { "this project names no RFEM export yet" } else { "this export carries " + known.keys().slice(0, calc.min(8, known.len())).join(", ") + (if known.len() > 8 { ", …" } else { "" }) }))
  if shown <= 0 { return }
  let combination = known.at(id)
  let cases = doc.at("cases", default: (:))
  let digits = number-digits.get()
  let terms = combination.terms.map(term => rfem-term(term.at(0), term.at(1), names, cases, digits))
  let out = if terms.len() == 0 { combination.at("name", default: id) } else { terms.join(" + ") }
  if shown >= 2 { out = id + " = " + out }
  if shown >= 3 and combination.at("situation", default: "") != "" {
    out = out + " [" + combination.situation + "]"
  }
  out
}
