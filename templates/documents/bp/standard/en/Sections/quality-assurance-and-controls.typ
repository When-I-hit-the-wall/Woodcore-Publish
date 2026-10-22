#import "/commands.typ": *

// woodcore:object heading title
== Quality assurance and controls
// woodcore:/object title

// woodcore:object text p1
Ensuring adequate reliability requires quality assurance measures during design, execution, use and preservation (SIA 260, 2.3.6), with division of responsibilities, processes, controls and corrective mechanisms (2.5.2). The structural system is chosen so as to provide sufficient redundancy (insensitivity to local failure, 2.4.6). The essential instruments are [the designer's construction inspection plan and the contractor's test plan, in accordance with SIA Merkblatt 2007 “Qualität im Bauwesen”].
// woodcore:/object p1

// woodcore:object table controls-table
#figure(
  table(
    columns: (auto, auto, auto, auto),
    align: (left, left, left, left),
    table.hline(stroke: 1pt),
    table.header([*Phase*], [*Measure*], [*Responsible*], [*Check / evidence*]),
    table.hline(stroke: 0.5pt),
    [Design], [[Verification $E_d$ ≤ $R_d$ in accordance with the SIA standards; plausibility check of results]], [[Engineer]], [[Independent check]],
    [Execution], [[Contractor's quality assurance programme; testing and monitoring of the materials used]], [[Contractor / site management]], [[Construction inspection plan]],
    table.hline(stroke: 1pt),
  ),
  caption: [Measures and controls],
)
// woodcore:/object controls-table
