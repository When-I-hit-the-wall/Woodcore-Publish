#import "/commands.typ": *

// woodcore:object heading title
== Structural system
// woodcore:/object title

// woodcore:object doc-table structural-system-table
#doc-table(
  columns: (
    (id: "item", title: [Item]),
    (id: "text", title: [Description], kind: "wide"),
  ),
  hidden: (),
  rows: (
    (item: [Vertical structural system], text: [[Columns, walls, cores, foundations …]]),
    (item: [Floor and roof systems], text: [[Floor system by storey, principal span direction, load-carrying action (one-way or two-way), role of the timber in a composite section …]]),
    (item: [Wall and column systems], text: [[Material and layout by storey, main sections …]]),
    (item: [Transfer structures], text: [[Transfer elements: beams, slabs, trusses; storeys concerned …]]),
    (item: [Load path], text: [[…]]),
    (item: [Variants studied], text: [[Reference to variant studies where applicable.]]),
  ),
  caption: [Structural system],
  header: false,
)
// woodcore:/object structural-system-table
