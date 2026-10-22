#import "/commands.typ": *

// woodcore:object heading title
== Hazard scenarios
// woodcore:/object title

// woodcore:object text p1
Possible hazard scenarios have been thought through and suitable measures specified to keep the hazards under control or limit them to an acceptable amount (SIA 260, 2.4.4). The hazard scenarios considered, with measures, follow-up and design assumptions, are:
// woodcore:/object p1

// woodcore:object text hazard-influences
*Influences that may represent a hazard (SIA 260, 2.4.5)*:
- *Deviation from the assumed values of the actions*
- *Physical actions, e.g. humidity or temperature*
- *Biological actions, e.g. due to insects or fungi*
- *Impairment of the ultimate resistance due to fire, explosion, impact, rupture of pipes, or earthquakes*
// woodcore:/object hazard-influences

// woodcore:object table hazard-scenarios-table
#figure(
  table(
    columns: (auto, auto, auto, auto),
    align: (left, left, left, left),
    table.hline(stroke: 1pt),
    table.header([*Hazard scenario*], [*Measures*], [*Follow-up*], [*Assumptions for analysis and design*]),
    table.hline(stroke: 0.5pt),
    [[Fire]], [[Fire compartments, fire resistance, sufficient member dimensions, fire protection cladding]], [[Fire protection concept; fire design]], [[R 60]],
    [[Earthquake]], [[Design; constructional measures in accordance with SIA 261]], [[Static calculations]], [[Zone, ground class, building class, q]],
    table.hline(stroke: 1pt),
  ),
  caption: [Hazard scenarios and measures],
)
// woodcore:/object hazard-scenarios-table
