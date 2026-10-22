#import "/commands.typ": *

// woodcore:object heading title
== Settlements
// woodcore:/object title
// woodcore:shared settlements

// woodcore:object text p1
Settlements must not have any harmful effects on the building or its surroundings (adjacent buildings, pipes, roads, etc.). To ensure this, the following permissible limits are set for settlement behaviour:
// woodcore:/object p1

// woodcore:object table settlements-table
#figure(
  table(
    columns: (auto, auto, auto),
    align: (left, right, left),
    table.hline(stroke: 1pt),
    table.header([*Settlement*], [*Limit*], [*Reference / validity*]),
    table.hline(stroke: 0.5pt),
    [Absolute settlement], [[…]], [[from completion of the basement slab]],
    [Differential settlement], [[…]], [[over a length of … m]],
    table.hline(stroke: 1pt),
  ),
  caption: [Settlement limits],
)
// woodcore:/object settlements-table
// woodcore:/shared settlements
