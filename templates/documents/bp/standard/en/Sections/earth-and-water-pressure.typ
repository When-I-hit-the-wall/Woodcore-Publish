#import "/commands.typ": *

// woodcore:object heading title
=== Earth and water pressure
// woodcore:/object title

// woodcore:object doc-table earth-water-table
#doc-table(
  columns: (
    (id: "item", title: [Item]),
    (id: "text", title: [Description], kind: "wide"),
  ),
  hidden: (),
  rows: (
    (item: [Earth pressure], text: [[Earth pressure coefficients, unit weight of the soil, soil surcharges, calculation assumptions.]]),
    (item: [Water pressure], text: [[Design water levels (see “Ground”), treatment as a permanent or variable action.]]),
  ),
  caption: [Actions from the ground],
  header: false,
)
// woodcore:/object earth-water-table
