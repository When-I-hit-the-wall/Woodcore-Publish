#import "/commands.typ": *

// woodcore:object heading title
== Reduktionsbeiwerte
// woodcore:/object title

// woodcore:object text p1
Die Reduktionsbeiwerte ψ₀, ψ₁ und ψ₂ berücksichtigen die reduzierte Wahrscheinlichkeit des gleichzeitigen Auftretens der ungünstigsten Werte mehrerer unabhängiger Einwirkungen; sie liefern den seltenen, häufigen und quasi-ständigen Wert einer veränderlichen Einwirkung (SIA 260, Ziffer 3.2.3 und Anhang A, Tabelle 2). [Die Schneelast hängt von der Bezugshöhe h₀ gemäss SIA 261 ab.]
// woodcore:/object p1

// woodcore:object doc-table reduction-factors-table
#doc-table(
  columns: (
    (id: "action", title: [Einwirkung]),
    (id: "psi_0", title: [$psi_0$], kind: "math"),
    (id: "psi_1", title: [$psi_1$], kind: "math"),
    (id: "psi_2", title: [$psi_2$], kind: "math"),
  ),
  hidden: (),
  rows: (
    (action: [Nutzlast, Kategorie [A]], psi_0: 0.7, psi_1: 0.5, psi_2: 0.3),
    (action: [Nutzlast, Kategorie [C]], psi_0: 0.7, psi_1: 0.7, psi_2: 0.6),
    (action: [Nutzlast, Kategorie H], psi_0: 0, psi_1: 0, psi_2: 0),
    (action: [Schnee], psi_0: [$1 - 60 \/ h_0$], psi_1: [$1 - 250 \/ h_0$], psi_2: [$1 - 1000 \/ h_0$]),
    (action: [Wind], psi_0: 0.6, psi_1: 0.5, psi_2: 0),
  ),
  caption: [Reduktionsbeiwerte für Gebäude],
)
// woodcore:/object reduction-factors-table
