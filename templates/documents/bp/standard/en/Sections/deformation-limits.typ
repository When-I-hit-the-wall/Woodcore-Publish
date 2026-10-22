#import "/commands.typ": *

// woodcore:object heading title
== Deformation limits (deflections)
// woodcore:/object title
// woodcore:shared deformation-limits

// woodcore:object text p1
Deflections are limited to the standard values of SIA 260, Appendix A, Table 3; they are determined in accordance with SIA 262 to 266. Different limit values may be agreed in line with the service requirements, in particular for secondary members; they are then specified in the basis of design. [The owner makes no more stringent requirements than the standard: yes / no.]
// woodcore:/object p1

// woodcore:object table deformation-table
#figure(
  table(
    columns: (auto, auto, auto, auto),
    align: (left, left, center, left),
    table.hline(stroke: 1pt),
    table.header([*Member*], [*Criterion*], [*Limit*], [*Load case (SIA 260, Table 3)*]),
    table.hline(stroke: 0.5pt),
    [Floors and beams], [Fittings with brittle behaviour], [$w <= l \/ 500$], [occasional (20)],
    [Floors and beams], [Fittings with ductile behaviour], [$w <= l \/ 350$], [frequent (21)],
    [Floors and beams], [Use, operation and comfort (deflection due to variable actions)], [$w <= l \/ 350$], [frequent (21)],
    [Floors and beams], [Appearance (after deduction of any camber)], [$w <= l \/ 300$], [quasi-permanent (22)],
    table.hline(stroke: 1pt),
  ),
  caption: [Permissible deflections],
)
// woodcore:/object deformation-table

// woodcore:object text p2
Deflection due to the actions and long-term effects after installation of all secondary members and technical equipment. If fittings react particularly sensitively to deformations of the structure, constructional measures against damage are to be provided in addition to, or instead of, dimensioning measures.
// woodcore:/object p2
// woodcore:/shared deformation-limits
