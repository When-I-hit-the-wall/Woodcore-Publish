#import "/commands.typ": *

// woodcore:object heading title
== Thermal insulation and moisture protection
// woodcore:/object title

// woodcore:object text p1
The maximum thermal transmittances $U_"max"$ in accordance with #cite-norm(norm: "SIA 180") must be met. For the proof by individual component requirements, the values of the cantonal energy legislation [canton, ordinance] apply to new buildings. [Label sought (Minergie …) or none.]
// woodcore:/object p1

// woodcore:object table u-values-table
#figure(
  table(
    columns: (auto, auto, auto, auto),
    align: (left, left, right, left),
    table.hline(stroke: 1pt),
    table.header([*Element*], [*Against*], [*Thermal transmittance $U$*], [*Basis*]),
    table.hline(stroke: 0.5pt),
    [Roof], [Outside], [[…]], [[cantonal ordinance]],
    [External wall], [Outside], [[…]], [[cantonal ordinance]],
    table.hline(stroke: 1pt),
  ),
  caption: [Limit values of thermal transmittance],
)
// woodcore:/object u-values-table
