#import "/commands.typ": *

// woodcore:object heading title
= Actions
// woodcore:/object title

// Every case entered in Woodcore's tabs of loads, one file each (docs/domain/calculation-domains.md §3.3). Name the cases by hand instead -- #include domain-file("snow-load", "SL") -- to leave some out. The live loads are SIA 261's Tabelle 8, one category a file: #include domain-file("live-load", "A1").

// woodcore:object heading h2
== Poids propre
// woodcore:/object h2

#for case in ids("dead-load") {
  include domain-file("dead-load", case)
}

// woodcore:object heading h3
== Charge de neige
// woodcore:/object h3

#for case in ids("snow-load") {
  include domain-file("snow-load", case)
}

// woodcore:object heading h4
== Charge de vent
// woodcore:/object h4

#for case in ids("wind-load") {
  include domain-file("wind-load", case)
}
