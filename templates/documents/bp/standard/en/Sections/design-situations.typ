#import "/commands.typ": *

// woodcore:object heading title
== Design situations
// woodcore:/object title

// woodcore:object text p1
The design situations considered include all foreseeable conditions that may occur during execution and use (SIA 260, 4.2.1). They are divided into persistent, transient and accidental situations; construction states may be treated as persistent or transient design situations (4.2.2 and 4.2.3).
// woodcore:/object p1

// woodcore:object table design-situations-table
#figure(
  table(
    columns: (auto, auto, auto),
    align: (left, left, left),
    table.hline(stroke: 1pt),
    table.header([*Situation*], [*Description*], [*Governing load cases*]),
    table.hline(stroke: 0.5pt),
    [Persistent], [[Normal use]], [[…]],
    [Transient], [[Construction states]], [[…]],
    [Accidental], [[Earthquake, fire, impact]], [[…]],
    table.hline(stroke: 1pt),
  ),
  caption: [Design situations],
)
// woodcore:/object design-situations-table
