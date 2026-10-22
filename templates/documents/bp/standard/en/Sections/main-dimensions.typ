#import "/commands.typ": *

// woodcore:object heading title
== Main dimensions
// woodcore:/object title

// woodcore:object text p1
The main dimensions of the load-bearing members are recorded in the structural concept drawings and are based on the static dimensioning of the building.
// woodcore:/object p1

// woodcore:object table main-dimensions-table
#figure(
  table(
    columns: (auto, auto, auto, auto),
    align: (left, left, left, left),
    table.hline(stroke: 1pt),
    table.header([*Position*], [*Member*], [*Material / strength class*], [*Dimensions*]),  // woodcore:hidden 5=[Remark]
    table.hline(stroke: 0.5pt),
    [[…]], [[Main beam]], [[…]], [[…]],  // woodcore:hidden 5=[]
    [[…]], [[Column]], [[…]], [[…]],  // woodcore:hidden 5=[]
    table.hline(stroke: 1pt),
  ),
  caption: [Main load-bearing members],
)
// woodcore:/object main-dimensions-table
