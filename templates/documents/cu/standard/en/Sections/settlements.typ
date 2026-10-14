#import "/commands.typ": *

// woodcore:object heading title
== Settlements
// woodcore:/object title
// woodcore:shared settlements

// woodcore:object text p1
Settlements must not have any harmful effects on the building or its surroundings (adjacent buildings, pipes, roads, etc.). To ensure this, the following permissible limits are set for settlement behaviour:
// woodcore:/object p1

// woodcore:object doc-table settlements-table
#doc-table(
  columns: (
    (id: "kind", title: [Settlement]),
    (id: "limit", title: [Limit], unit: "mm", kind: "number"),
    (id: "basis", title: [Reference / validity]),
  ),
  hidden: (),
  rows: (
    (kind: [Absolute settlement], limit: [[…]], basis: [[from completion of the basement slab]]),
    (kind: [Differential settlement], limit: [[…]], basis: [[over a length of … m]]),
  ),
  caption: [Settlement limits],
)
// woodcore:/object settlements-table
// woodcore:/shared settlements
