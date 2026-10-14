#import "/commands.typ": *

// woodcore:object heading title
== Requirements by building part
// woodcore:/object title

// woodcore:object doc-table maintenance-table
#doc-table(
  columns: (
    (id: "item", title: [Item]),
    (id: "text", title: [Description], kind: "wide"),
  ),
  hidden: (),
  rows: (
    (item: [Roof], text: [[Waterproofing, accessible drainage, roof accessible for maintenance and snow clearance. Snow depth taken into account in the design; beyond it, snow clearance at the owner's expense.]]),
    (item: [Upper floors], text: [[…]]),
    (item: [Ground floor], text: [[…]]),
    (item: [Basements], text: [[…]]),
    (item: [Facade], text: [[Replaceable independently of the load-bearing elements; preferred material (e.g. timber cladding).]]),
  ),
  caption: [Operational and maintenance requirements],
  header: false,
)
// woodcore:/object maintenance-table
