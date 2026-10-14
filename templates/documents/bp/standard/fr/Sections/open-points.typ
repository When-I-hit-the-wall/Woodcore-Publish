#import "/commands.typ": *

// woodcore:object heading title
== Points ouverts
// woodcore:/object title

// woodcore:object text p1
Les points suivants sont à clarifier ou à étudier en détail dans la phase suivante du projet :
// woodcore:/object p1

// woodcore:object doc-table open-points-table
#doc-table(
  columns: (
    (id: "point", title: [Point à clarifier]),
    (id: "owner", title: [Responsable]),
    (id: "phase", title: [Phase / échéance]),
    (id: "status", title: [État]),
  ),
  hidden: ("status",),
  rows: (
    (point: [[…]], owner: [[…]], phase: [[…]], status: []),
    (point: [[…]], owner: [[…]], phase: [[…]], status: []),
  ),
  caption: [Points ouverts],
)
// woodcore:/object open-points-table
