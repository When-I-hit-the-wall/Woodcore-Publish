#import "/commands.typ": *

// woodcore:object heading title
== Requirements for cracking
// woodcore:/object title

// woodcore:object text p1
SIA 262 distinguishes three levels of requirement for cracking: normal where cracks are tolerated and no particular requirements are placed on tightness and appearance; increased where there are particular requirements for functionality and appearance and good crack distribution is sought; high where a limitation of crack widths is wanted. These requirements apply to imposed-deformation effects (e.g. shrinkage) as well as to bending; increased or high requirements reduce the permissible steel stresses and increase the reinforcement content.
// woodcore:/object p1

// woodcore:object doc-table cracking-requirements-table
#doc-table(
  columns: (
    (id: "area", title: [Area]),
    (id: "level", title: [Requirement]),
    (id: "wm", title: [Mean crack width $w_m$], unit: "mm", kind: "number"),
    (id: "wmax", title: [Maximum crack width $w_"max"$], unit: "mm", kind: "number"),
  ),
  hidden: ("wm", "wmax"),
  rows: (
    (area: [[General]], level: [Normal], wm: 0.7, wmax: 1.2),
    (area: [[Exposed concrete members]], level: [Increased], wm: 0.5, wmax: 0.9),
  ),
  caption: [Requirements by area],
  notes: (
    [Expected crack widths for the three levels: $w_m$ = 0.7 / 0.5 / 0.25 mm and $w_"max"$ = 1.2 / 0.9 / 0.4 mm ($w_"max"$ = 1.7 · $w_m$, 95 % fractile), based on the tension chord model (SIA documentation D 0182).],
  ),
)
// woodcore:/object cracking-requirements-table
