#import "/commands.typ": *

// woodcore:object heading title
== Horizontal displacements
// woodcore:/object title

// woodcore:object text p1
Horizontal displacements due to the variable actions are limited to the standard values of SIA 260, Appendix A, Table 4; h denotes the storey height and H the building height. For the earthquake design situation, the horizontal displacements per storey are limited to 1/500 or 1/200 of the storey height where fittings have brittle or ductile behaviour respectively (4.4.4.5).
// woodcore:/object p1

// woodcore:object table horizontal-limits-table
#figure(
  table(
    columns: (auto, auto, auto),
    align: (left, center, left),
    table.hline(stroke: 1pt),
    table.header([*Criterion*], [*Limit*], [*Load case (SIA 260, Table 4)*]),
    table.hline(stroke: 0.5pt),
    [Fittings with brittle behaviour], [$u <= h \/ 500$], [occasional (20)],
    [Fittings with ductile behaviour], [$u <= h \/ 200$], [frequent (21)],
    [Use and operation], [$u <= H \/ 300$], [frequent (21)],
    [Appearance], [$u <= h \/ 250$], [quasi-permanent (22)],
    table.hline(stroke: 1pt),
  ),
  caption: [Permissible horizontal displacements],
)
// woodcore:/object horizontal-limits-table
