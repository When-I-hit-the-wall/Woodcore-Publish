#import "/commands.typ": *

// woodcore:object heading title
== Aménagements, façades et installations
// woodcore:/object title

// woodcore:object text p1
Les cloisons non porteuses réalisées avec le gros œuvre (p. ex. maçonnerie non porteuse) sont séparées du plancher par des couches intermédiaires souples, de sorte que les déformations du plancher définies plus haut (en plus de la tolérance de construction) restent sans conséquence pour elles. Celles réalisées après le gros œuvre et le désétaiement présentent une couche intermédiaire souple d'au moins [20] mm. Les cloisons non porteuses en maçonnerie qui ne se stabilisent pas d'elles-mêmes sont à assurer contre le basculement en cas de séisme. [Poids et déformations admissibles de la façade : …]
// woodcore:/object p1

// woodcore:object doc-table deformation-margins
#doc-table(
  columns: (
    (id: "element", title: [Élément]),
    (id: "margin", title: [Déformation du plancher à prévoir], unit: "mm", kind: "number"),
  ),
  hidden: (),
  rows: (
    (element: [Cloisons non porteuses], margin: [[…]]),
    (element: [Façade], margin: [[…]]),
  ),
  caption: [Marges de déformation à prévoir après la pose],
  notes: (
    [Marge de déformation en plus de la tolérance de construction ; les bords de plancher sont relevés avant la production et la pose de la façade.],
  ),
)
// woodcore:/object deformation-margins
