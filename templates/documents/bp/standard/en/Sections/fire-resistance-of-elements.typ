#import "/commands.typ": *

// woodcore:object heading title
== Fire resistance of building elements
// woodcore:/object title

// woodcore:object table fire-resistance-table
#figure(
  table(
    columns: (auto, auto, auto, auto, auto),
    align: (left, left, left, left, left),
    table.hline(stroke: 1pt),
    table.header([*Category*], [*Zone / element*], [*Basis*], [*Requirement*], [*Execution / values*]),
    table.hline(stroke: 0.5pt),
    [Load-bearing structure], [[Basement – ground floor]], [VKF 15-15], [R 60], [[…]],
    [Fire compartments], [[Slab above ground floor]], [VKF 15-15], [REI 60], [[…]],
    table.hline(stroke: 1pt),
  ),
  caption: [Fire resistance of building elements],
)
// woodcore:/object fire-resistance-table
