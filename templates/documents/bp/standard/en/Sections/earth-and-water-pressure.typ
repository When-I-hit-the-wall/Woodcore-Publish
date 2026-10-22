#import "/commands.typ": *

// woodcore:object heading title
=== Earth and water pressure
// woodcore:/object title

// woodcore:object table earth-water-table
#figure(
  table(
    columns: (auto, 1fr),
    align: (left, left),
    table.hline(stroke: 1pt),
    [Earth pressure], [[Earth pressure coefficients, unit weight of the soil, soil surcharges, calculation assumptions.]],
    [Water pressure], [[Design water levels (see “Ground”), treatment as a permanent or variable action.]],
    table.hline(stroke: 1pt),
  ),
  caption: [Actions from the ground],
)
// woodcore:/object earth-water-table
