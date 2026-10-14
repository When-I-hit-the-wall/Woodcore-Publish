#import "/commands.typ": *

// woodcore:object heading title
== Fire resistance of building elements
// woodcore:/object title

// woodcore:object doc-table fire-resistance-table
#doc-table(
  columns: (
    (id: "category", title: [Category]),
    (id: "zone", title: [Zone / element]),
    (id: "basis", title: [Basis]),
    (id: "requirement", title: [Requirement]),
    (id: "execution", title: [Execution / values]),
  ),
  hidden: (),
  rows: (
    (category: [Load-bearing structure], zone: [[Basement – ground floor]], basis: [VKF 15-15], requirement: [R 60], execution: [[…]]),
    (category: [Fire compartments], zone: [[Slab above ground floor]], basis: [VKF 15-15], requirement: [REI 60], execution: [[…]]),
  ),
  caption: [Fire resistance of building elements],
)
// woodcore:/object fire-resistance-table
