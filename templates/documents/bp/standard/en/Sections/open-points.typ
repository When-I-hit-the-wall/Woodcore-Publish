#import "/commands.typ": *

// woodcore:object heading title
== Open points
// woodcore:/object title

// woodcore:object text p1
The following points are to be clarified or examined in detail in the next project phase:
// woodcore:/object p1

// woodcore:object table open-points-table
#figure(
  table(
    columns: (auto, auto, auto),
    align: (left, left, left),
    table.hline(stroke: 1pt),
    table.header([*Point to clarify*], [*Responsible*], [*Phase / deadline*]),  // woodcore:hidden 4=[Status]
    table.hline(stroke: 0.5pt),
    [[…]], [[…]], [[…]],  // woodcore:hidden 4=[]
    [[…]], [[…]], [[…]],  // woodcore:hidden 4=[]
    table.hline(stroke: 1pt),
  ),
  caption: [Open points],
)
// woodcore:/object open-points-table
