#import "/commands.typ": *

// woodcore:object heading title
== Load cases: serviceability
// woodcore:/object title

// woodcore:object text p1
For serviceability, $E_d$ is generally determined with $γ_F$ = $γ_m$ = 1.0 (SIA 260, 4.4.4.3). Three types of load case are distinguished (4.4.4.4):
// woodcore:/object p1

// woodcore:object text p2
- occasional load cases: leading variable action at its characteristic value, accompanying actions with ψ₀;
- frequent load cases: leading variable action with ψ₁, accompanying actions with ψ₂;
- quasi-permanent load cases: all variable actions with ψ₂.
// woodcore:/object p2

// woodcore:object doc-table sls-load-cases-table
#doc-table(
  columns: (
    (id: "element", title: [Member]),
    (id: "case", title: [Load case]),
    (id: "permanent", title: [Self-weight and permanent loads], kind: "number"),
    (id: "live", title: [Live load [category]], kind: "number"),
    (id: "snow", title: [Snow], kind: "number"),
    (id: "wind", title: [Wind], kind: "math"),
  ),
  hidden: (),
  rows: (
    (element: [[Roof]], case: [CC 1], permanent: 1.0, live: [–], snow: 1.0, wind: [$ψ_0$]),
    (element: [[Typical floor]], case: [CC 2], permanent: 1.0, live: 1.0, snow: [–], wind: [$ψ_0$]),
  ),
  caption: [Load cases: serviceability],
)
// woodcore:/object sls-load-cases-table
