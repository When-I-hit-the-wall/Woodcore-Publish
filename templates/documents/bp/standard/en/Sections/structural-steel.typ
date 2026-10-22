#import "/commands.typ": *

// woodcore:object heading title
== Structural steel and fasteners
// woodcore:/object title

// woodcore:object table structural-steel-table
#figure(
  table(
    columns: (auto, auto, auto, auto),
    align: (left, left, right, right),
    table.hline(stroke: 1pt),
    table.header([*Grade*], [*Thickness*], [*Yield strength $f_y$*], [*Tensile strength $f_u$*]),  // woodcore:hidden 5=[Modulus of elasticity $E_a$] 6=[Unit weight $gamma$]
    table.hline(stroke: 0.5pt),
    [S235], [t ≤ 40 mm], [235], [360],  // woodcore:hidden 5=[210000] 6=[78.5]
    [S355], [t ≤ 40 mm], [355], [510],  // woodcore:hidden 5=[210000] 6=[78.5]
    table.hline(stroke: 1pt),
  ),
  caption: [Structural steel (SIA 263)],
)
// woodcore:/object structural-steel-table

// woodcore:object table bolts-table
#figure(
  table(
    columns: (auto, auto, auto, auto),
    align: (left, right, right, left),
    table.hline(stroke: 1pt),
    table.header([*Strength class*], [*Yield strength $f_"yb"$*], [*Tensile strength $f_"ub"$*], [*Use*]),
    table.hline(stroke: 0.5pt),
    [4.6], [240], [400], [Bolts, lag screws],
    [8.8], [640], [800], [Wood screws (minimum class)],
    table.hline(stroke: 1pt),
  ),
  caption: [Bolts, lag screws and wood screws (SIA 263)],
)
// woodcore:/object bolts-table

// woodcore:object text bolts-table-notes
Dowels of S355 steel are calculated with $f_(u,k)$ = 510 N/mm² (SN EN 14592).
// woodcore:/object bolts-table-notes
