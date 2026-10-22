#import "/commands.typ": *

// woodcore:object heading title
== Requirements for building elements
// woodcore:/object title

// woodcore:object text separating-elements-plan
#figure(rect(width: 100%, height: 5cm, stroke: 0.5pt + luma(60%))[[Plan or section with the numbering of the separating elements]], caption: [Identification of separating elements [storey]])
// woodcore:/object separating-elements-plan

// woodcore:object table airborne-exterior-table
#figure(
  table(
    columns: (auto, auto, auto, auto),
    align: (left, left, left, left),
    table.hline(stroke: 1pt),
    table.header([*Element*], [*Basis*], [*Requirement day / night*], [*Execution / values*]),
    table.hline(stroke: 0.5pt),
    [[Bedroom facade]], [SIA 181, tab. 2], [[…] / […]], [[…]],
    table.hline(stroke: 1pt),
  ),
  caption: [Airborne sound from outside],
)
// woodcore:/object airborne-exterior-table

// woodcore:object table airborne-interior-table
#figure(
  table(
    columns: (auto, auto, auto, auto),
    align: (left, left, left, left),
    table.hline(stroke: 1pt),
    table.header([*Zone / element*], [*Basis*], [*Requirement*], [*Execution / values*]),
    table.hline(stroke: 0.5pt),
    [[Bedroom / bedroom]], [SIA 181, tab. 3], [[…]], [[…]],
    table.hline(stroke: 1pt),
  ),
  caption: [Airborne sound within the building],
)
// woodcore:/object airborne-interior-table

// woodcore:object table impact-sound-table
#figure(
  table(
    columns: (auto, auto, auto, auto),
    align: (left, left, left, left),
    table.hline(stroke: 1pt),
    table.header([*Zone / element*], [*Basis*], [*Requirement*], [*Execution / values*]),
    table.hline(stroke: 0.5pt),
    [[Terrace / bedroom]], [SIA 181, tab. 5], [[…]], [[…]],
    table.hline(stroke: 1pt),
  ),
  caption: [Impact sound],
)
// woodcore:/object impact-sound-table

// woodcore:object table installation-noise-table
#figure(
  table(
    columns: (auto, auto, auto, auto, auto),
    align: (left, left, left, left, left),
    table.hline(stroke: 1pt),
    table.header([*Type of noise*], [*Zone / element*], [*Basis*], [*Requirement*], [*Execution / values*]),
    table.hline(stroke: 0.5pt),
    [Isolated noises], [[Kitchen / restaurant]], [SIA 181, tab. 6], [[…]], [[…]],
    table.hline(stroke: 1pt),
  ),
  caption: [Noise from technical installations],
)
// woodcore:/object installation-noise-table
