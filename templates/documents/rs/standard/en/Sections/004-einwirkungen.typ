#import "/commands.typ": *

// woodcore:object heading title
= Actions
// woodcore:/object title

// Every case of the load workbooks, one sheet each (docs/domain/calculation-domains.md §3.3). Name the cases by hand instead -- #include domain-file("snow-load", "SL") -- to leave some out. The live loads are SIA 261's Tabelle 8, one category a file: #include domain-file("live-load", "A1").

// woodcore:object heading h2
== Self-weight
// woodcore:/object h2

#for sheet in ids("dead-load") {
  include domain-file("dead-load", sheet)
}

// woodcore:object heading h3
== Snow load
// woodcore:/object h3

#for sheet in ids("snow-load") {
  include domain-file("snow-load", sheet)
}

// woodcore:object heading h4
== Wind load
// woodcore:/object h4

#for sheet in ids("wind-load") {
  include domain-file("wind-load", sheet)
}
