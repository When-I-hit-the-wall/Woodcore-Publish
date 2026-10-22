#import "/commands.typ": *

// woodcore:object heading title
== Offene Punkte
// woodcore:/object title

// woodcore:object text p1
Die folgenden Punkte sind in der nächsten Projektphase zu klären bzw. im Detail zu untersuchen:
// woodcore:/object p1

// woodcore:object table open-points-table
#figure(
  table(
    columns: (auto, auto, auto),
    align: (left, left, left),
    table.hline(stroke: 1pt),
    table.header([*Zu klärender Punkt*], [*Verantwortlich*], [*Phase / Termin*]),  // woodcore:hidden 4=[Stand]
    table.hline(stroke: 0.5pt),
    [[…]], [[…]], [[…]],  // woodcore:hidden 4=[]
    [[…]], [[…]], [[…]],  // woodcore:hidden 4=[]
    table.hline(stroke: 1pt),
  ),
  caption: [Offene Punkte],
)
// woodcore:/object open-points-table
