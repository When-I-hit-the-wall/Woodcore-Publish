#import "/commands.typ": *

// woodcore:object heading title
== Quality assurance and controls
// woodcore:/object title

// woodcore:object text p1
Ensuring adequate reliability requires quality assurance measures during design, execution, use and preservation (SIA 260, 2.3.6), with division of responsibilities, processes, controls and corrective mechanisms (2.5.2). The structural system is chosen so as to provide sufficient redundancy (insensitivity to local failure, 2.4.6). The essential instruments are [the designer's construction inspection plan and the contractor's test plan, in accordance with SIA Merkblatt 2007 “Qualität im Bauwesen”].
// woodcore:/object p1

// woodcore:object doc-table controls-table
#doc-table(
  columns: (
    (id: "phase", title: [Phase]),
    (id: "measure", title: [Measure]),
    (id: "responsible", title: [Responsible]),
    (id: "verification", title: [Check / evidence]),
  ),
  hidden: (),
  rows: (
    (phase: [Design], measure: [[Verification $E_d$ ≤ $R_d$ in accordance with the SIA standards; plausibility check of results]], responsible: [[Engineer]], verification: [[Independent check]]),
    (phase: [Execution], measure: [[Contractor's quality assurance programme; testing and monitoring of the materials used]], responsible: [[Contractor / site management]], verification: [[Construction inspection plan]]),
  ),
  caption: [Measures and controls],
)
// woodcore:/object controls-table
