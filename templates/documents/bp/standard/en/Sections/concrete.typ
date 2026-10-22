#import "/commands.typ": *

// woodcore:object heading title
== Concrete
// woodcore:/object title

// woodcore:object table concrete-table
#figure(
  table(
    columns: (auto, auto, auto, auto, auto, auto),
    align: (left, left, right, right, right, right),
    table.hline(stroke: 1pt),
    table.header([*Member*], [*Strength class*], [*Characteristic strength $f_"ck"$*], [*Design strength $f_"cd"$*], [*Design shear stress $tau_"cd"$*], [*Unit weight $gamma$*]),  // woodcore:hidden 6=[Mean modulus of elasticity $E_"cm"$]
    table.hline(stroke: 0.5pt),
    [[Member]], [C25/30], [25], [[…]], [[…]], [25],  // woodcore:hidden 6=[[…]]
    [[Member]], [C30/37], [30], [[…]], [[…]], [25],  // woodcore:hidden 6=[[…]]
    table.hline(stroke: 1pt),
  ),
  caption: [Reinforced concrete (SIA 262)],
)
// woodcore:/object concrete-table

// woodcore:object text concrete-table-notes
Design values in accordance with SIA 262:2025. The durability requirements (exposure classes) are given in the section “Durability”.
// woodcore:/object concrete-table-notes
