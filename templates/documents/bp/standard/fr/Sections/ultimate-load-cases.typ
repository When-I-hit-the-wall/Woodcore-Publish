#import "/commands.typ": *

// woodcore:object heading title
== Cas de charge : sécurité structurale
// woodcore:/object title

// woodcore:object text p1
Chaque cas de charge est caractérisé par une action prépondérante et les actions concomitantes qui agissent en même temps (SIA 260, ch. 4.2.6). Les valeurs ci-dessous sont les facteurs appliqués aux valeurs caractéristiques ; pour une action concomitante, le facteur est $γ_Q$ · ψ₀ [indiquer $γ_Q$ et ψ₀ ou leur produit].
// woodcore:/object p1

// woodcore:object doc-table uls-load-cases-table
#doc-table(
  columns: (
    (id: "element", title: [Élément]),
    (id: "case", title: [Cas]),
    (id: "permanent", title: [Poids propre et charges permanentes], kind: "number"),
    (id: "live", title: [Charge utile [catégorie]], kind: "number"),
    (id: "snow", title: [Neige], kind: "number"),
    (id: "wind", title: [Vent], kind: "math"),
  ),
  hidden: (),
  rows: (
    (element: [[Toiture]], case: [CC 1], permanent: 1.35, live: [–], snow: 1.5, wind: [$γ_Q · ψ_0$]),
    (element: [[Toiture]], case: [CC 2], permanent: 0.8, live: [–], snow: [–], wind: 1.5),
  ),
  caption: [Cas de charge : sécurité structurale],
)
// woodcore:/object uls-load-cases-table
