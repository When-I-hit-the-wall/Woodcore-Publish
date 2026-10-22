#import "/commands.typ": *

// woodcore:object heading title
== Points ouverts
// woodcore:/object title

// woodcore:object text p1
Les points suivants sont à clarifier ou à étudier en détail dans la phase suivante du projet :
// woodcore:/object p1

// woodcore:object table open-points-table
#figure(
  table(
    columns: (auto, auto, auto),
    align: (left, left, left),
    table.hline(stroke: 1pt),
    table.header([*Point à clarifier*], [*Responsable*], [*Phase / échéance*]),  // woodcore:hidden 4=[État]
    table.hline(stroke: 0.5pt),
    [[…]], [[…]], [[…]],  // woodcore:hidden 4=[]
    [[…]], [[…]], [[…]],  // woodcore:hidden 4=[]
    table.hline(stroke: 1pt),
  ),
  caption: [Points ouverts],
)
// woodcore:/object open-points-table
