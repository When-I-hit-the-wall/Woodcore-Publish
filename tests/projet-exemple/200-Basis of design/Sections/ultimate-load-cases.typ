#import "/000-Typst-Config/commands.typ": *

// woodcore:object heading title
== Lastfälle: Tragsicherheit
// woodcore:/object title

// woodcore:object text p1
Jeder Lastfall wird durch eine Leiteinwirkung und die gleichzeitig mit ihr auftretenden Begleiteinwirkungen charakterisiert (SIA 260, Ziffer 4.2.6). Die folgenden Werte sind die auf die charakteristischen Werte angewendeten Beiwerte; für eine Begleiteinwirkung beträgt der Beiwert $γ_Q$ · ψ₀ [$γ_Q$ und ψ₀ oder ihr Produkt angeben].
// woodcore:/object p1

// woodcore:object table uls-load-cases-table
#figure(
  table(
    columns: (auto, auto, auto, auto, auto, auto),
    align: (left, left, right, right, right, center),
    table.hline(stroke: 1pt),
    table.header([*Bauteil*], [*Lastfall*], [*Eigengewicht und ständige Lasten*], [*Nutzlast [Kategorie]*], [*Schnee*], [*Wind*]),
    table.hline(stroke: 0.5pt),
    [[Dach]], [CC 1], [1.35], [–], [1.5], [$γ_Q · ψ_0$],
    [[Dach]], [CC 2], [0.8], [–], [–], [1.5],
    table.hline(stroke: 1pt),
  ),
  caption: [Lastfälle: Tragsicherheit],
)
// woodcore:/object uls-load-cases-table
