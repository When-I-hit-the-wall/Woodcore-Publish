#import "/commands.typ": *

// woodcore:object heading title
== Structural steel and fasteners
// woodcore:/object title

// woodcore:object doc-table structural-steel-table
#doc-table(
  columns: (
    (id: "grade", title: [Grade]),
    (id: "band", title: [Thickness]),
    (id: "fy", title: [Yield strength $f_y$], unit: "N/mm²", kind: "number"),
    (id: "fu", title: [Tensile strength $f_u$], unit: "N/mm²", kind: "number"),
    (id: "Ea", title: [Modulus of elasticity $E_a$], unit: "N/mm²", kind: "number"),
    (id: "gamma", title: [Unit weight $gamma$], unit: "kN/m³", kind: "number"),
  ),
  hidden: ("Ea", "gamma"),
  rows: (
    (grade: [S235], band: [t ≤ 40 mm], fy: 235, fu: 360, Ea: 210000, gamma: 78.5),
    (grade: [S355], band: [t ≤ 40 mm], fy: 355, fu: 510, Ea: 210000, gamma: 78.5),
  ),
  caption: [Structural steel (SIA 263)],
)
// woodcore:/object structural-steel-table

// woodcore:object doc-table bolts-table
#doc-table(
  columns: (
    (id: "class", title: [Strength class]),
    (id: "fyb", title: [Yield strength $f_"yb"$], unit: "N/mm²", kind: "number"),
    (id: "fub", title: [Tensile strength $f_"ub"$], unit: "N/mm²", kind: "number"),
    (id: "use", title: [Use]),
  ),
  hidden: (),
  rows: (
    (class: [4.6], fyb: 240, fub: 400, use: [Bolts, lag screws]),
    (class: [8.8], fyb: 640, fub: 800, use: [Wood screws (minimum class)]),
  ),
  caption: [Bolts, lag screws and wood screws (SIA 263)],
  notes: (
    [Dowels of S355 steel are calculated with $f_(u,k)$ = 510 N/mm² (SN EN 14592).],
  ),
)
// woodcore:/object bolts-table
