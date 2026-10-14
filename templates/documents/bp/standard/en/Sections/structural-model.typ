#import "/commands.typ": *

// woodcore:object heading title
== Structural and analytical model
// woodcore:/object title

// woodcore:object doc-table structural-model-table
#doc-table(
  columns: (
    (id: "item", title: [Item]),
    (id: "text", title: [Description], kind: "wide"),
  ),
  hidden: (),
  rows: (
    (item: [Software and analytical model], text: [[Analysis software, type of model (beam, finite element), level of detail.]]),
    (item: [Static system and supports], text: [[…]]),
    (item: [Stiffnesses assumed], text: [[Stiffness of the ground, of connections (slip moduli), of composite members, cracking.]]),
    (item: [Second-order effects], text: [[…]]),
    (item: [Ground-structure interaction], text: [[…]]),
    (item: [Moisture and load duration (timber)], text: [[…]]),
    (item: [Plausibility check], text: [[The results of the structural analysis are checked for plausibility (SIA 260, 3.1.4).]]),
  ),
  caption: [Modelling assumptions],
  header: false,
)
// woodcore:/object structural-model-table
