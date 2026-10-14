#import "/commands.typ": *

// woodcore:object heading title
=== Self-weight and unit weights
// woodcore:/object title

// woodcore:object text p1
Permanent actions act continuously. They comprise the self-weight of the structure and the permanent loads of the building elements. The self-weight is determined from the dimensions on the drawings and the mean unit weights of SIA 261, Annex A; it is treated as a whole with upper or lower design values, depending on whether the overall effect is unfavourable or favourable (SIA 261, 2.1.2).
// woodcore:/object p1

// woodcore:object doc-table permanent-actions-table
#doc-table(
  columns: (
    (id: "action", title: [Action / hazard]),
    (id: "measures", title: [Measures]),
    (id: "followup", title: [Follow-up]),
    (id: "assumptions", title: [Assumptions for analysis and design]),
  ),
  hidden: (),
  rows: (
    (action: [Self-weight], measures: [Design; construction inspections], followup: [Static calculations; inspection plan], assumptions: [Unit weights in accordance with SIA 261, Annex A (table below)]),
    (action: [Superimposed dead loads], measures: [Design; construction inspections; monitoring in service (alterations)], followup: [Static calculations; inspection plan; monitoring plan], assumptions: [According to the member build-ups (section “Superimposed dead loads”)]),
  ),
  caption: [Permanent actions: measures and assumptions],
)
// woodcore:/object permanent-actions-table

// woodcore:object doc-table unit-weights-table
#doc-table(
  columns: (
    (id: "material", title: [Material]),
    (id: "gamma", title: [Unit weight $gamma$], unit: "kN/m³", kind: "number"),
  ),
  hidden: (),
  rows: (
    (material: [Structural steel], gamma: 78.5),
    (material: [Reinforced concrete], gamma: 25),
    (material: [Softwood, in general], gamma: 5),
  ),
  caption: [Unit weights of materials],
  notes: (
    [Mean values from SIA 261, Annex A, Table 28; the complete table is in the standard.],
  ),
)
// woodcore:/object unit-weights-table
