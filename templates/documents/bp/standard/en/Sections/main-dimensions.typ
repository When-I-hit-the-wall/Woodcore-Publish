#import "/commands.typ": *

// woodcore:object heading title
== Main dimensions
// woodcore:/object title

// woodcore:object text p1
The main dimensions of the load-bearing members are recorded in the structural concept drawings and are based on the static dimensioning of the building.
// woodcore:/object p1

// woodcore:object doc-table main-dimensions-table
#doc-table(
  columns: (
    (id: "position", title: [Position]),
    (id: "member", title: [Member]),
    (id: "material", title: [Material / strength class]),
    (id: "section", title: [Dimensions]),
    (id: "remark", title: [Remark]),
  ),
  hidden: ("remark",),
  rows: (
    (position: [[…]], member: [[Main beam]], material: [[…]], section: [[…]], remark: []),
    (position: [[…]], member: [[Column]], material: [[…]], section: [[…]], remark: []),
  ),
  caption: [Main load-bearing members],
)
// woodcore:/object main-dimensions-table
