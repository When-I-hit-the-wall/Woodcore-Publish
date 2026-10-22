#import "../commands.typ": *

= Baustoffe

Baustoffe und Querschnitte des Tragwerks.

// Every row of Positionen.xlsx's Positions Element sheet, each on the line #member prints at level 1 -- the timber ones written down for the checks of SIA 265 4.2 on the way --, and every connector saved in Woodcore (docs/domain/member-checks.md §3.3undecies, docs/domain/positions.md §7, docs/domain/connectors.md §7bis).
#for id in ids("position") {
  position(id, category-show: ("type", "material", "strength-class", "dimension", "units", "descr"))
  parbreak()
}

#if ids("connector").len() > 0 [
  == Verbindungsmittel

  #for id in ids("connector") {
    include domain-file("connector", id)
  }
]
