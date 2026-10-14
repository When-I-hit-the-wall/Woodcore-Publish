#import "/commands.typ": *

// woodcore:object heading title
= Materials
// woodcore:/object title

// woodcore:object text p1
Materials and cross-sections of the structure.
// woodcore:/object p1

// Every position, each on the line #member prints at level 1 -- the timber ones written down for the checks of SIA 265 4.2 on the way --, and every connector saved in Woodcore (docs/domain/member-checks.md §3.3undecies, docs/domain/positions.md §7, docs/domain/connectors.md §7bis).
#for id in position-ids() {
  member(id, level: 1, description: true)
}

#if connector-ids().len() > 0 [
  == Fasteners

  #for id in connector-ids() {
    show-connector(id, description: true)
    parbreak()
  }
]
