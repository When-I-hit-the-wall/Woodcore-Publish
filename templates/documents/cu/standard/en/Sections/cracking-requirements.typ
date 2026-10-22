#import "/commands.typ": *

// woodcore:object heading title
== Requirements for cracking
// woodcore:/object title

// woodcore:object text p1
SIA 262 distinguishes three levels of requirement for cracking: normal where cracks are tolerated and no particular requirements are placed on tightness and appearance; increased where there are particular requirements for functionality and appearance and good crack distribution is sought; high where a limitation of crack widths is wanted. These requirements apply to imposed-deformation effects (e.g. shrinkage) as well as to bending; increased or high requirements reduce the permissible steel stresses and increase the reinforcement content.
// woodcore:/object p1

// woodcore:object table cracking-requirements-table
#figure(
  table(
    columns: (auto, auto),
    align: (left, left),
    table.hline(stroke: 1pt),
    table.header([*Area*], [*Requirement*]),  // woodcore:hidden 3=[Mean crack width $w_m$] 4=[Maximum crack width $w_"max"$]
    table.hline(stroke: 0.5pt),
    [[General]], [Normal],  // woodcore:hidden 3=[0.7] 4=[1.2]
    [[Exposed concrete members]], [Increased],  // woodcore:hidden 3=[0.5] 4=[0.9]
    table.hline(stroke: 1pt),
  ),
  caption: [Requirements by area],
)
// woodcore:/object cracking-requirements-table

// woodcore:object text cracking-requirements-table-notes
Expected crack widths for the three levels: $w_m$ = 0.7 / 0.5 / 0.25 mm and $w_"max"$ = 1.2 / 0.9 / 0.4 mm ($w_"max"$ = 1.7 · $w_m$, 95 % fractile), based on the tension chord model (SIA documentation D 0182).
// woodcore:/object cracking-requirements-table-notes
