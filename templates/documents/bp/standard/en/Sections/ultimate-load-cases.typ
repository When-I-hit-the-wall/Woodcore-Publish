#import "/commands.typ": *

// woodcore:object heading title
== Load cases: structural safety
// woodcore:/object title

// woodcore:object text p1
Each load case is characterised by a leading action and the accompanying actions occurring at the same time (SIA 260, 4.2.6). The following values are the factors applied to the characteristic values; for an accompanying action the factor is $γ_Q$ · ψ₀ [state $γ_Q$ and ψ₀ or their product].
// woodcore:/object p1

// woodcore:object table uls-load-cases-table
#figure(
  table(
    columns: (auto, auto, auto, auto, auto, auto),
    align: (left, left, right, right, right, center),
    table.hline(stroke: 1pt),
    table.header([*Member*], [*Load case*], [*Self-weight and permanent loads*], [*Live load [category]*], [*Snow*], [*Wind*]),
    table.hline(stroke: 0.5pt),
    [[Roof]], [CC 1], [1.35], [–], [1.5], [$γ_Q · ψ_0$],
    [[Roof]], [CC 2], [0.8], [–], [–], [1.5],
    table.hline(stroke: 1pt),
  ),
  caption: [Load cases: structural safety],
)
// woodcore:/object uls-load-cases-table
