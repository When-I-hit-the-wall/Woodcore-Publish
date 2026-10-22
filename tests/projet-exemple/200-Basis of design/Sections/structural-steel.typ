#import "/000-Typst-Config/commands.typ": *

// woodcore:object heading title
== Baustahl und Verbindungsmittel
// woodcore:/object title

// woodcore:object table structural-steel-table
#figure(
  table(
    columns: (auto, auto, auto, auto),
    align: (left, left, right, right),
    table.hline(stroke: 1pt),
    table.header([*Stahlsorte*], [*Dicke*], [*Streckgrenze $f_y$*], [*Zugfestigkeit $f_u$*]),  // woodcore:hidden 5=[Elastizitätsmodul $E_a$] 6=[Raumlast $gamma$]
    table.hline(stroke: 0.5pt),
    [S235], [t ≤ 40 mm], [235], [360],  // woodcore:hidden 5=[210000] 6=[78.5]
    [S355], [t ≤ 40 mm], [355], [510],  // woodcore:hidden 5=[210000] 6=[78.5]
    table.hline(stroke: 1pt),
  ),
  caption: [Baustahl (SIA 263)],
)
// woodcore:/object structural-steel-table

// woodcore:object table bolts-table
#figure(
  table(
    columns: (auto, auto, auto, auto),
    align: (left, right, right, left),
    table.hline(stroke: 1pt),
    table.header([*Festigkeitsklasse*], [*Streckgrenze $f_"yb"$*], [*Zugfestigkeit $f_"ub"$*], [*Verwendung*]),
    table.hline(stroke: 0.5pt),
    [4.6], [240], [400], [Bolzen, Schlüsselschrauben],
    [8.8], [640], [800], [Holzschrauben (Mindestklasse)],
    table.hline(stroke: 1pt),
  ),
  caption: [Schrauben und Holzschrauben (SIA 263)],
)
// woodcore:/object bolts-table

// woodcore:object text bolts-table-notes
Stabdübel aus Stahl S355 werden mit $f_(u,k)$ = 510 N/mm² berechnet (SN EN 14592).
// woodcore:/object bolts-table-notes
