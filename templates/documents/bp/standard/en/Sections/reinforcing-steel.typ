#import "/commands.typ": *

// woodcore:object heading title
== Reinforcing steel
// woodcore:/object title

// woodcore:object doc-table reinforcing-steel-table
#doc-table(
  columns: (
    (id: "designation", title: [Designation]),
    (id: "fsk", title: [Characteristic yield strength $f_"sk"$], unit: "N/mm²", kind: "number"),
    (id: "fsd", title: [Design yield strength $f_"sd"$], unit: "N/mm²", kind: "number"),
    (id: "Es", title: [Modulus of elasticity $E_s$], unit: "N/mm²", kind: "number"),
    (id: "gamma", title: [Unit weight $gamma$], unit: "kN/m³", kind: "number"),
  ),
  hidden: (),
  rows: (
    (designation: [B500B], fsk: 500, fsd: [[…]], Es: [[…]], gamma: 78.5),
  ),
  caption: [Reinforcing steel (SIA 262)],
  notes: (
    [Design values in accordance with SIA 262:2025.],
  ),
)
// woodcore:/object reinforcing-steel-table
