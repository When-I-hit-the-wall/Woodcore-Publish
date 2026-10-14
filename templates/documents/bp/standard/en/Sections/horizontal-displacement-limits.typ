#import "/commands.typ": *

// woodcore:object heading title
== Horizontal displacements
// woodcore:/object title

// woodcore:object text p1
Horizontal displacements due to the variable actions are limited to the standard values of SIA 260, Appendix A, Table 4; h denotes the storey height and H the building height. For the earthquake design situation, the horizontal displacements per storey are limited to 1/500 or 1/200 of the storey height where fittings have brittle or ductile behaviour respectively (4.4.4.5).
// woodcore:/object p1

// woodcore:object doc-table horizontal-limits-table
#doc-table(
  columns: (
    (id: "criterion", title: [Criterion]),
    (id: "limit", title: [Limit], kind: "math"),
    (id: "load_case", title: [Load case (SIA 260, Table 4)]),
  ),
  hidden: (),
  rows: (
    (criterion: [Fittings with brittle behaviour], limit: [$u <= h \/ 500$], load_case: [occasional (20)]),
    (criterion: [Fittings with ductile behaviour], limit: [$u <= h \/ 200$], load_case: [frequent (21)]),
    (criterion: [Use and operation], limit: [$u <= H \/ 300$], load_case: [frequent (21)]),
    (criterion: [Appearance], limit: [$u <= h \/ 250$], load_case: [quasi-permanent (22)]),
  ),
  caption: [Permissible horizontal displacements],
)
// woodcore:/object horizontal-limits-table
