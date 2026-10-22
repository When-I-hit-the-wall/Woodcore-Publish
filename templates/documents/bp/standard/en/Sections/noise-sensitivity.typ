#import "/commands.typ": *

// woodcore:object heading title
== Noise sensitivity of rooms in accordance with SIA 181
// woodcore:/object title

// woodcore:object table noise-sensitivity-table
#figure(
  table(
    columns: (auto, auto),
    align: (left, left),
    table.hline(stroke: 1pt),
    table.header([*Room*], [*Noise sensitivity*]),
    table.hline(stroke: 0.5pt),
    [[Plant room, storage]], [None],
    [[Bedrooms, seminar room]], [Medium],
    table.hline(stroke: 1pt),
  ),
  caption: [Noise sensitivity of rooms],
)
// woodcore:/object noise-sensitivity-table
