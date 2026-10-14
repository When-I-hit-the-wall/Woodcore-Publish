#import "/commands.typ": *

// woodcore:object heading title
== Lastfälle: Tragsicherheit
// woodcore:/object title

// woodcore:object text p1
Jeder Lastfall wird durch eine Leiteinwirkung und die gleichzeitig mit ihr auftretenden Begleiteinwirkungen charakterisiert (SIA 260, Ziffer 4.2.6). Die folgenden Werte sind die auf die charakteristischen Werte angewendeten Beiwerte; für eine Begleiteinwirkung beträgt der Beiwert $γ_Q$ · ψ₀ [$γ_Q$ und ψ₀ oder ihr Produkt angeben].
// woodcore:/object p1

// woodcore:object doc-table uls-load-cases-table
#doc-table(
  columns: (
    (id: "element", title: [Bauteil]),
    (id: "case", title: [Lastfall]),
    (id: "permanent", title: [Eigengewicht und ständige Lasten], kind: "number"),
    (id: "live", title: [Nutzlast [Kategorie]], kind: "number"),
    (id: "snow", title: [Schnee], kind: "number"),
    (id: "wind", title: [Wind], kind: "math"),
  ),
  hidden: (),
  rows: (
    (element: [[Dach]], case: [CC 1], permanent: 1.35, live: [–], snow: 1.5, wind: [$γ_Q · ψ_0$]),
    (element: [[Dach]], case: [CC 2], permanent: 0.8, live: [–], snow: [–], wind: 1.5),
  ),
  caption: [Lastfälle: Tragsicherheit],
)
// woodcore:/object uls-load-cases-table
