#import "/commands.typ": *

// woodcore:object heading title
=== Self-weight and unit weights
// woodcore:/object title

// woodcore:object text p1
Permanent actions act continuously. They comprise the self-weight of the structure and the permanent loads of the building elements. The self-weight is determined from the dimensions on the drawings and the mean unit weights of SIA 261, Annex A; it is treated as a whole with upper or lower design values, depending on whether the overall effect is unfavourable or favourable (SIA 261, 2.1.2).
// woodcore:/object p1

// woodcore:object table permanent-actions-table
#figure(
  table(
    columns: (auto, auto, auto, auto),
    align: (left, left, left, left),
    table.hline(stroke: 1pt),
    table.header([*Action / hazard*], [*Measures*], [*Follow-up*], [*Assumptions for analysis and design*]),
    table.hline(stroke: 0.5pt),
    [Self-weight], [Design; construction inspections], [Static calculations; inspection plan], [Unit weights in accordance with SIA 261, Annex A (table below)],
    [Superimposed dead loads], [Design; construction inspections; monitoring in service (alterations)], [Static calculations; inspection plan; monitoring plan], [According to the member build-ups (section “Superimposed dead loads”)],
    table.hline(stroke: 1pt),
  ),
  caption: [Permanent actions: measures and assumptions],
)
// woodcore:/object permanent-actions-table

// woodcore:object table unit-weights-table
#figure(
  table(
    columns: (auto, auto),
    align: (left, right),
    table.hline(stroke: 1pt),
    table.header([*Material*], [*Unit weight $gamma$*]),
    table.hline(stroke: 0.5pt),
    [Structural steel], [78.5],
    [Reinforced concrete], [25],
    [Softwood, in general], [5],
    table.hline(stroke: 1pt),
  ),
  caption: [Unit weights of materials],
)
// woodcore:/object unit-weights-table

// woodcore:object text unit-weights-table-notes
Mean values from SIA 261, Annex A, Table 28; the complete table is in the standard.
// woodcore:/object unit-weights-table-notes
