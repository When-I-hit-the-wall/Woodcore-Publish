#import "../commands.typ": *

= Einwirkungen

// Every case of the load workbooks, one sheet each (docs/domain/calculation-domains.md §3.3). Name the cases by hand instead -- #include domain-file("snow-load", "SL") -- to leave some out. The live loads are SIA 261's Tabelle 8, one category a file: #include domain-file("live-load", "A1").

== Eigengewicht

#for sheet in ids("dead-load") {
  include domain-file("dead-load", sheet)
}

== Schneelast

#for sheet in ids("snow-load") {
  include domain-file("snow-load", sheet)
}

== Windlast

#for sheet in ids("wind-load") {
  include domain-file("wind-load", sheet)
}
