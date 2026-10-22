#import "/commands.typ": *

// woodcore:object heading title
== Lärmempfindlichkeit der Räume nach SIA 181
// woodcore:/object title

// woodcore:object table noise-sensitivity-table
#figure(
  table(
    columns: (auto, auto),
    align: (left, left),
    table.hline(stroke: 1pt),
    table.header([*Raum*], [*Lärmempfindlichkeit*]),
    table.hline(stroke: 0.5pt),
    [[Technikraum, Lager]], [Keine],
    [[Zimmer, Seminarraum]], [Mittel],
    table.hline(stroke: 1pt),
  ),
  caption: [Lärmempfindlichkeit der Räume],
)
// woodcore:/object noise-sensitivity-table
