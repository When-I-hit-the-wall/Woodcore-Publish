#import "/commands.typ": *

// woodcore:object heading title
= Actions
// woodcore:/object title

// Every case of the load workbooks, one sheet each (docs/domain/calculation-domains.md §3.3). Name the cases by hand instead -- #show-calc("snow-load", "SL", level: 1) -- to choose each one's level and leave some out. The live loads are SIA 261's Tabelle 8, one category per call: #show-live-load("A1").

// woodcore:object heading h2
== Self-weight
// woodcore:/object h2

#for sheet in instance-ids("dead-load") {
  show-calc("dead-load", sheet)
}

// woodcore:object heading h3
== Snow load
// woodcore:/object h3

#for sheet in instance-ids("snow-load") {
  show-calc("snow-load", sheet)
}

// woodcore:object heading h4
== Wind load
// woodcore:/object h4

#for sheet in instance-ids("wind-load") {
  show-calc("wind-load", sheet)
}
