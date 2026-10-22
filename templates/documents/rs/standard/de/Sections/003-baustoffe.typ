#import "/commands.typ": *

// woodcore:object heading title
= Baustoffe
// woodcore:/object title

// woodcore:object text p1
Baustoffe und Querschnitte des Tragwerks.
// woodcore:/object p1

// Every position on its line (#position), and every connector saved in Woodcore, its file written out (domain-file) (docs/domain/member-checks.md §3.3undecies, docs/domain/positions.md §7, docs/domain/connectors.md §7bis).
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
