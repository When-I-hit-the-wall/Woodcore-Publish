#import "/commands.typ": *

// woodcore:object heading title
== Bewehrungsstahl
// woodcore:/object title

// woodcore:object table reinforcing-steel-table
#figure(
  table(
    columns: (auto, auto, auto, auto, auto),
    align: (left, right, right, right, right),
    table.hline(stroke: 1pt),
    table.header([*Bezeichnung*], [*Charakteristische Streckgrenze $f_"sk"$*], [*Bemessungswert der Streckgrenze $f_"sd"$*], [*Elastizitätsmodul $E_s$*], [*Raumlast $gamma$*]),
    table.hline(stroke: 0.5pt),
    [B500B], [500], [[…]], [[…]], [78.5],
    table.hline(stroke: 1pt),
  ),
  caption: [Betonstahl (SIA 262)],
)
// woodcore:/object reinforcing-steel-table

// woodcore:object text reinforcing-steel-table-notes
Bemessungswerte nach der Norm SIA 262:2025.
// woodcore:/object reinforcing-steel-table-notes
