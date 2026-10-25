#import "../commands.typ": *

= Einwirkungen

// Every case entered in Woodcore's tabs of loads, one file each (docs/domain/calculation-domains.md §3.3). Name the cases by hand instead -- #include domain-file("snow-load", "SL") -- to leave some out. The live loads are SIA 261's Tabelle 8, one category a file: #include domain-file("live-load", "A1").

== Eigengewicht

#for case in ids("dead-load") {
  include domain-file("dead-load", case)
}

== Schneelast

#for case in ids("snow-load") {
  include domain-file("snow-load", case)
}

== Windlast

#for case in ids("wind-load") {
  include domain-file("wind-load", case)
}
