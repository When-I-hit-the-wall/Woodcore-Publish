#import "/commands.typ": *

// woodcore:object heading title
== Cas de charge : sécurité structurale
// woodcore:/object title

// woodcore:object text p1
Chaque cas de charge est caractérisé par une action prépondérante et les actions concomitantes qui agissent en même temps (SIA 260, ch. 4.2.6). Les valeurs ci-dessous sont les facteurs appliqués aux valeurs caractéristiques ; pour une action concomitante, le facteur est $γ_Q$ · ψ₀ [indiquer $γ_Q$ et ψ₀ ou leur produit].
// woodcore:/object p1

// woodcore:object table uls-load-cases-table
#figure(
  table(
    columns: (auto, auto, auto, auto, auto, auto),
    align: (left, left, right, right, right, center),
    table.hline(stroke: 1pt),
    table.header([*Élément*], [*Cas*], [*Poids propre et charges permanentes*], [*Charge utile [catégorie]*], [*Neige*], [*Vent*]),
    table.hline(stroke: 0.5pt),
    [[Toiture]], [CC 1], [1.35], [–], [1.5], [$γ_Q · ψ_0$],
    [[Toiture]], [CC 2], [0.8], [–], [–], [1.5],
    table.hline(stroke: 1pt),
  ),
  caption: [Cas de charge : sécurité structurale],
)
// woodcore:/object uls-load-cases-table
