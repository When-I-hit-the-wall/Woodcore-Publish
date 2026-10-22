#import "/commands.typ": *

// woodcore:object heading title
== Aménagements, façades et installations
// woodcore:/object title

// woodcore:object text p1
Les cloisons non porteuses réalisées avec le gros œuvre (p. ex. maçonnerie non porteuse) sont séparées du plancher par des couches intermédiaires souples, de sorte que les déformations du plancher définies plus haut (en plus de la tolérance de construction) restent sans conséquence pour elles. Celles réalisées après le gros œuvre et le désétaiement présentent une couche intermédiaire souple d'au moins [20] mm. Les cloisons non porteuses en maçonnerie qui ne se stabilisent pas d'elles-mêmes sont à assurer contre le basculement en cas de séisme. [Poids et déformations admissibles de la façade : …]
// woodcore:/object p1

// woodcore:object table deformation-margins
#figure(
  table(
    columns: (auto, auto),
    align: (left, right),
    table.hline(stroke: 1pt),
    table.header([*Élément*], [*Déformation du plancher à prévoir*]),
    table.hline(stroke: 0.5pt),
    [Cloisons non porteuses], [[…]],
    [Façade], [[…]],
    table.hline(stroke: 1pt),
  ),
  caption: [Marges de déformation à prévoir après la pose],
)
// woodcore:/object deformation-margins

// woodcore:object text deformation-margins-notes
Marge de déformation en plus de la tolérance de construction ; les bords de plancher sont relevés avant la production et la pose de la façade.
// woodcore:/object deformation-margins-notes
