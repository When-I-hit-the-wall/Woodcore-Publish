#import "/commands.typ": *

// woodcore:object heading title
== Structural and analytical model
// woodcore:/object title

// woodcore:object table structural-model-table
#figure(
  table(
    columns: (auto, 1fr),
    align: (left, left),
    table.hline(stroke: 1pt),
    [Software and analytical model], [[Analysis software, type of model (beam, finite element), level of detail.]],
    [Static system and supports], [[…]],
    [Stiffnesses assumed], [[Stiffness of the ground, of connections (slip moduli), of composite members, cracking.]],
    [Second-order effects], [[…]],
    [Ground-structure interaction], [[…]],
    [Moisture and load duration (timber)], [[…]],
    [Plausibility check], [[The results of the structural analysis are checked for plausibility (SIA 260, 3.1.4).]],
    table.hline(stroke: 1pt),
  ),
  caption: [Modelling assumptions],
)
// woodcore:/object structural-model-table
