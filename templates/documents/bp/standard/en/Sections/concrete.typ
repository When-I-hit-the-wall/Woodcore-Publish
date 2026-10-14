#import "/commands.typ": *

// woodcore:object heading title
== Concrete
// woodcore:/object title

// woodcore:object doc-table concrete-table
#doc-table(
  columns: (
    (id: "member", title: [Member]),
    (id: "class", title: [Strength class]),
    (id: "fck", title: [Characteristic strength $f_"ck"$], unit: "N/mm²", kind: "number"),
    (id: "fcd", title: [Design strength $f_"cd"$], unit: "N/mm²", kind: "number"),
    (id: "taucd", title: [Design shear stress $tau_"cd"$], unit: "N/mm²", kind: "number"),
    (id: "Ecm", title: [Mean modulus of elasticity $E_"cm"$], unit: "N/mm²", kind: "number"),
    (id: "gamma", title: [Unit weight $gamma$], unit: "kN/m³", kind: "number"),
  ),
  hidden: ("Ecm",),
  rows: (
    (member: [[Member]], class: [C25/30], fck: 25, fcd: [[…]], taucd: [[…]], Ecm: [[…]], gamma: 25),
    (member: [[Member]], class: [C30/37], fck: 30, fcd: [[…]], taucd: [[…]], Ecm: [[…]], gamma: 25),
  ),
  caption: [Reinforced concrete (SIA 262)],
  notes: (
    [Design values in accordance with SIA 262:2025.],
    [The durability requirements (exposure classes) are given in the section “Durability”.],
  ),
)
// woodcore:/object concrete-table
