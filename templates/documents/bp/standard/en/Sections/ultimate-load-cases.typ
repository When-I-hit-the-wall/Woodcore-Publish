#import "/commands.typ": *

// woodcore:object heading title
== Load cases: structural safety
// woodcore:/object title

// woodcore:object text p1
Each load case is characterised by a leading action and the accompanying actions occurring at the same time (SIA 260, 4.2.6). The following values are the factors applied to the characteristic values; for an accompanying action the factor is $γ_Q$ · ψ₀ [state $γ_Q$ and ψ₀ or their product].
// woodcore:/object p1

// woodcore:object doc-table uls-load-cases-table
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
    (element: [[Roof]], case: [CC 1], permanent: 1.35, live: [–], snow: 1.5, wind: [$γ_Q · ψ_0$]),
    (element: [[Roof]], case: [CC 2], permanent: 0.8, live: [–], snow: [–], wind: 1.5),
  ),
  caption: [Load cases: structural safety],
)
// woodcore:/object uls-load-cases-table
