#import "/commands.typ": *

// woodcore:object heading title
== Open points
// woodcore:/object title

// woodcore:object text p1
The following points are to be clarified or examined in detail in the next project phase:
// woodcore:/object p1

// woodcore:object doc-table open-points-table
#doc-table(
  columns: (
    (id: "point", title: [Point to clarify]),
    (id: "owner", title: [Responsible]),
    (id: "phase", title: [Phase / deadline]),
    (id: "status", title: [Status]),
  ),
  hidden: ("status",),
  rows: (
    (point: [[…]], owner: [[…]], phase: [[…]], status: []),
    (point: [[…]], owner: [[…]], phase: [[…]], status: []),
  ),
  caption: [Open points],
)
// woodcore:/object open-points-table
