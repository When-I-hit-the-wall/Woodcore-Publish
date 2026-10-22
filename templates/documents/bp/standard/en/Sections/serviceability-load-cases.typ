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

// woodcore:object table sls-load-cases-table
#figure(
  table(
    columns: (auto, auto, auto, auto, auto, auto),
    align: (left, left, right, right, right, center),
    table.hline(stroke: 1pt),
    table.header([*Member*], [*Load case*], [*Self-weight and permanent loads*], [*Live load [category]*], [*Snow*], [*Wind*]),
    table.hline(stroke: 0.5pt),
    [[Roof]], [CC 1], [1.0], [–], [1.0], [$ψ_0$],
    [[Typical floor]], [CC 2], [1.0], [1.0], [–], [$ψ_0$],
    table.hline(stroke: 1pt),
  ),
  caption: [Load cases: serviceability],
)
// woodcore:/object sls-load-cases-table
