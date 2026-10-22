#import "/commands.typ": *

// woodcore:object heading title
== Reduktionsbeiwerte
// woodcore:/object title

// woodcore:object text p1
Die Reduktionsbeiwerte ψ₀, ψ₁ und ψ₂ berücksichtigen die reduzierte Wahrscheinlichkeit des gleichzeitigen Auftretens der ungünstigsten Werte mehrerer unabhängiger Einwirkungen; sie liefern den seltenen, häufigen und quasi-ständigen Wert einer veränderlichen Einwirkung (SIA 260, Ziffer 3.2.3 und Anhang A, Tabelle 2). [Die Schneelast hängt von der Bezugshöhe h₀ gemäss SIA 261 ab.]
// woodcore:/object p1

// woodcore:object table reduction-factors-table
#figure(
  table(
    columns: (auto, auto, auto, auto),
    align: (left, center, center, center),
    table.hline(stroke: 1pt),
    table.header([*Einwirkung*], [*$psi_0$*], [*$psi_1$*], [*$psi_2$*]),
    table.hline(stroke: 0.5pt),
    [Nutzlast, Kategorie [A]], [0.7], [0.5], [0.3],
    [Nutzlast, Kategorie [C]], [0.7], [0.7], [0.6],
    [Nutzlast, Kategorie H], [0], [0], [0],
    [Schnee], [$1 - 60 \/ h_0$], [$1 - 250 \/ h_0$], [$1 - 1000 \/ h_0$],
    [Wind], [0.6], [0.5], [0],
    table.hline(stroke: 1pt),
  ),
  caption: [Reduktionsbeiwerte für Gebäude],
)
// woodcore:/object reduction-factors-table
