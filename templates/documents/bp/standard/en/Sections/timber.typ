#import "/commands.typ": *

// woodcore:object heading title
== Timber and wood-based materials
// woodcore:/object title

// woodcore:object doc-table timber-table
#doc-table(
  columns: (
    (id: "designation", title: [Designation]),
    (id: "fmd", title: [Bending $f_"md"$], unit: "N/mm²", kind: "number"),
    (id: "fc0d", title: [Compression parallel to the grain $f_(c,0,d)$], unit: "N/mm²", kind: "number"),
    (id: "fvd", title: [Shear $f_"vd"$], unit: "N/mm²", kind: "number"),
    (id: "E0", title: [Mean modulus of elasticity $E_(0,"mean")$], unit: "N/mm²", kind: "number"),
    (id: "rho", title: [Characteristic density $rho_k$], unit: "kg/m³", kind: "number"),
    (id: "gamma", title: [Unit weight $gamma$], unit: "kN/m³", kind: "number"),
  ),
  hidden: ("rho", "gamma"),
  rows: (
    (designation: [C24], fmd: 14.1, fc0d: 12.4, fvd: 1.5, E0: 11000, rho: 350, gamma: 5),
    (designation: [GL24h], fmd: 16.0, fc0d: 16.0, fvd: 1.8, E0: 11500, rho: 385, gamma: 5),
  ),
  caption: [Solid timber and glulam (SIA 265, design values for moisture class 1)],
  notes: (
    [The strength and stiffness properties, the resistance factors and the factors taking account of load duration are applied in accordance with the SIA standards in force. For wood-based materials (panels, cross-laminated timber) the values of SIA 265/1 apply.],
  ),
)
// woodcore:/object timber-table
