#import "/commands.typ": *

// woodcore:object heading title
== Reinforcing steel
// woodcore:/object title

// woodcore:object table reinforcing-steel-table
#figure(
  table(
    columns: (auto, auto, auto, auto, auto),
    align: (left, right, right, right, right),
    table.hline(stroke: 1pt),
    table.header([*Designation*], [*Characteristic yield strength $f_"sk"$*], [*Design yield strength $f_"sd"$*], [*Modulus of elasticity $E_s$*], [*Unit weight $gamma$*]),
    table.hline(stroke: 0.5pt),
    [B500B], [500], [[…]], [[…]], [78.5],
    table.hline(stroke: 1pt),
  ),
  caption: [Reinforcing steel (SIA 262)],
)
// woodcore:/object reinforcing-steel-table

// woodcore:object text reinforcing-steel-table-notes
Design values in accordance with SIA 262:2025.
// woodcore:/object reinforcing-steel-table-notes
