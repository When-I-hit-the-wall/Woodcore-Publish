#import "/000-Typst-Config/commands.typ": *

= Baustoffe

Baustoffe und Querschnitte des Tragwerks.

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
