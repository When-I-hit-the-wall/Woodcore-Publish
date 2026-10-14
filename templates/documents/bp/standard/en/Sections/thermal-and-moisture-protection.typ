#import "/commands.typ": *

// woodcore:object heading title
== Thermal insulation and moisture protection
// woodcore:/object title

// woodcore:object text p1
The maximum thermal transmittances $U_"max"$ in accordance with #cite-norm(norm: "SIA 180") must be met. For the proof by individual component requirements, the values of the cantonal energy legislation [canton, ordinance] apply to new buildings. [Label sought (Minergie …) or none.]
// woodcore:/object p1

// woodcore:object doc-table u-values-table
#doc-table(
  columns: (
    (id: "element", title: [Element]),
    (id: "against", title: [Against]),
    (id: "U", title: [Thermal transmittance $U$], unit: "W/(m²K)", kind: "number"),
    (id: "basis", title: [Basis]),
  ),
  hidden: (),
  rows: (
    (element: [Roof], against: [Outside], U: [[…]], basis: [[cantonal ordinance]]),
    (element: [External wall], against: [Outside], U: [[…]], basis: [[cantonal ordinance]]),
  ),
  caption: [Limit values of thermal transmittance],
)
// woodcore:/object u-values-table
