#import "/commands.typ": *

// woodcore:object heading title
== Certification and sustainability standard
// woodcore:/object title
// woodcore:shared sustainability-certification

// woodcore:object doc-checklist certification-choice
#doc-checklist(
  label: [Certification or standard sought],
  options: (
    (id: "snbs", label: [SNBS Buildings (Swiss Sustainable Building Standard)], checked: false),
    (id: "minergie", label: [Minergie], checked: false),
    (id: "minergie-p", label: [Minergie-P], checked: false),
    (id: "minergie-a", label: [Minergie-A], checked: false),
    (id: "minergie-eco", label: [Minergie-ECO (supplement)], checked: false),
    (id: "sia-2040", label: [SIA energy efficiency path (SIA 2040) and embodied energy (SIA 2032)], checked: false),
    (id: "none", label: [No certification sought], checked: true),
  ),
)
// woodcore:/object certification-choice

// woodcore:object text p1
[State what the target implies for the structure, e.g. limit values for greenhouse-gas emissions, embodied energy and stored carbon, and the use, where possible, of timber members with low CO₂ emissions and high carbon storage.]
// woodcore:/object p1

// woodcore:object text p2
[State who verifies compliance with the limit values: this check is generally not part of the structural engineer's tasks.]
// woodcore:/object p2
// woodcore:/shared sustainability-certification
