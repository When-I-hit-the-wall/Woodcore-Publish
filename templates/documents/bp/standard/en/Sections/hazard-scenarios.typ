#import "/commands.typ": *

// woodcore:object heading title
== Hazard scenarios
// woodcore:/object title

// woodcore:object text p1
Possible hazard scenarios have been thought through and suitable measures specified to keep the hazards under control or limit them to an acceptable amount (SIA 260, 2.4.4). The hazard scenarios considered, with measures, follow-up and design assumptions, are:
// woodcore:/object p1

// woodcore:object doc-checklist hazard-influences
#doc-checklist(
  label: [Influences that may represent a hazard (SIA 260, 2.4.5)],
  options: (
    (id: "deviations-actions", label: [Deviation from the assumed values of the actions], checked: true),
    (id: "ground-actions", label: [Actions imposed by the ground], checked: false),
    (id: "natural-hazards", label: [Actions due to gravitational or meteorological natural hazards], checked: false),
    (id: "physical", label: [Physical actions, e.g. humidity or temperature], checked: true),
    (id: "chemical", label: [Chemical actions, e.g. due to de-icing salt or groundwater], checked: false),
    (id: "biological", label: [Biological actions, e.g. due to insects or fungi], checked: true),
    (id: "resonance", label: [Resonance effects], checked: false),
    (id: "resistance-deviations", label: [Deviations from the planned values of the ultimate resistances of the structure or the ground], checked: false),
    (id: "deterioration", label: [Impairment of the ultimate resistance through corrosion, increasing brittleness or fatigue], checked: false),
    (id: "accidental", label: [Impairment of the ultimate resistance due to fire, explosion, impact, rupture of pipes, or earthquakes], checked: true),
  ),
)
// woodcore:/object hazard-influences

// woodcore:object doc-table hazard-scenarios-table
#doc-table(
  columns: (
    (id: "scenario", title: [Hazard scenario]),
    (id: "measures", title: [Measures]),
    (id: "followup", title: [Follow-up]),
    (id: "assumptions", title: [Assumptions for analysis and design]),
  ),
  hidden: (),
  rows: (
    (scenario: [[Fire]], measures: [[Fire compartments, fire resistance, sufficient member dimensions, fire protection cladding]], followup: [[Fire protection concept; fire design]], assumptions: [[R 60]]),
    (scenario: [[Earthquake]], measures: [[Design; constructional measures in accordance with SIA 261]], followup: [[Static calculations]], assumptions: [[Zone, ground class, building class, q]]),
  ),
  caption: [Hazard scenarios and measures],
)
// woodcore:/object hazard-scenarios-table
