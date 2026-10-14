#import "/commands.typ": *

// woodcore:object heading title
== Deformation limits (deflections)
// woodcore:/object title
// woodcore:shared deformation-limits

// woodcore:object text p1
Deflections are limited to the standard values of SIA 260, Appendix A, Table 3; they are determined in accordance with SIA 262 to 266. Different limit values may be agreed in line with the service requirements, in particular for secondary members; they are then specified in the basis of design. [The owner makes no more stringent requirements than the standard: yes / no.]
// woodcore:/object p1

// woodcore:object doc-table deformation-table
#doc-table(
  columns: (
    (id: "element", title: [Member]),
    (id: "criterion", title: [Criterion]),
    (id: "limit", title: [Limit], kind: "math"),
    (id: "load_case", title: [Load case (SIA 260, Table 3)]),
  ),
  hidden: (),
  rows: (
    (element: [Floors and beams], criterion: [Fittings with brittle behaviour], limit: [$w <= l \/ 500$], load_case: [occasional (20)]),
    (element: [Floors and beams], criterion: [Fittings with ductile behaviour], limit: [$w <= l \/ 350$], load_case: [frequent (21)]),
    (element: [Floors and beams], criterion: [Use, operation and comfort (deflection due to variable actions)], limit: [$w <= l \/ 350$], load_case: [frequent (21)]),
    (element: [Floors and beams], criterion: [Appearance (after deduction of any camber)], limit: [$w <= l \/ 300$], load_case: [quasi-permanent (22)]),
  ),
  caption: [Permissible deflections],
)
// woodcore:/object deformation-table

// woodcore:object text p2
Deflection due to the actions and long-term effects after installation of all secondary members and technical equipment. If fittings react particularly sensitively to deformations of the structure, constructional measures against damage are to be provided in addition to, or instead of, dimensioning measures.
// woodcore:/object p2
// woodcore:/shared deformation-limits
